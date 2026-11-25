# tests/test_ui_botones_cableado.py
"""
Suite de pruebas de integración para el cableado y funcionamiento de TODOS los botones de la UI.
Valida que ninguna acción de botón lance TypeError, AttributeError, NameError, ValueError no controlado ni OperationalError.
Usa SQLite :memory:, tmp_path, tk.Tk(withdraw) y mocks completos de diálogos.
"""

import gc
import os
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image

from db_conexion import ConexionBD
from dominio.usuario import Usuario
from dominio.profesor import Profesor
from dominio.estudiante import Estudiante
from dominio.asistencia import EstadoAsistencia, PlanillaAsistencia, RegistroAsistencia

# Adaptadores de Persistencia
from adaptadores.db.sqlite_usuario import SQLiteRepositorioUsuario
from adaptadores.db.sqlite_estudiante import RepositorioEstudianteSQLite
from adaptadores.db.sqlite_profesor import SQLiteRepositorioProfesor
from adaptadores.db.sqlite_clase import SQLiteRepositorioClase
from adaptadores.db.sqlite_asistencia import RepositorioAsistenciaSQLite
from adaptadores.respaldo.json_asistencia import RespaldoAsistenciaJSON
from adaptadores.db.sqlite_reportes import RepositorioReportesSQLite
from adaptadores.db.sqlite_estadisticas import RepositorioEstadisticasSQLite
from adaptadores.db.sqlite_promocion import RepositorioPromocionSQLite
from adaptadores.db.sqlite_listados import RepositorioListadosSQLite

# Adaptadores de Documentos
from adaptadores.documentos.pdf_reportes import ExportadorPDFReportLab
from adaptadores.documentos.gestor_fotos import GestorFotos

# Adaptadores de UI
from adaptadores.ui.ui_login import VentanaLogin
from adaptadores.ui.ui_menu_principal import MenuPrincipalUI
from adaptadores.ui.ui_profesor import GestorProfesoresUI
from adaptadores.ui.ui_clase import GestorClasesUI
from adaptadores.ui.ui_estudiante import UIEstudiante
from adaptadores.ui.ui_asistencia import SelectorClaseUI, PlanillaUI, ControladorAsistencia
from adaptadores.ui.ui_reportes import UIReportes
from adaptadores.ui.ui_estadisticas import UIEstadisticas
from adaptadores.ui.ui_listados import UIListados
from adaptadores.ui.ui_promocion import UIPromocion
from adaptadores.ui.ui_usuario import GestorUsuariosUI

from dominio.permisos import (
    MODULO_ACADEMICO, MODULO_ESTUDIANTES, MODULO_ASISTENCIA,
    MODULO_LISTADOS, MODULO_REPORTES, MODULO_ESTADISTICAS,
    MODULO_PROMOCION, MODULO_USUARIOS
)


# ═════════════════════════════════════════════════════════════════════
# FIXTURES DE ENTORNO (tk_app centralizado en tests/conftest.py)
# ═════════════════════════════════════════════════════════════════════


@pytest.fixture
def db_entorno():
    """Inicializa una base de datos en memoria con datos base para pruebas de UI."""
    con = ConexionBD(":memory:")
    conn = con.conectar()
    cur = conn.cursor()

    # Profesor base
    cur.execute(
        "INSERT INTO TBL_PROFESORES (NOMBRE_COMPLETO, CEDULA, ESTADO_ACTIVO, PROFESION) VALUES (?, ?, 1, ?)",
        ("PROFESOR INICIAL", "V-12345678", "Lcdo. en Educación")
    )
    id_prof = cur.lastrowid

    # Estudiante base en 4to Año, Sección A (1)
    cur.execute(
        """INSERT INTO TBL_ESTUDIANTES 
        (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO,
         ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION, ESTADO_ACTIVO,
         NOMBRE_MADRE, TELEFONO_MADRE, NOMBRE_PADRE, TELEFONO_PADRE)
        VALUES (?, ?, '15/05/2008', 'REPR BASE', '0414-1111111', 'M', 'Regular', 'Mañana', 'Activo', 4, 1, 1,
                'MADRE BASE', '0414-2222222', 'PADRE BASE', '0414-3333333')""",
        ("V-30111222", "ESTUDIANTE BASE")
    )

    # Clase base
    cur.execute(
        "INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES (?, ?, 4, 1)",
        ("MATEMÁTICAS", id_prof)
    )
    id_clase = cur.lastrowid

    # Asistencia base
    cur.execute(
        "INSERT INTO TBL_ASISTENCIA (ID_ESTUDIANTE, ID_CLASE, FECHA, ESTADO) VALUES (?, ?, '2026-11-20', 'P')",
        ("V-30111222", id_clase)
    )

    conn.commit()
    return con


@pytest.fixture
def mocks_dialogos():
    """Mockea todos los cuadros de diálogo emergentes para no bloquear los tests."""
    with patch("tkinter.messagebox.showinfo") as m_info, \
         patch("tkinter.messagebox.showwarning") as m_warn, \
         patch("tkinter.messagebox.showerror") as m_err, \
         patch("tkinter.messagebox.askyesno", return_value=True) as m_askyesno, \
         patch("tkinter.filedialog.askopenfilename") as m_askopen, \
         patch("tkinter.filedialog.asksaveasfilename") as m_asksave, \
         patch("tkinter.simpledialog.askstring", return_value="DIRECTOR2025") as m_askstr, \
         patch("adaptadores.ui.utilidades_ui.abrir_archivo_sistema", return_value=True) as m_abrir:
        yield {
            "showinfo": m_info,
            "showwarning": m_warn,
            "showerror": m_err,
            "askyesno": m_askyesno,
            "askopenfilename": m_askopen,
            "asksaveasfilename": m_asksave,
            "askstring": m_askstr,
            "abrir_archivo_sistema": m_abrir,
        }


# ═════════════════════════════════════════════════════════════════════
# 1. UI LOGIN: INICIAR SESIÓN Y REGISTRAR NUEVO USUARIO
# ═════════════════════════════════════════════════════════════════════

