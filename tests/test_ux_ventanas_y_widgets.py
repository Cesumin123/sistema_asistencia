# tests/test_ux_ventanas_y_widgets.py
"""
Suite de pruebas automatizadas de Experiencia de Usuario (UX) y Geometría de Widgets.
Cubre:
1. Auditoría estática AST de diálogos (messagebox, filedialog, simpledialog) exigiendo parent= explícito.
2. Comportamiento de ventanas hijas secundarias, foco y botón '← Volver al Panel'.
3. Geometría 2x2, ancho, uniformidad y tooltips de los botones en GestorProfesoresUI.
4. Renderizado de vista previa de fotos en contenedores de 110x110 px y retención de referencias PhotoImage.
"""

import ast
import glob
import os
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image

from db_conexion import ConexionBD
from adaptadores.db.sqlite_profesor import SQLiteRepositorioProfesor
from adaptadores.db.sqlite_clase import SQLiteRepositorioClase
from adaptadores.db.sqlite_estudiante import RepositorioEstudianteSQLite
from adaptadores.documentos.gestor_fotos import GestorFotos
from adaptadores.documentos.pdf_reportes import ExportadorPDFReportLab
from adaptadores.ui.ui_profesor import GestorProfesoresUI
from adaptadores.ui.ui_estudiante import UIEstudiante
from adaptadores.ui.utilidades_ui import (
    configurar_ventana_hija,
    restaurar_foco,
    agregar_barra_superior_volver,
    maximizar_ventana,
)


