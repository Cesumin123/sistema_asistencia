# main.py
"""
Punto de Entrada Oficial (Composition Root) - Sistema de Asistencia Estudiantil.
Complejo Educativo 'Colinas del Llano' (Barinas, Venezuela).

Ensambla y orquesta la arquitectura hexagonal:
1. Inicializa la conexión SQLite y todos los repositorios.
2. Abre la ventana de Autenticación (Login).
3. Tras la autenticación exitosa, presenta el Menú Principal (Dashboard) con RBAC.
4. Soporta cierre de sesión limpio regresando al Login.
"""

import tkinter as tk
from tkinter import ttk

from db_conexion import ConexionBD
from rutas_app import obtener_ruta_dato

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

# Adaptadores de Interfaz de Usuario (UI)
from adaptadores.ui.utilidades_ui import (
    aplicar_tema_global, maximizar_ventana,
    configurar_ventana_hija, agregar_barra_superior_volver,
)
from adaptadores.ui.ui_login import VentanaLogin
from adaptadores.ui.ui_menu_principal import MenuPrincipalUI
from adaptadores.ui.ui_usuario import GestorUsuariosUI
from adaptadores.ui.ui_estudiante import UIEstudiante
from adaptadores.ui.ui_profesor import GestorProfesoresUI
from adaptadores.ui.ui_clase import GestorClasesUI
from adaptadores.ui.ui_asistencia import GestorAsistenciaUI
from adaptadores.ui.ui_listados import UIListados
from adaptadores.ui.ui_reportes import UIReportes
from adaptadores.ui.ui_estadisticas import UIEstadisticas
from adaptadores.ui.ui_promocion import UIPromocion

# Dominio y Permisos
from dominio.permisos import (
    MODULO_ESTUDIANTES,
    MODULO_ACADEMICO,
    MODULO_ASISTENCIA,
    MODULO_LISTADOS,
    MODULO_REPORTES,
    MODULO_ESTADISTICAS,
    MODULO_PROMOCION,
    MODULO_USUARIOS,
)


def iniciar_aplicacion():
    """Inicializa la infraestructura y arranca el ciclo de vida del sistema."""
    # 1. Base de datos (inicializa/migra esquema junto al ejecutable desde el arranque)
    conexion = ConexionBD()
    if conexion.conectar() is not None:
        conexion.cerrar()

    # 2. Inicialización de Repositorios (Puertos y Adaptadores)
    repo_usuario = SQLiteRepositorioUsuario(conexion)
    repo_estudiante = RepositorioEstudianteSQLite(conexion)
    repo_profesor = SQLiteRepositorioProfesor(conexion)
    repo_clase = SQLiteRepositorioClase(conexion)
    repo_asistencia = RepositorioAsistenciaSQLite(conexion)
    respaldo_asistencia = RespaldoAsistenciaJSON(obtener_ruta_dato("memoria_emergencia.json"))
    repo_reportes = RepositorioReportesSQLite(conexion)
    repo_estadisticas = RepositorioEstadisticasSQLite(conexion)
    repo_promocion = RepositorioPromocionSQLite(conexion)
    repo_listados = RepositorioListadosSQLite(conexion)
    exportador_pdf = ExportadorPDFReportLab()
    gestor_fotos = GestorFotos()

    # 3. Callbacks para la apertura de módulos
    menu_actual = [None]

    def _obtener_padre():
        if menu_actual[0] and hasattr(menu_actual[0], "root") and menu_actual[0].root.winfo_exists():
            return menu_actual[0].root
        return None

    def abrir_academico():
        padre = _obtener_padre()
        win = tk.Toplevel(padre)
        win.title("Gestión Académica - Profesores y Clases")
        win.geometry("900x600")
        configurar_ventana_hija(win, padre)
        agregar_barra_superior_volver(win, padre, "Módulo Académico")
        maximizar_ventana(win)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        GestorProfesoresUI(
            nb, repo_profesor,
            exportador_pdf=exportador_pdf,
            gestor_fotos=gestor_fotos,
            repositorio_clase=repo_clase
        )
        GestorClasesUI(nb, repo_clase)

    def abrir_estudiantes():
        padre = _obtener_padre()
        ui = UIEstudiante(
            repo_estudiante,
            parent=padre,
            exportador_pdf=exportador_pdf,
            gestor_fotos=gestor_fotos,
            repositorio_reportes=repo_reportes
        )
        configurar_ventana_hija(ui.root, padre)
        agregar_barra_superior_volver(ui.root, padre, "Módulo de Estudiantes")
        maximizar_ventana(ui.root)

    def abrir_asistencia():
        padre = _obtener_padre()
        ui_asist = GestorAsistenciaUI(repo_asistencia, respaldo_asistencia, repo_clase, parent=padre)
        ui_asist.mostrar(parent=padre)

    def abrir_listados():
        padre = _obtener_padre()
        ui = UIListados(repo_listados, exportador_pdf, parent=padre)
        configurar_ventana_hija(ui.root, padre)
        agregar_barra_superior_volver(ui.root, padre, "Módulo de Listados")
        maximizar_ventana(ui.root)

    def abrir_reportes():
        padre = _obtener_padre()
        ui = UIReportes(repo_reportes, exportador_pdf, parent=padre)
        configurar_ventana_hija(ui.root, padre)
        agregar_barra_superior_volver(ui.root, padre, "Módulo de Reportes")
        maximizar_ventana(ui.root)

    def abrir_estadisticas():
        padre = _obtener_padre()
        ui = UIEstadisticas(repo_estadisticas, parent=padre, exportador_pdf=exportador_pdf)
        configurar_ventana_hija(ui.root, padre)
        maximizar_ventana(ui.root)

    def abrir_promocion():
        padre = _obtener_padre()
        ui = UIPromocion(repo_promocion, parent=padre)
        configurar_ventana_hija(ui.root, padre)
        agregar_barra_superior_volver(ui.root, padre, "Módulo de Promoción")
        maximizar_ventana(ui.root)

    def abrir_usuarios():
        padre = _obtener_padre()
        ui = GestorUsuariosUI(padre, repo_usuario)
        if hasattr(ui, "root") and ui.root and ui.root.winfo_exists():
            configurar_ventana_hija(ui.root, padre)
            agregar_barra_superior_volver(ui.root, padre, "Módulo de Usuarios")
            maximizar_ventana(ui.root)

    callbacks_modulos = {
        MODULO_ACADEMICO: abrir_academico,
        MODULO_ESTUDIANTES: abrir_estudiantes,
        MODULO_ASISTENCIA: abrir_asistencia,
        MODULO_LISTADOS: abrir_listados,
        MODULO_REPORTES: abrir_reportes,
        MODULO_ESTADISTICAS: abrir_estadisticas,
        MODULO_PROMOCION: abrir_promocion,
        MODULO_USUARIOS: abrir_usuarios,
    }

    # 4. Orquestación del Flujo Login <-> Menú Principal
    def mostrar_menu_principal(usuario_autenticado):
        menu = MenuPrincipalUI(
            usuario=usuario_autenticado,
            callbacks=callbacks_modulos,
            on_logout=mostrar_login
        )
        menu_actual[0] = menu
        menu.root.mainloop()

    def mostrar_login():
        login = VentanaLogin(
            repositorio_usuario=repo_usuario,
            on_login_exitoso=mostrar_menu_principal
        )
        login.root.mainloop()

    # Iniciar con la ventana de Login
    mostrar_login()


if __name__ == "__main__":
    iniciar_aplicacion()