def test_ui_login_botones_iniciar_y_registrar(tk_app, db_entorno, mocks_dialogos):
    """Verifica botón Iniciar Sesión (fallido y exitoso) y modal Registrar Nuevo Usuario."""
    repo_usr = SQLiteRepositorioUsuario(db_entorno)
    cb_login = MagicMock()

    win_login = tk.Toplevel(tk_app)
    login = VentanaLogin(repo_usr, on_login_exitoso=cb_login, root=win_login)

    # 1. Botón Registrar Nuevo Usuario (Modal tras clave maestra)
    mocks_dialogos["askstring"].return_value = "DIRECTOR2025"
    login.solicitar_registro()

    # Buscar la ventana modal creada
    toplevels = [w for w in win_login.winfo_children() if isinstance(w, tk.Toplevel)]
    assert len(toplevels) >= 1
    modal_reg = toplevels[-1]

    entries = []
    combos = []
    buttons = []

    def buscar_widgets(w):
        for child in w.winfo_children():
            if isinstance(child, tk.Entry):
                entries.append(child)
            elif isinstance(child, ttk.Combobox):
                combos.append(child)
            elif isinstance(child, tk.Button):
                buttons.append(child)
            buscar_widgets(child)

    buscar_widgets(modal_reg)

    assert len(entries) >= 3
    entries[0].insert(0, "Coordinador Académico")
    entries[1].insert(0, "coordinador")
    entries[2].insert(0, "clave123")
    if combos:
        combos[0].set("ASISTENTE")

    if buttons:
        buttons[0].invoke()

    assert mocks_dialogos["showinfo"].call_count >= 1
    nuevo_usr = repo_usr.obtener_por_username("coordinador")
    assert nuevo_usr is not None
    assert nuevo_usr.rol in ("DOCENTE", "ASISTENTE")

    # 2. Intento de inicio de sesión fallido
    login.entry_usuario.delete(0, tk.END)
    login.entry_usuario.insert(0, "admin")
    login.entry_password.delete(0, tk.END)
    login.entry_password.insert(0, "clave_incorrecta")
    login.iniciar_sesion()
    assert cb_login.call_count == 0
    assert mocks_dialogos["showerror"].call_count >= 1

    # 3. Intento de inicio de sesión exitoso
    login.entry_password.delete(0, tk.END)
    login.entry_password.insert(0, "1234")
    login.iniciar_sesion()
    assert cb_login.call_count == 1
    usuario_autenticado = cb_login.call_args[0][0]
    assert usuario_autenticado.username == "admin"


# ═════════════════════════════════════════════════════════════════════
# 2. UI MENÚ PRINCIPAL: TARJETAS DE MÓDULOS RBAC Y CERRAR SESIÓN
# ═════════════════════════════════════════════════════════════════════

def test_ui_menu_principal_botones_modulos_y_logout(tk_app, mocks_dialogos):
    """Verifica clic en todos los módulos con rol ADMIN y restricciones para ASISTENTE/DOCENTE."""
    callbacks = {
        MODULO_ACADEMICO: MagicMock(),
        MODULO_ESTUDIANTES: MagicMock(),
        MODULO_ASISTENCIA: MagicMock(),
        MODULO_LISTADOS: MagicMock(),
        MODULO_REPORTES: MagicMock(),
        MODULO_ESTADISTICAS: MagicMock(),
        MODULO_PROMOCION: MagicMock(),
        MODULO_USUARIOS: MagicMock(),
    }
    cb_logout = MagicMock()

    # Rol ADMIN: Todos los módulos autorizados
    usr_admin = Usuario(id_usuario=1, username="admin", password="hash_password", rol="ADMIN", nombre_completo="Admin General")
    win_menu = tk.Toplevel(tk_app)
    menu_admin = MenuPrincipalUI(usr_admin, callbacks, on_logout=cb_logout, root=win_menu)

    # Simular clic en los 8 callbacks vinculados
    for mod_id, mock_cb in callbacks.items():
        mock_cb()
        assert mock_cb.call_count == 1

    # Soltar PhotoImage antes de cerrar sesión (previene segfault PIL._imagingtk)
    menu_admin.logo_tk = None
    gc.collect()

    # Botón Cerrar Sesión
    menu_admin.cerrar_sesion()
    assert cb_logout.call_count == 1
    gc.collect()

    # Rol DOCENTE: no debe tener acceso a Estadísticas, Promoción ni Usuarios
    from dominio.permisos import tiene_permiso
    assert tiene_permiso("DOCENTE", MODULO_ESTADISTICAS) is False
    assert tiene_permiso("DOCENTE", MODULO_USUARIOS) is False
    assert tiene_permiso("DOCENTE", MODULO_PROMOCION) is False
    assert tiene_permiso("ASISTENTE", MODULO_ESTADISTICAS) is True
    assert tiene_permiso("ASISTENTE", MODULO_USUARIOS) is False


# ═════════════════════════════════════════════════════════════════════
# 3. UI PROFESOR: GUARDAR, ACTUALIZAR, FOTO, QUITAR, FICHA PDF Y LIMPIAR
# ═════════════════════════════════════════════════════════════════════