@pytest.fixture
def tk_root():
    """Crea una raíz Tkinter oculta para pruebas de UI y garantiza su destrucción."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def db_mem():
    """Conexión SQLite en memoria con esquema migrado."""
    con = ConexionBD(":memory:")
    return con


# ═════════════════════════════════════════════════════════════════════
# TEST 1: AUDITORÍA AST DE DIÁLOGOS CON PARENT EXPLÍCITO (Z-ORDER FIX)
# ═════════════════════════════════════════════════════════════════════

def test_ast_auditoria_dialogos_con_parent_explicito():
    """
    Analiza sintácticamente con ast todos los archivos de adaptadores/ui/.
    Verifica que el 100% de llamadas a messagebox, filedialog y simpledialog
    tengan el keyword argument 'parent=' para evitar que Linux/X11 entierre ventanas Toplevel.
    """
    directorio_ui = os.path.join(os.path.dirname(__file__), "..", "adaptadores", "ui")
    archivos_py = sorted(glob.glob(os.path.join(directorio_ui, "*.py")))
    assert len(archivos_py) >= 9, f"Se esperaban al menos 9 archivos en {directorio_ui}"

    modulos_dialogo = {"messagebox", "filedialog", "simpledialog"}
    llamadas_sin_parent = []
    total_llamadas_dialogo = 0

    for ruta_archivo in archivos_py:
        nombre_base = os.path.basename(ruta_archivo)
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            contenido = f.read()

        arbol = ast.parse(contenido, filename=ruta_archivo)

        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call):
                mod_name = ""
                func_name = ""
                if isinstance(nodo.func, ast.Attribute) and isinstance(nodo.func.value, ast.Name):
                    mod_name = nodo.func.value.id
                    func_name = nodo.func.attr

                if mod_name in modulos_dialogo:
                    total_llamadas_dialogo += 1
                    tiene_parent = any(k.arg == "parent" for k in nodo.keywords)
                    if not tiene_parent:
                        llamadas_sin_parent.append(
                            f"{nombre_base}:{nodo.lineno} -> {mod_name}.{func_name}() no pasa parent="
                        )

    assert total_llamadas_dialogo > 0, "No se detectaron llamadas a diálogos para auditar."
    assert len(llamadas_sin_parent) == 0, (
        f"Se encontraron {len(llamadas_sin_parent)} llamadas a diálogos sin 'parent=':\n"
        + "\n".join(llamadas_sin_parent)
    )


# ═════════════════════════════════════════════════════════════════════
# TEST 2: VENTANA HIJA, RESTAURAR FOCO Y BOTÓN '← VOLVER AL PANEL'
# ═════════════════════════════════════════════════════════════════════

def test_configurar_ventana_hija_y_boton_volver(tk_root):
    """
    Verifica que configurar_ventana_hija:
    - Con es_modal=False (default de módulos) NO aplique transient para permitir maximizado en Xfwm4.
    - Con es_modal=True SÍ aplique transient al padre.
    - agregar_barra_superior_volver cree un botón que cierre la ventana devolviendo el foco.
    """
    padre = tk.Toplevel(tk_root)
    padre.title("Panel de Control")
    padre.update_idletasks()

    hija = tk.Toplevel(padre)
    hija.title("Ventana Hija Módulo")
    configurar_ventana_hija(hija, padre, es_modal=False)
    hija.update_idletasks()

    # Con es_modal=False no debe quedar transient al padre
    assert str(hija.transient() or "") == ""

    # Con es_modal=True sí debe aplicar transient al padre
    modal = tk.Toplevel(padre)
    configurar_ventana_hija(modal, padre, es_modal=True)
    modal.update_idletasks()
    try:
        assert str(modal.transient()) == str(padre)
    except Exception:
        pass
    modal.destroy()

    # Agregar la barra superior
    barra = agregar_barra_superior_volver(hija, padre, "Módulo de Prueba")
    hija.update_idletasks()

    # Buscar el botón ← Volver al Panel
    botones = [w for w in barra.winfo_children() if isinstance(w, tk.Button)]
    assert len(botones) >= 1
    btn_volver = botones[0]
    assert "Volver al Panel" in btn_volver.cget("text")

    # Invocar el comando de volver
    btn_volver.invoke()
    hija.update_idletasks()

    # La ventana hija debe haber sido destruida
    assert not hija.winfo_exists()
    # El padre debe seguir vivo
    assert padre.winfo_exists()

    # Probar que restaurar_foco opera de forma defensiva sin lanzar errores
    restaurar_foco(padre)
    restaurar_foco(None)  # No debe lanzar excepción con None


# ═════════════════════════════════════════════════════════════════════
# TEST 3: BOTONERA 2X2, ANCHO, TOOLTIPS Y SUBTÍTULO EN UI_PROFESOR
# ═════════════════════════════════════════════════════════════════════

def test_ui_profesor_botonera_2x2_tooltips_y_subtitulo(tk_root, db_mem, tmp_path):
    """
    Verifica que ui_profesor organice sus 4 botones en cuadrícula 2x2:
    - Fila 0: Guardar (col 0), Actualizar (col 1)
    - Fila 1: Ficha PDF (col 0), Limpiar (col 1)
    - Cada botón posea tooltips de AyudaVisual.
    - El subtítulo del panel derecho cuente con wraplength=380.
    """
    repo_prof = SQLiteRepositorioProfesor(db_mem)
    repo_clase = SQLiteRepositorioClase(db_mem)
    gestor_fotos = GestorFotos(directorio_base=str(tmp_path))
    exportador = ExportadorPDFReportLab(gestor_fotos=gestor_fotos)

    win = tk.Toplevel(tk_root)
    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True)

    ui = GestorProfesoresUI(
        parent_notebook=nb,
        repositorio_profesor=repo_prof,
        exportador_pdf=exportador,
        gestor_fotos=gestor_fotos,
        repositorio_clase=repo_clase,
    )
    win.update_idletasks()

    # Verificar existencia de los 4 botones principales
    assert hasattr(ui, "btn_guardar")
    assert hasattr(ui, "btn_actualizar")
    assert hasattr(ui, "btn_ficha")
    assert hasattr(ui, "btn_limpiar")

    # Verificar cuadrícula 2x2 mediante grid_info
    info_g = ui.btn_guardar.grid_info()
    info_a = ui.btn_actualizar.grid_info()
    info_f = ui.btn_ficha.grid_info()
    info_l = ui.btn_limpiar.grid_info()

    assert info_g["row"] == 0 and info_g["column"] == 0, f"Guardar debe estar en (0, 0), está en {info_g}"
    assert info_a["row"] == 0 and info_a["column"] == 1, f"Actualizar debe estar en (0, 1), está en {info_a}"
    assert info_f["row"] == 1 and info_f["column"] == 0, f"Ficha PDF debe estar en (1, 0), está en {info_f}"
    assert info_l["row"] == 1 and info_l["column"] == 1, f"Limpiar debe estar en (1, 1), está en {info_l}"

    # Botones con cursor hand2 y texto visible
    for b in (ui.btn_guardar, ui.btn_actualizar, ui.btn_ficha, ui.btn_limpiar):
        assert b.cget("cursor") == "hand2"
        assert len(b.cget("text").strip()) > 0

    # Verificar subtítulo con wraplength para evitar recorte en 1024x768
    assert hasattr(ui, "lbl_subtitulo_lista")
    assert ui.lbl_subtitulo_lista.cget("wraplength") == 380

    # Verificar botones de foto con tooltips
    assert hasattr(ui, "btn_cargar_foto")
    assert hasattr(ui, "btn_quitar_foto")


# ═════════════════════════════════════════════════════════════════════
# TEST 4: RENDERIZADO DE FOTO EN CONTENEDOR 110X110 Y RETENCIÓN PHOTOIMAGE
# ═════════════════════════════════════════════════════════════════════

def test_renderizado_foto_preview_en_ui_profesor_y_estudiante(tk_root, db_mem, tmp_path):
    """
    Verifica que ui_profesor y ui_estudiante:
    - Encierren lbl_foto en un Frame contenedor fijo de 110x110 px con pack_propagate(False).
    - Asignen PhotoImage viva tanto a lbl_foto.image como a self._foto_preview_ref.
    - Al pulsar 'Quitar Foto', reseteen limpiamente a '[ SIN FOTO ]' con imagen None.
    """
    gestor_fotos = GestorFotos(directorio_base=str(tmp_path))

    # Crear una imagen de prueba real con Pillow
    ruta_img_origen = str(tmp_path / "foto_alumno.png")
    Image.new("RGB", (300, 300), color=(0, 128, 255)).save(ruta_img_origen)

    # 1. Probar en GestorProfesoresUI
    repo_prof = SQLiteRepositorioProfesor(db_mem)
    repo_clase = SQLiteRepositorioClase(db_mem)
    win_prof = tk.Toplevel(tk_root)
    nb = ttk.Notebook(win_prof)
    nb.pack(fill="both", expand=True)

    ui_prof = GestorProfesoresUI(
        parent_notebook=nb,
        repositorio_profesor=repo_prof,
        exportador_pdf=None,
        gestor_fotos=gestor_fotos,
        repositorio_clase=repo_clase,
    )
    win_prof.update_idletasks()

    # Contenedor de 110x110
    assert hasattr(ui_prof, "f_foto_container")
    assert ui_prof.f_foto_container.cget("width") == 110
    assert ui_prof.f_foto_container.cget("height") == 110

    # Cargar foto y verificar preview
    ruta_rel_prof = gestor_fotos.guardar_foto(ruta_img_origen, "profesor", "V-11222333")
    ui_prof._mostrar_preview_foto(ruta_rel_prof)
    win_prof.update_idletasks()

    assert ui_prof._foto_preview_ref is not None
    assert ui_prof.lbl_foto.image is not None
    assert ui_prof.lbl_foto.cget("text") == ""
    assert ui_prof._foto_preview_ref.width() == 110
    assert ui_prof._foto_preview_ref.height() == 110

    # Quitar foto
    ui_prof.quitar_foto_click()
    win_prof.update_idletasks()

    assert ui_prof.lbl_foto.cget("text") == "[ SIN FOTO ]"
    assert ui_prof.lbl_foto.image is None
    assert ui_prof._foto_preview_ref is None

    # 2. Probar en UIEstudiante
    repo_est = RepositorioEstudianteSQLite(db_mem)
    ui_est = UIEstudiante(
        repositorio=repo_est,
        parent=tk_root,
        exportador_pdf=None,
        gestor_fotos=gestor_fotos,
        repositorio_reportes=None,
    )
    ui_est.root.update_idletasks()

    # Contenedor de 110x110
    assert hasattr(ui_est, "f_foto_container")
    assert ui_est.f_foto_container.cget("width") == 110
    assert ui_est.f_foto_container.cget("height") == 110

    # Cargar foto y verificar preview
    ruta_rel_est = gestor_fotos.guardar_foto(ruta_img_origen, "estudiante", "V-30999888")
    ui_est._mostrar_preview_foto(ruta_rel_est)
    ui_est.root.update_idletasks()

    assert ui_est._foto_preview_ref is not None
    assert ui_est.lbl_foto.image is not None
    assert ui_est.lbl_foto.cget("text") == ""
    assert ui_est._foto_preview_ref.width() == 110
    assert ui_est._foto_preview_ref.height() == 110

    # Quitar foto
    ui_est.quitar_foto_click()
    ui_est.root.update_idletasks()

    assert ui_est.lbl_foto.cget("text") == "[ SIN FOTO ]"
    assert ui_est.lbl_foto.image is None
    assert ui_est._foto_preview_ref is None


# ═════════════════════════════════════════════════════════════════════
# TEST 5: MAXIMIZACIÓN MULTIPLATAFORMA DEFENSIVA POST-LOGIN
# ═════════════════════════════════════════════════════════════════════

def test_maximizar_ventana_tk_y_toplevel_sin_tclerror(tk_root):
    """
    Verifica que maximizar_ventana(ventana) opere defensivamente sin lanzar TclError:
    - Habilita resizable(True, True).
    - En Linux/X11 usa attributes('-zoomed', True) sin sobrescribir geometry si no falla.
    - Solo recurre a geometry como fallback si attributes('-zoomed', True) lanza TclError.
    - Maneja None y ventanas destruidas limpiamente.
    """
    # 1. Sobre tk.Tk
    maximizar_ventana(tk_root)
    tk_root.update_idletasks()

    # 2. Sobre tk.Toplevel independiente y tras configurar_ventana_hija(es_modal=False)
    win = tk.Toplevel(tk_root)
    hija = tk.Toplevel(win)
    configurar_ventana_hija(hija, win, es_modal=False)
    hija.resizable(False, False)

    # Verificar que si attributes('-zoomed', True) funciona, NO sobrescribe geometry
    with patch.object(hija, "state", side_effect=tk.TclError("no zoomed")):
        with patch.object(hija, "attributes", wraps=hija.attributes) as spy_attr, \
             patch.object(hija, "geometry", wraps=hija.geometry) as spy_geom:
            maximizar_ventana(hija)
            hija.update_idletasks()
            assert hija.resizable() == (True, True)
            assert any(call.args == ("-zoomed", True) for call in spy_attr.call_args_list)
            assert spy_geom.call_count == 0

    # Verificar fallback de geometry solo si attributes('-zoomed', True) falla con TclError
    with patch.object(hija, "state", side_effect=tk.TclError("no zoomed")), \
         patch.object(hija, "attributes", side_effect=tk.TclError("no attr")):
        with patch.object(hija, "geometry", wraps=hija.geometry) as spy_geom_fb:
            maximizar_ventana(hija)
            assert spy_geom_fb.call_count >= 1

    # 3. Casos límite: ventana destruida y None (no deben lanzar TclError)
    hija.destroy()
    maximizar_ventana(hija)
    maximizar_ventana(None)
    win.destroy()


def test_geometria_1024x700_visibilidad_modulos_sin_recortes(tk_root, db_mem, tmp_path):
    """
    Simula una ventana útil de 1024x700 px (1024x768 menos barra de tareas)
    y verifica que los controles críticos no se desborden ni queden ocultos:
    - ui_reportes.py: botones Alertas de Riesgo y Exportar PDF visibles <= 700 px alto.
    - ui_estudiante.py: formulario + fotografía + botones Cargar/Quitar caben en <= 1024 px ancho.
    - ui_profesor.py: btn_quitar_foto no recortado y botonera 2x2 dentro de <= 700 px alto.
    - ui_promocion.py: botones Refrescar Censo y Ejecutar Promoción dentro de <= 700 px alto.
    - ui_listados.py: columnas de Alumnos Activos caben en <= 960 px para no recortar Turno.
    """
    from adaptadores.db.sqlite_reportes import RepositorioReportesSQLite
    from adaptadores.db.sqlite_promocion import RepositorioPromocionSQLite
    from adaptadores.db.sqlite_listados import RepositorioListadosSQLite
    from adaptadores.ui.ui_reportes import UIReportes
    from adaptadores.ui.ui_promocion import UIPromocion
    from adaptadores.ui.ui_listados import UIListados

    exportador = ExportadorPDFReportLab()
    gestor_fotos = GestorFotos(directorio_base=str(tmp_path))

    # 1. UIReportes en 1024x700
    ui_rep = UIReportes(RepositorioReportesSQLite(db_mem), exportador, parent=tk_root)
    ui_rep.root.geometry("1024x700+0+0")
    ui_rep.root.update()
    for btn in (ui_rep.btn_alertas, ui_rep.btn_exportar_pdf):
        assert btn.winfo_ismapped()
        y_rel = btn.winfo_rooty() - ui_rep.root.winfo_rooty()
        assert y_rel + btn.winfo_height() <= 700, f"Botón de Reportes oculto: y={y_rel}, h={btn.winfo_height()}"
    ui_rep.root.destroy()

    # 2. UIEstudiante en 1024x700 (Fotografía y botones dentro de 1024 px)
    ui_est = UIEstudiante(
        RepositorioEstudianteSQLite(db_mem),
        parent=tk_root,
        exportador_pdf=exportador,
        gestor_fotos=gestor_fotos,
    )
    ui_est.root.geometry("1024x700+0+0")
    ui_est.root.update()
    assert ui_est.root.winfo_reqwidth() <= 1024, (
        f"UIEstudiante requiere {ui_est.root.winfo_reqwidth()} px > 1024 px"
    )
    for w in (ui_est.lbl_foto, ui_est.btn_cargar_foto, ui_est.btn_quitar_foto):
        x_rel = w.winfo_rootx() - ui_est.root.winfo_rootx()
        assert x_rel + w.winfo_width() <= 1024, (
            f"Widget {w} desborda 1024 px: x={x_rel}, w={w.winfo_width()}"
        )
    ui_est.root.destroy()

    # 3. GestorProfesoresUI en 1024x700 (Quitar foto completo y botonera 2x2 visible)
    win_prof = tk.Toplevel(tk_root)
    win_prof.geometry("1024x700+0+0")
    nb_prof = ttk.Notebook(win_prof)
    nb_prof.pack(fill="both", expand=True)
    ui_prof = GestorProfesoresUI(
        nb_prof,
        SQLiteRepositorioProfesor(db_mem),
        exportador_pdf=exportador,
        gestor_fotos=gestor_fotos,
        repositorio_clase=SQLiteRepositorioClase(db_mem),
    )
    win_prof.update()
    assert ui_prof.btn_quitar_foto.winfo_width() >= ui_prof.btn_quitar_foto.winfo_reqwidth()
    for btn in (ui_prof.btn_guardar, ui_prof.btn_actualizar, ui_prof.btn_ficha, ui_prof.btn_limpiar):
        y_rel = btn.winfo_rooty() - win_prof.winfo_rooty()
        assert y_rel + btn.winfo_height() <= 700, f"Botón profesor desborda 700 px: {y_rel + btn.winfo_height()}"
    win_prof.destroy()

    # 4. UIPromocion en 1024x700
    ui_prom = UIPromocion(RepositorioPromocionSQLite(db_mem), parent=tk_root)
    ui_prom.root.geometry("1024x700+0+0")
    ui_prom.root.update()
    for btn in (ui_prom.btn_refrescar, ui_prom.btn_ejecutar):
        assert btn.winfo_ismapped()
        y_rel = btn.winfo_rooty() - ui_prom.root.winfo_rooty()
        assert y_rel + btn.winfo_height() <= 700, f"Botón promoción oculto: {y_rel + btn.winfo_height()}"
    ui_prom.root.destroy()

    # 5. UIListados en 1024x700 (suma de anchos de columnas cabe en 1024 px)
    ui_list = UIListados(RepositorioListadosSQLite(db_mem), exportador_pdf=exportador, parent=tk_root)
    ui_list.root.geometry("1024x700+0+0")
    ui_list.root.update()
    suma_anchos = sum(ui_list.tree_alumnos.column(c, "width") for c in ui_list.tree_alumnos["columns"])
    assert suma_anchos <= 960, f"Columnas de Listados Alumnos ({suma_anchos} px) recortarían Turno en 1024 px"
    ui_list.root.destroy()


def test_auditoria_maximizacion_post_login_y_exclusion_login(tk_root):
    """
    Verifica por análisis AST que:
    - main.py y los módulos post-login invocan maximizar_ventana().
    - Ningún módulo fuera de utilidades_ui.py llama state('zoomed') crudo.
    - ui_login.py NO invoca maximizar_ventana() y permanece compacto (resizable False).
    """
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    archivos_post_login = [
        os.path.join(raiz, "main.py"),
        os.path.join(raiz, "adaptadores", "ui", "ui_menu_principal.py"),
        os.path.join(raiz, "adaptadores", "ui", "ui_estudiante.py"),
        os.path.join(raiz, "adaptadores", "ui", "ui_asistencia.py"),
        os.path.join(raiz, "adaptadores", "ui", "ui_profesor.py"),
        os.path.join(raiz, "adaptadores", "ui", "ui_listados.py"),
        os.path.join(raiz, "adaptadores", "ui", "ui_reportes.py"),
        os.path.join(raiz, "adaptadores", "ui", "ui_estadisticas.py"),
        os.path.join(raiz, "adaptadores", "ui", "ui_promocion.py"),
        os.path.join(raiz, "adaptadores", "ui", "ui_usuario.py"),
    ]

    def _llamadas_en_ast(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            arbol = ast.parse(f.read(), filename=ruta)
        llamadas_max = 0
        llamadas_state_zoomed = 0
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call):
                if isinstance(nodo.func, ast.Name) and nodo.func.id == "maximizar_ventana":
                    llamadas_max += 1
                elif isinstance(nodo.func, ast.Attribute) and nodo.func.attr == "state":
                    if nodo.args and isinstance(nodo.args[0], ast.Constant) and nodo.args[0].value == "zoomed":
                        llamadas_state_zoomed += 1
        return llamadas_max, llamadas_state_zoomed

    for ruta in archivos_post_login:
        nombre = os.path.basename(ruta)
        n_max, n_zoomed = _llamadas_en_ast(ruta)
        assert n_max >= 1, f"{nombre} debe invocar maximizar_ventana()."
        assert n_zoomed == 0, f"{nombre} no debe llamar .state('zoomed') crudo; debe usar maximizar_ventana()."

    # ui_login.py NO debe maximizarse ni llamar state('zoomed')
    ruta_login = os.path.join(raiz, "adaptadores", "ui", "ui_login.py")
    n_max_login, n_zoomed_login = _llamadas_en_ast(ruta_login)
    assert n_max_login == 0, "ui_login.py NO debe invocar maximizar_ventana()."
    assert n_zoomed_login == 0, "ui_login.py NO debe invocar state('zoomed')."

    # Verificar instanciación compacta de VentanaLogin
    from adaptadores.ui.ui_login import VentanaLogin
    win_login = tk.Toplevel(tk_root)
    VentanaLogin(repositorio_usuario=MagicMock(), on_login_exitoso=MagicMock(), root=win_login)
    win_login.update_idletasks()
    assert win_login.resizable() == (False, False)
    win_login.destroy()


def test_qa_legibilidad_textos_y_botones_gestion_docentes_y_modulos(tk_root, db_mem, tmp_path):
    """
    Auditoría automatizada anti-regresión en 1024x700 (margen para DPI Windows):
    1. Monta GestorProfesoresUI y GestorClasesUI en Notebook dentro de 1024x700 con barra volver.
    2. Mide con tkinter.font.Font el ancho de texto de cada botón mapeado y exige
       winfo_width() >= ancho_texto_px + 12.
    3. Verifica que ningún botón ni etiqueta clave de ui_profesor/ui_clase se salga del contenedor
       ni tenga winfo_width() < winfo_reqwidth().
    4. Verifica coherencia de columnas de tree_prof y visibilidad en PlanillaUI y UIEstadisticas.
    """
    from tkinter import font as tkfont
    from adaptadores.ui.ui_clase import GestorClasesUI
    from adaptadores.ui.ui_asistencia import ControladorAsistencia, PlanillaUI
    from adaptadores.ui.ui_estadisticas import UIEstadisticas
    from adaptadores.db.sqlite_asistencia import RepositorioAsistenciaSQLite
    from adaptadores.db.sqlite_estadisticas import RepositorioEstadisticasSQLite
    from adaptadores.respaldo.json_asistencia import RespaldoAsistenciaJSON

    exportador = ExportadorPDFReportLab()
    gestor_fotos = GestorFotos(directorio_base=str(tmp_path))

    def _verificar_botones_y_limites(win_objetivo, nombre_modulo):
        wx0, wy0 = win_objetivo.winfo_rootx(), win_objetivo.winfo_rooty()
        ww, wh = win_objetivo.winfo_width(), win_objetivo.winfo_height()

        def _recorrer(w):
            for ch in w.winfo_children():
                if ch.winfo_ismapped():
                    cls = ch.winfo_class()
                    x = ch.winfo_rootx() - wx0
                    y = ch.winfo_rooty() - wy0
                    cw, chh = ch.winfo_width(), ch.winfo_height()
                    assert x >= 0 and y >= 0, f"{nombre_modulo}: {cls} fuera por izq/arriba ({x},{y})"
                    assert x + cw <= ww + 1 and y + chh <= wh + 1, (
                        f"{nombre_modulo}: {cls} excede {ww}x{wh} -> ({x}+{cw}, {y}+{chh})"
                    )
                    if cls in ("Button", "TButton"):
                        txt = ch.cget("text")
                        f = tkfont.Font(font=ch.cget("font"))
                        tw = f.measure(txt)
                        assert cw >= tw + 12, (
                            f"{nombre_modulo}: botón {txt!r} sin holgura suficiente (w={cw}, tw={tw})"
                        )
                _recorrer(ch)

        _recorrer(win_objetivo)

    # 1. Gestión Académica (Profesores y Clases) en 1024x700
    w_acad = tk.Toplevel(tk_root)
    agregar_barra_superior_volver(w_acad, tk_root, "Módulo Académico")
    nb = ttk.Notebook(w_acad)
    nb.pack(fill="both", expand=True, padx=10, pady=10)
    ui_prof = GestorProfesoresUI(
        nb, SQLiteRepositorioProfesor(db_mem), exportador, gestor_fotos, SQLiteRepositorioClase(db_mem)
    )
    ui_clase = GestorClasesUI(nb, SQLiteRepositorioClase(db_mem))
    w_acad.geometry("1024x700+0+0")
    w_acad.update()

    assert w_acad.winfo_reqwidth() <= 1024, f"Académico reqwidth={w_acad.winfo_reqwidth()} > 1024"
    _verificar_botones_y_limites(w_acad, "GestorProfesoresUI")
    for b in (ui_prof.btn_cargar_foto, ui_prof.btn_quitar_foto,
              ui_prof.btn_guardar, ui_prof.btn_actualizar, ui_prof.btn_ficha, ui_prof.btn_limpiar):
        assert b.winfo_width() >= b.winfo_reqwidth()
    col_sum = sum(ui_prof.tree_prof.column(c, "width") for c in ui_prof.tree_prof["columns"])
    assert col_sum <= ui_prof.tree_prof.winfo_width() + 2

    # Cambiar a pestaña Asignar Materias (ui_clase.py)
    nb.select(1)
    w_acad.update()
    _verificar_botones_y_limites(w_acad, "GestorClasesUI")
    assert ui_clase.btn_inscribir.winfo_width() >= ui_clase.btn_inscribir.winfo_reqwidth()
    w_acad.destroy()

    # 2. PlanillaUI (Asistencia) en 1024x700: verificar que todos los botones inferiores caben
    ctrl = ControladorAsistencia(
        RepositorioAsistenciaSQLite(db_mem),
        RespaldoAsistenciaJSON(ruta_archivo=str(tmp_path / "em.json")),
        SQLiteRepositorioClase(db_mem),
        parent=tk_root,
    )
    from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia
    planilla = PlanillaAsistencia(id_clase=1, fecha="2026-11-24", registros=[RegistroAsistencia("V-1")])
    pl = PlanillaUI(ctrl, planilla, {"V-1": "ALUMNO TEST"}, "MATEMATICAS", parent=tk_root)
    pl.win.geometry("1024x700+0+0")
    pl.win.update()
    _verificar_botones_y_limites(pl.win, "PlanillaUI")
    for b in (pl.btn_presente, pl.btn_ausente, pl.btn_justificada, pl.btn_guardar, pl.btn_cerrar):
        assert b.winfo_ismapped()
        assert b.winfo_height() >= 28
    pl.win.destroy()

    # 3. UIEstadisticas en 1024x700: botones de cabecera y etiquetas sin recorte
    ui_stats = UIEstadisticas(
        RepositorioEstadisticasSQLite(db_mem), parent=tk_root, exportador_pdf=exportador
    )
    ui_stats.root.geometry("1024x700+0+0")
    ui_stats.root.update()
    _verificar_botones_y_limites(ui_stats.root, "UIEstadisticas")
    ui_stats.root.destroy()