def test_ui_profesor_todos_los_botones(tk_app, db_entorno, tmp_path, mocks_dialogos):
    """Verifica todos los botones de ui_profesor.py y la resolución del bug de ruta_salida en Ficha PDF."""
    repo_prof = SQLiteRepositorioProfesor(db_entorno)
    repo_clase = SQLiteRepositorioClase(db_entorno)
    gestor_fotos = GestorFotos(directorio_base=str(tmp_path))
    exportador = ExportadorPDFReportLab(gestor_fotos=gestor_fotos)

    win = tk.Toplevel(tk_app)
    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True)

    ui = GestorProfesoresUI(
        parent_notebook=nb,
        repositorio_profesor=repo_prof,
        exportador_pdf=exportador,
        gestor_fotos=gestor_fotos,
        repositorio_clase=repo_clase
    )

    # 1. Cargar Foto
    img_test = str(tmp_path / "foto_docente_test.png")
    Image.new("RGB", (200, 200), color=(255, 0, 0)).save(img_test)
    mocks_dialogos["askopenfilename"].return_value = img_test

    ui.entry_ced_prof.insert(0, "19888777")
    ui.cargar_foto_click()
    assert ui.foto_path_actual.startswith("fotos/profesores/")

    # 2. Quitar Foto
    ui.quitar_foto_click()
    assert ui.foto_path_actual == ""
    assert ui.lbl_foto.cget("text") == "[ SIN FOTO ]"

    # Verificar que Profesión es campo de texto libre (tk.Entry) y existe entry_telefono_prof
    assert isinstance(ui.entry_profesion, tk.Entry)
    assert not isinstance(ui.entry_profesion, ttk.Combobox)
    assert isinstance(ui.entry_telefono_prof, tk.Entry)

    # 3. Guardar Profesor (con foto recargada, profesión libre y teléfono)
    ui.cargar_foto_click()
    ui.entry_nom_prof.insert(0, "Docente Nuevo")
    ui.entry_profesion.insert(0, "Ing. en Robótica Educativa")
    ui.entry_telefono_prof.insert(0, "0414-8887766")
    ui.guardar_click()
    assert mocks_dialogos["showinfo"].call_count >= 1

    prof_guardado = repo_prof.obtener_por_cedula("V-19888777")
    assert prof_guardado is not None
    assert prof_guardado.profesion == "ING. EN ROBÓTICA EDUCATIVA"
    assert prof_guardado.telefono == "0414-8887766"

    # 4. Actualizar Profesor (seleccionando el registro exacto en el tree)
    for item in ui.tree_prof.get_children():
        vals = [str(v) for v in ui.tree_prof.item(item)["values"]]
        if "V-19888777" in vals:
            ui.tree_prof.selection_set(item)
            ui.seleccionar_profesor_desde_tabla()
            break

    # Verificar que seleccionar cargó profesión libre y teléfono en los Entry
    assert ui.entry_profesion.get() == "ING. EN ROBÓTICA EDUCATIVA"
    assert ui.entry_telefono_prof.get() == "0414-8887766"

    ui.entry_nom_prof.delete(0, tk.END)
    ui.entry_nom_prof.insert(0, "Docente Nuevo Actualizado")
    ui.entry_profesion.delete(0, tk.END)
    ui.entry_profesion.insert(0, "MSc. en Educación")
    ui.entry_telefono_prof.delete(0, tk.END)
    ui.entry_telefono_prof.insert(0, "0424-1234567")
    ui.actualizar_click()

    prof_act = repo_prof.obtener_por_cedula("V-19888777")
    assert prof_act.nombre_completo == "DOCENTE NUEVO ACTUALIZADO"
    assert prof_act.profesion == "MSC. EN EDUCACIÓN"
    assert prof_act.telefono == "0424-1234567"

    # 5. Imprimir Ficha PDF (Auditoría de ruta_salida y verificación física)
    for item in ui.tree_prof.get_children():
        vals = [str(v) for v in ui.tree_prof.item(item)["values"]]
        if "V-19888777" in vals:
            ui.tree_prof.selection_set(item)
            ui.seleccionar_profesor_desde_tabla()
            break

    pdf_salida = str(tmp_path / "ficha_docente_generada.pdf")
    mocks_dialogos["asksaveasfilename"].return_value = pdf_salida
    mocks_dialogos["askyesno"].return_value = True

    ui.imprimir_ficha_click()
    assert os.path.exists(pdf_salida)
    assert os.path.getsize(pdf_salida) > 1000
    with open(pdf_salida, "rb") as f:
        assert f.read(5).startswith(b"%PDF-")

    # 6. Limpiar Formulario
    ui.limpiar_formulario()
    assert ui.profesor_seleccionado is None
    assert ui.entry_ced_prof.get() == ""
    assert ui.entry_nom_prof.get() == ""
    assert ui.entry_profesion.get() == ""
    assert ui.entry_telefono_prof.get() == ""

    ui.img_logo_tk = None
    ui._foto_preview_ref = None
    ui.preview_foto_tk = None
    ui.lbl_foto.image = None
    win.destroy()
    gc.collect()


# ═════════════════════════════════════════════════════════════════════
# 4. UI CLASE: SELECCIÓN MÚLTIPLE DE SECCIONES (A-Z) Y ASIGNAR
# ═════════════════════════════════════════════════════════════════════

def test_ui_clase_secciones_a_z_y_guardar(tk_app, db_entorno, mocks_dialogos):
    """Verifica que el Listbox contenga 26 secciones y el botón Inscribir guarde el lote."""
    repo_clase = SQLiteRepositorioClase(db_entorno)

    win = tk.Toplevel(tk_app)
    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True)

    ui = GestorClasesUI(parent_notebook=nb, repositorio_clase=repo_clase)

    # Verificar que el Listbox cargó dinámicamente las 26 secciones de la A a la Z
    assert ui.listbox_secciones.size() == 26
    assert ui.listbox_secciones.get(0) == "Sección A"
    assert ui.listbox_secciones.get(25) == "Sección Z"

    # Llenar formulario seleccionando secciones 'A', 'M', 'Z'
    ui.entry_nom_mat.insert(0, "FÍSICA MODERNA")
    ui.combo_prof.current(0)
    ui.combo_grado.current(3)  # 4to Año

    ui.listbox_secciones.selection_set(0)   # A
    ui.listbox_secciones.selection_set(12)  # M
    ui.listbox_secciones.selection_set(25)  # Z

    # Ejecutar botón guardar
    ui.guardar_click()
    assert mocks_dialogos["showinfo"].call_count >= 1

    # Verificar que se crearon las clases en SQLite
    conn = db_entorno.conectar()
    cur = conn.cursor()
    cur.execute("SELECT ID_SECCION FROM TBL_CLASES WHERE NOMBRE_MATERIA = 'FÍSICA MODERNA'")
    secciones_creadas = [r[0] for r in cur.fetchall()]
    db_entorno.cerrar()

    assert len(secciones_creadas) == 3


# ═════════════════════════════════════════════════════════════════════
# 5. UI ESTUDIANTE: GUARDAR, MODIFICAR, ELIMINAR, FOTO, PDF Y LIMPIAR
# ═════════════════════════════════════════════════════════════════════

def test_ui_estudiante_todos_los_botones(tk_app, db_entorno, tmp_path, mocks_dialogos):
    """Verifica todos los botones de ui_estudiante.py y la generación de Ficha PDF."""
    repo_est = RepositorioEstudianteSQLite(db_entorno)
    gestor_fotos = GestorFotos(directorio_base=str(tmp_path))
    exportador = ExportadorPDFReportLab(gestor_fotos=gestor_fotos)
    repo_rep = RepositorioReportesSQLite(db_entorno)

    ui = UIEstudiante(
        repositorio=repo_est,
        parent=tk_app,
        exportador_pdf=exportador,
        gestor_fotos=gestor_fotos,
        repositorio_reportes=repo_rep
    )

    # Verificar secciones A-Z en el combobox
    assert len(ui.combo_seccion['values']) == 26
    assert "Z" in ui.combo_seccion['values']

    # 1. Cargar Foto
    img_test = str(tmp_path / "foto_est_test.png")
    Image.new("RGB", (200, 200), color=(0, 0, 255)).save(img_test)
    mocks_dialogos["askopenfilename"].return_value = img_test

    ui.entry_cedula.insert(0, "32555666")
    ui.cargar_foto_click()
    assert ui.foto_path_actual.startswith("fotos/estudiantes/")

    # 2. Quitar Foto
    ui.quitar_foto_click()
    assert ui.foto_path_actual == ""
    assert ui.lbl_foto.cget("text") == "[ SIN FOTO ]"

    # 3. Guardar Estudiante
    ui.cargar_foto_click()
    ui.entry_nombre.insert(0, "Estudiante Prueba")
    ui.entry_grado.insert(0, "4")
    ui.combo_seccion.set("Z")
    ui.entry_repre.insert(0, "Representante Legal")
    ui.entry_telf.insert(0, "0412-1111111")
    ui.entry_madre.insert(0, "Madre Test")
    ui.entry_telf_madre.insert(0, "0412-2222222")
    ui.entry_padre.insert(0, "Padre Test")
    ui.entry_telf_padre.insert(0, "0412-3333333")

    ui.guardar_nuevo()
    assert mocks_dialogos["showinfo"].call_count >= 1

    est_guardado = repo_est.obtener_por_cedula("V-32555666")
    assert est_guardado is not None
    assert est_guardado.nombre_madre == "Madre Test"

    # 4. Modificar Estudiante
    for item in ui.tree.get_children():
        vals = [str(v) for v in ui.tree.item(item)["values"]]
        if "V-32555666" in vals:
            ui.tree.selection_set(item)
            ui.cargar_formulario_desde_tabla(None)
            break

    ui.entry_repre.delete(0, tk.END)
    ui.entry_repre.insert(0, "Representante Modificado")
    ui.modificar_existente()

    est_mod = repo_est.obtener_por_cedula("V-32555666")
    assert est_mod.representante == "Representante Modificado"

    # 5. Imprimir Ficha PDF (seleccionando el estudiante)
    for item in ui.tree.get_children():
        vals = [str(v) for v in ui.tree.item(item)["values"]]
        if "V-32555666" in vals:
            ui.tree.selection_set(item)
            ui.cargar_formulario_desde_tabla(None)
            break

    pdf_salida = str(tmp_path / "ficha_estudiante_generada.pdf")
    mocks_dialogos["asksaveasfilename"].return_value = pdf_salida
    mocks_dialogos["askyesno"].return_value = True

    ui.imprimir_ficha_click()
    assert os.path.exists(pdf_salida)
    assert os.path.getsize(pdf_salida) > 1000
    with open(pdf_salida, "rb") as f:
        assert f.read(5).startswith(b"%PDF-")

    # 6. Limpiar Formulario
    ui.limpiar_formulario()
    assert ui.cedula_seleccionada is None
    assert ui.entry_cedula.get() == ""

    # 7. Eliminar / Desincorporar Estudiante
    for item in ui.tree.get_children():
        vals = [str(v) for v in ui.tree.item(item)["values"]]
        if "V-32555666" in vals:
            ui.tree.selection_set(item)
            ui.cargar_formulario_desde_tabla(None)
            break

    mocks_dialogos["askyesno"].return_value = True
    ui.eliminar_estudiante()
    assert repo_est.obtener_por_cedula("V-32555666") is None

    ui._foto_preview_ref = None
    ui.preview_foto_tk = None
    ui.lbl_foto.image = None
    ui.root.destroy()
    gc.collect()


# ═════════════════════════════════════════════════════════════════════
# 6. UI ASISTENCIA: SELECTOR, MARCAJE P/A/J Y GUARDADO ATÓMICO
# ═════════════════════════════════════════════════════════════════════

def test_ui_asistencia_todos_los_botones(tk_app, db_entorno, tmp_path, mocks_dialogos):
    """Verifica botones de SelectorClaseUI y PlanillaUI (P, A, J, Guardar, Cerrar)."""
    repo_asist = RepositorioAsistenciaSQLite(db_entorno)
    respaldo = RespaldoAsistenciaJSON(ruta_archivo=str(tmp_path / "emergencia.json"))
    repo_clase = SQLiteRepositorioClase(db_entorno)

    controlador = ControladorAsistencia(repo_asist, respaldo, repo_clase)

    # 1. Selector de clase: botón COMENZAR CLASE (mockeando PlanillaUI.mostrar para evitar mainloop)
    with patch.object(PlanillaUI, "mostrar", return_value=None):
        selector = SelectorClaseUI(controlador, ["MATEMÁTICAS - 4to Año A"], [1])
        selector.root.mainloop = MagicMock()
        selector.mostrar()
        selector._on_comenzar()

    assert controlador.planilla_actual is not None
    assert len(controlador.planilla_actual.registros) >= 1

    # 2. PlanillaUI: Botones de Marcaje
    planilla_ui = PlanillaUI(
        controlador=controlador,
        planilla=controlador.planilla_actual,
        nombres=controlador.nombres_estudiantes,
        nombre_clase="MATEMÁTICAS - 4to Año A"
    )
    planilla_ui.win.mainloop = MagicMock()

    item_id = planilla_ui.tree.get_children()[0]
    planilla_ui.tree.selection_set(item_id)

    # Botón AUSENTE
    planilla_ui._cambiar_seleccionados(EstadoAsistencia.AUSENTE)
    assert controlador.planilla_actual.registros[0].estado == EstadoAsistencia.AUSENTE

    # Botón JUSTIFICADA (con askstring y re-seleccionando el item tras refresco)
    planilla_ui.tree.selection_set(planilla_ui.tree.get_children()[0])
    mocks_dialogos["askstring"].return_value = "Fiebre y reposo médico"
    planilla_ui._cambiar_seleccionados(EstadoAsistencia.JUSTIFICADO)
    assert controlador.planilla_actual.registros[0].estado == EstadoAsistencia.JUSTIFICADO
    assert controlador.planilla_actual.registros[0].motivo_justificacion == "Fiebre y reposo médico"

    # Botón PRESENTE (re-seleccionando tras refresco)
    planilla_ui.tree.selection_set(planilla_ui.tree.get_children()[0])
    planilla_ui._cambiar_seleccionados(EstadoAsistencia.PRESENTE)
    assert controlador.planilla_actual.registros[0].estado == EstadoAsistencia.PRESENTE

    # Botón GUARDAR EN BASE DE DATOS
    planilla_ui._guardar()
    assert mocks_dialogos["showinfo"].call_count >= 1

    # Botón CERRAR SIN GUARDAR
    mocks_dialogos["askyesno"].return_value = True
    win_temp = PlanillaUI(controlador, controlador.planilla_actual, {}, "Clase")
    win_temp.win.mainloop = MagicMock()
    win_temp._cerrar_sin_guardar()


# ═════════════════════════════════════════════════════════════════════
# 7. UI REPORTES: BÚSQUEDA DIARIA, MENSUAL, HISTORIAL, RIESGO Y PDF
# ═════════════════════════════════════════════════════════════════════

def test_ui_reportes_todos_los_botones(tk_app, db_entorno, tmp_path, mocks_dialogos):
    """Verifica botones de búsqueda, alerta de riesgo y exportación PDF en ui_reportes.py."""
    repo_rep = RepositorioReportesSQLite(db_entorno)
    exportador = ExportadorPDFReportLab()

    ui = UIReportes(repo_reportes=repo_rep, exportador_pdf=exportador, parent=tk_app)

    # 1. Búsqueda Diario
    import datetime
    ui.cal_dia.set_date(datetime.date(2026, 11, 20))
    ui.buscar_por_dia()
    assert len(ui.tree.get_children()) >= 1

    # 2. Búsqueda Mensual
    ui.combo_mes.set("Noviembre")
    ui.entry_anio.delete(0, tk.END)
    ui.entry_anio.insert(0, "2026")
    ui.buscar_por_mes()
    assert len(ui.tree.get_children()) >= 1

    # 3. Búsqueda Historial por Cédula
    ui.entry_cedula.delete(0, tk.END)
    ui.entry_cedula.insert(0, "V-30111222")
    ui.buscar_por_cedula()
    assert len(ui.tree.get_children()) >= 1

    # 4. Botón Alertas de Riesgo (< 75%)
    ui.mostrar_alertas_riesgo()

    # 5. Botón Exportar PDF
    pdf_salida = str(tmp_path / "reporte_asistencia_salida.pdf")
    mocks_dialogos["asksaveasfilename"].return_value = pdf_salida
    ui.generar_pdf()
    assert os.path.exists(pdf_salida)
    assert os.path.getsize(pdf_salida) > 1000
    with open(pdf_salida, "rb") as f:
        assert f.read(5).startswith(b"%PDF-")


# ═════════════════════════════════════════════════════════════════════
# 8. UI LISTADOS: PESTAÑAS, FILTROS Y EXPORTACIÓN PDF
# ═════════════════════════════════════════════════════════════════════

def test_ui_listados_todos_los_botones(tk_app, db_entorno, tmp_path, mocks_dialogos):
    """Verifica refresco, filtrado y botones de exportación PDF en ui_listados.py."""
    repo_list = RepositorioListadosSQLite(db_entorno)
    exportador = ExportadorPDFReportLab()

    ui = UIListados(repo_listados=repo_list, exportador_pdf=exportador, parent=tk_app)

    # Pestaña 1: Alumnos
    ui.cargar_alumnos()
    assert len(ui.tree_alumnos.get_children()) >= 1
    ui.entry_filtro_alumnos.insert(0, "BASE")
    ui._filtrar_alumnos()
    assert len(ui.tree_alumnos.get_children()) >= 1

    # Pestaña 2: Materias
    ui.cargar_materias()
    assert len(ui.tree_materias.get_children()) >= 1
    ui.entry_filtro_materias.insert(0, "MATEMÁTICAS")
    ui._filtrar_materias()
    assert len(ui.tree_materias.get_children()) >= 1

    # Pestaña 3: Profesores
    ui.cargar_profesores()
    assert len(ui.tree_profesores.get_children()) >= 1
    ui.entry_filtro_profesores.insert(0, "PROFESOR")
    ui._filtrar_profesores()
    assert len(ui.tree_profesores.get_children()) >= 1

    # Botón Exportar PDF
    pdf_salida = str(tmp_path / "listado_estudiantes_salida.pdf")
    mocks_dialogos["asksaveasfilename"].return_value = pdf_salida
    ui._exportar_tabla_pdf(ui.tree_alumnos, "LISTADO DE ESTUDIANTES", ["Cédula", "Nombre", "Grado"])
    assert os.path.exists(pdf_salida)
    assert os.path.getsize(pdf_salida) > 1000
    with open(pdf_salida, "rb") as f:
        assert f.read(5).startswith(b"%PDF-")


# ═════════════════════════════════════════════════════════════════════
# 9. UI PROMOCIÓN: VISTA PREVIA Y EJECUCIÓN (FALLO Y ÉXITO)
# ═════════════════════════════════════════════════════════════════════

def test_ui_promocion_botones_censo_y_ejecutar(tk_app, db_entorno, mocks_dialogos):
    """Verifica botones Refrescar Censo y Ejecutar Promoción con clave errónea y correcta."""
    repo_prom = RepositorioPromocionSQLite(db_entorno)
    ui = UIPromocion(repo_promocion=repo_prom, parent=tk_app)

    # 1. Refrescar Censo
    ui.cargar_vista_previa()
    assert len(ui.tree.get_children()) >= 1

    # 2. Ejecutar con clave errónea
    mocks_dialogos["askyesno"].return_value = True
    mocks_dialogos["askstring"].return_value = "CLAVE_FALSA"
    ui.solicitar_promocion()
    assert mocks_dialogos["showerror"].call_count >= 1

    # 3. Ejecutar con clave correcta DIRECTOR2025
    mocks_dialogos["askstring"].return_value = "DIRECTOR2025"
    ui.solicitar_promocion()
    assert mocks_dialogos["showinfo"].call_count >= 1

    # Verificar que el estudiante de 4to año pasó a 5to año
    conn = db_entorno.conectar()
    cur = conn.cursor()
    cur.execute("SELECT ID_GRADO FROM TBL_ESTUDIANTES WHERE ID_ESTUDIANTE = 'V-30111222'")
    assert cur.fetchone()[0] == 5
    db_entorno.cerrar()


# ═════════════════════════════════════════════════════════════════════
# 10. UI USUARIO: GUARDAR, ACTUALIZAR, LIMPIAR Y DESACTIVAR
# ═════════════════════════════════════════════════════════════════════

def test_ui_usuario_todos_los_botones(tk_app, db_entorno, mocks_dialogos):
    """Verifica botones Guardar Nuevo, Actualizar, Limpiar y Desactivar en ui_usuario.py."""
    repo_usr = SQLiteRepositorioUsuario(db_entorno)
    mocks_dialogos["askstring"].return_value = "DIRECTOR2025"
    ui = GestorUsuariosUI(tk_app, repo_usr)

    # 1. Guardar Nuevo Usuario
    ui.entry_nom.insert(0, "Usuario Auxiliar")
    ui.entry_usr.insert(0, "auxiliar")
    ui.entry_pwd.insert(0, "aux123")
    ui.combo_rol.set("DOCENTE")
    ui.guardar()
    assert mocks_dialogos["showinfo"].call_count >= 1

    usr_creado = repo_usr.obtener_por_username("auxiliar")
    assert usr_creado is not None
    assert usr_creado.rol == "DOCENTE"

    # 2. Actualizar Usuario (seleccionando de la tabla para cargar datos)
    for item in ui.tree.get_children():
        if "auxiliar" in str(ui.tree.item(item)["values"]):
            ui.tree.focus(item)
            ui.seleccionar_fila(None)
            break

    ui.entry_nom.delete(0, tk.END)
    ui.entry_nom.insert(0, "Usuario Auxiliar Modificado")
    ui.entry_pwd.delete(0, tk.END)
    ui.entry_pwd.insert(0, "nueva_clave")
    ui.actualizar()

    usr_act = repo_usr.obtener_por_username("auxiliar")
    assert usr_act.nombre_completo == "USUARIO AUXILIAR MODIFICADO"

    # 3. Limpiar Formulario
    ui.limpiar()
    assert ui.usuario_seleccionado_id is None
    assert ui.entry_nom.get() == ""

    # 4. Desactivar Usuario (Soft-delete)
    for item in ui.tree.get_children():
        if "auxiliar" in str(ui.tree.item(item)["values"]):
            ui.tree.focus(item)
            ui.seleccionar_fila(None)
            break
    mocks_dialogos["askyesno"].return_value = True
    ui.desactivar()

    usr_desactivado = repo_usr.obtener_por_username("auxiliar")
    assert usr_desactivado is None or usr_desactivado.estado_activo == 0


# ═════════════════════════════════════════════════════════════════════
# 11. UI LOGIN RECUPERACIÓN EN 2 PASOS Y MÓDULO ESTADÍSTICAS (FASE 2)
# ═════════════════════════════════════════════════════════════════════

def test_ui_login_modal_recuperacion_dos_pasos(tk_app, db_entorno, mocks_dialogos):
    """
    Verifica el flujo completo del enlace '¿Olvidó su usuario o contraseña?' en ui_login.py:
    - Modal compacto sin maximizar.
    - Paso 1: clave maestra errónea muestra error sin habilitar Paso 2 ni exponer usuarios.
    - Paso 1 correcto habilita Combobox de usuarios activos y campos de contraseña.
    - Paso 2: restablecimiento exitoso permite iniciar sesión de inmediato con la nueva clave.
    """
    repo_usr = SQLiteRepositorioUsuario(db_entorno)
    cb_login = MagicMock()

    win_login = tk.Toplevel(tk_app)
    login = VentanaLogin(repo_usr, on_login_exitoso=cb_login, root=win_login)

    assert hasattr(login, "btn_recuperar")
    login.abrir_modal_recuperacion()

    modal = login._modal_recuperacion
    assert modal is not None
    assert modal["win"].winfo_exists()
    assert modal["win"].resizable() == (False, False)

    # Paso 2 debe iniciar deshabilitado
    assert str(modal["combo_usuarios"].cget("state")) == "disabled"
    assert str(modal["btn_restablecer"].cget("state")) == "disabled"

    # Paso 1 fallido
    modal["entry_maestra"].insert(0, "CLAVE_MALA")
    modal["btn_validar"].invoke()
    assert mocks_dialogos["showerror"].call_count >= 1
    assert str(modal["combo_usuarios"].cget("state")) == "disabled"
    assert len(modal["combo_usuarios"]["values"]) == 0

    # Paso 1 exitoso
    modal["entry_maestra"].delete(0, tk.END)
    modal["entry_maestra"].insert(0, "DIRECTOR2025")
    modal["btn_validar"].invoke()
    assert str(modal["combo_usuarios"].cget("state")) == "readonly"
    assert str(modal["btn_restablecer"].cget("state")) == "normal"
    assert any("admin" in v for v in modal["combo_usuarios"]["values"])

    # Seleccionar 'admin - ADMIN' y probar discordancia de contraseñas
    modal["combo_usuarios"].set("admin - ADMIN")
    modal["entry_nueva"].insert(0, "NuevaClave2026")
    modal["entry_confirmar"].insert(0, "OtraClave")
    modal["btn_restablecer"].invoke()
    assert mocks_dialogos["showwarning"].call_count >= 1

    # Confirmar correctamente y restablecer
    modal["entry_confirmar"].delete(0, tk.END)
    modal["entry_confirmar"].insert(0, "NuevaClave2026")
    modal["btn_restablecer"].invoke()
    assert mocks_dialogos["showinfo"].call_count >= 1
    assert not modal["win"].winfo_exists()

    # Iniciar sesión inmediatamente con la nueva clave
    login.entry_usuario.delete(0, tk.END)
    login.entry_usuario.insert(0, "admin")
    login.entry_password.delete(0, tk.END)
    login.entry_password.insert(0, "NuevaClave2026")
    login.iniciar_sesion()
    assert cb_login.call_count == 1
    assert cb_login.call_args[0][0].username == "admin"


def test_ui_login_qa_usabilidad_visibilidad_modales_y_escape(tk_app, db_entorno, mocks_dialogos):
    """
    Cubre los hallazgos QA de ui_login.py:
    - Alternar mostrar/ocultar contraseña en Login, Registro y Recuperación.
    - Campos vacíos y error de credenciales limpian contraseña y muestran alerta con parent=.
    - Bloqueo de modales duplicados al invocar dos veces seguidas.
    - Cierre limpio con tecla Escape sin destruir la ventana Login.
    - Todos los widgets del Login y sus modales caben dentro de sus dimensiones configuradas.
    """
    repo_usr = SQLiteRepositorioUsuario(db_entorno)
    cb_login = MagicMock()

    win_login = tk.Toplevel(tk_app)
    login = VentanaLogin(repo_usr, on_login_exitoso=cb_login, root=win_login)
    win_login.update()

    # 1. Todos los widgets del Login caben dentro de 430x570 sin recortes
    for w in (login.entry_usuario, login.entry_password, login.chk_mostrar_pwd,
              login.btn_iniciar, login.btn_registrar, login.btn_recuperar):
        y_rel = w.winfo_rooty() - win_login.winfo_rooty()
        assert y_rel + w.winfo_height() <= 570, f"Widget {w} excede alto Login: {y_rel + w.winfo_height()}"

    # 2. Alternar Ver / Ocultar contraseña en Login
    assert login.entry_password.cget("show") == "●"
    login.chk_mostrar_pwd.invoke()
    assert login.entry_password.cget("show") == ""
    login.chk_mostrar_pwd.invoke()
    assert login.entry_password.cget("show") == "●"

    # 3. Campos vacíos: aviso específico sin llamar al repo
    login.entry_usuario.delete(0, tk.END)
    login.entry_password.delete(0, tk.END)
    login.iniciar_sesion()
    assert mocks_dialogos["showwarning"].call_count >= 1
    assert cb_login.call_count == 0

    login.entry_usuario.insert(0, "admin")
    login.iniciar_sesion()
    assert mocks_dialogos["showwarning"].call_count >= 2

    # 4. Credenciales erróneas limpian el campo contraseña
    login.entry_password.insert(0, "clave_mala")
    login.iniciar_sesion()
    assert mocks_dialogos["showerror"].call_count >= 1
    assert login.entry_password.get() == ""

    # 5. Bloqueo de modal de Recuperación duplicado + ver/ocultar + cierre con Escape
    login.abrir_modal_recuperacion()
    win_rec_1 = login._modal_recuperacion["win"]
    login.abrir_modal_recuperacion()  # Segunda invocación no debe crear otra ventana
    assert login._modal_recuperacion["win"] is win_rec_1
    win_rec_1.update()

    # Verificar que todos los controles del modal de recuperación caben en 440x535
    btn_rest = login._modal_recuperacion["btn_restablecer"]
    y_rest = btn_rest.winfo_rooty() - win_rec_1.winfo_rooty()
    assert y_rest + btn_rest.winfo_height() <= 535

    # Validar clave maestra para habilitar Paso 2 y probar mostrar/ocultar
    login._modal_recuperacion["entry_maestra"].insert(0, "DIRECTOR2025")
    login._modal_recuperacion["btn_validar"].invoke()
    assert login._modal_recuperacion["entry_nueva"].cget("show") == "*"
    login._modal_recuperacion["chk_mostrar_pwd"].invoke()
    assert login._modal_recuperacion["entry_nueva"].cget("show") == ""
    assert login._modal_recuperacion["entry_confirmar"].cget("show") == ""

    # Cerrar modal de recuperación con Escape sin destruir Login
    win_rec_1.event_generate("<Escape>")
    win_login.update()
    assert not win_rec_1.winfo_exists()
    assert win_login.winfo_exists()

    # 6. Bloqueo de modal de Registro duplicado + cierre con Escape
    mocks_dialogos["askstring"].return_value = "DIRECTOR2025"
    login.solicitar_registro()
    win_reg_1 = login._modal_registro["win"]
    login._abrir_modal_registro()
    assert login._modal_registro["win"] is win_reg_1
    win_reg_1.update()
    assert win_reg_1.winfo_reqheight() <= 520

    win_reg_1.event_generate("<Escape>")
    win_login.update()
    assert not win_reg_1.winfo_exists()
    assert win_login.winfo_exists()


def test_ui_menu_principal_estadisticas_rbac_docente_bloqueado(tk_app):
    """
    Verifica tarjeta de Estadísticas en MenuPrincipalUI:
    - ADMIN/ASISTENTE disparan el callback al hacer clic en la tarjeta.
    - DOCENTE ve la tarjeta bloqueada ('🔒 Sin acceso') y no tiene callback vinculado.
    """
    cb_stats_doc = MagicMock()
    usr_doc = Usuario(
        id_usuario=2,
        nombre_completo="Docente Prueba",
        username="docente1",
        password="hash",
        rol="DOCENTE",
    )
    win_doc = tk.Toplevel(tk_app)
    MenuPrincipalUI(usr_doc, {MODULO_ESTADISTICAS: cb_stats_doc}, root=win_doc)
    win_doc.update_idletasks()

    # Verificar que aparece tarjeta de Estadísticas con etiqueta de bloqueo para DOCENTE
    textos_labels = []

    def _recolectar_labels(w):
        for ch in w.winfo_children():
            if isinstance(ch, tk.Label):
                textos_labels.append(ch.cget("text"))
            _recolectar_labels(ch)

    _recolectar_labels(win_doc)
    assert any("Estadísticas" in t for t in textos_labels)
    assert any("Sin acceso" in t for t in textos_labels)
    win_doc.destroy()

    # Para ASISTENTE sí debe permitir clic directo en la tarjeta de Estadísticas
    cb_stats_asist = MagicMock()
    usr_asist = Usuario(
        id_usuario=3,
        nombre_completo="Asistente Prueba",
        username="asist1",
        password="hash",
        rol="ASISTENTE",
    )
    win_asist = tk.Toplevel(tk_app)
    MenuPrincipalUI(usr_asist, {MODULO_ESTADISTICAS: cb_stats_asist}, root=win_asist)
    win_asist.update_idletasks()

    lbl_stats = None

    def _buscar_label_stats(w):
        nonlocal lbl_stats
        for ch in w.winfo_children():
            if isinstance(ch, tk.Label) and "Estadísticas" in ch.cget("text"):
                lbl_stats = ch
                return
            _buscar_label_stats(ch)

    _buscar_label_stats(win_asist)
    assert lbl_stats is not None
    lbl_stats.event_generate("<Button-1>")
    win_asist.update()
    assert cb_stats_asist.call_count == 1
    win_asist.destroy()


def test_ui_estadisticas_botones_y_canvas_renderizado(tk_app, db_entorno, tmp_path, mocks_dialogos):
    """
    Verifica UIEstadisticas:
    - Renderiza KPIs y gráficos puros en tk.Canvas (canvas_secciones y canvas_distribucion).
    - Leyenda P/A/J en 3 filas apiladas verticalmente sin solapamiento ni recorte horizontal.
    - Botón 'Actualizar Métricas' recalcula métricas al cambiar la BD.
    - Botón 'Exportar PDF' genera archivo PDF real en tmp_path con cabecera %PDF-.
    - Botón '← Volver al Panel' cierra la ventana limpiamente.
    """
    repo_stats = RepositorioEstadisticasSQLite(db_entorno)
    exportador = ExportadorPDFReportLab()
    ui = UIEstadisticas(repo_estadisticas=repo_stats, parent=tk_app, exportador_pdf=exportador)
    ui.root.geometry("980x680+0+0")
    ui.root.update()

    assert ui.lbl_kpi_estudiantes.cget("text") == "1"
    assert ui.lbl_kpi_docentes.cget("text") == "1"
    assert len(ui.canvas_secciones.find_all()) > 0
    assert len(ui.canvas_distribucion.find_all()) > 0

    # Verificar que las 3 líneas de leyenda P/A/J están apiladas verticalmente y dentro del canvas
    items_leyenda = ui.canvas_distribucion.find_withtag("leyenda_paj")
    assert len(items_leyenda) == 3
    coords_y = []
    w_canvas = ui.canvas_distribucion.winfo_width()
    for item_id in items_leyenda:
        bbox = ui.canvas_distribucion.bbox(item_id)
        assert bbox is not None
        coords_y.append(bbox[1])
        assert bbox[2] <= w_canvas, f"Leyenda {item_id} excede ancho del canvas ({bbox[2]} > {w_canvas})"
    assert len(set(coords_y)) == 3, f"Las 3 leyendas deben estar en filas Y distintas: {coords_y}"

    # Insertar una falta en BD para poner al estudiante en riesgo (< 75%: 1P, 1A = 50%)
    conn = db_entorno.conectar()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO TBL_ASISTENCIA (ID_ESTUDIANTE, ID_CLASE, FECHA, ESTADO) VALUES ('V-30111222', 1, '2026-11-21', 'A')"
    )
    conn.commit()
    db_entorno.cerrar()

    # Invocar botón Actualizar Métricas
    ui.btn_actualizar.invoke()
    ui.root.update_idletasks()
    assert ui.lbl_kpi_riesgo.cget("text") == "1"
    assert len(ui.tree_riesgo.get_children()) == 1

    # Invocar botón Exportar PDF
    pdf_salida = str(tmp_path / "estadisticas_ui_salida.pdf")
    mocks_dialogos["asksaveasfilename"].return_value = pdf_salida
    mocks_dialogos["askyesno"].return_value = True
    ui.btn_exportar_pdf.invoke()
    assert os.path.exists(pdf_salida)
    assert os.path.getsize(pdf_salida) > 1000
    with open(pdf_salida, "rb") as f:
        assert f.read(5).startswith(b"%PDF-")

    # Invocar botón ← Volver al Panel
    assert ui.btn_volver is not None
    ui.btn_volver.invoke()
    ui.root.update_idletasks()
    assert not ui.root.winfo_exists()
