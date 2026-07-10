import tkinter as tk
from tkinter import ttk

from db_conexion import ConexionBD
from adaptadores.db.sqlite_profesor import SQLiteRepositorioProfesor
from adaptadores.db.sqlite_clase import SQLiteRepositorioClase
from adaptadores.db.sqlite_usuario import SQLiteRepositorioUsuario 
from adaptadores.db.sqlite_estudiante import RepositorioEstudianteSQLite

# ============================================
# NUEVO: Importaciones del Módulo de Asistencia
# ============================================
from adaptadores.db.sqlite_asistencia import RepositorioAsistenciaSQLite
from adaptadores.respaldo.json_asistencia import RespaldoAsistenciaJSON
from adaptadores.ui.ui_asistencia import GestorAsistenciaUI

from adaptadores.ui.ui_profesor import GestorProfesoresUI
from adaptadores.ui.ui_clase import GestorClasesUI
from adaptadores.ui.ui_usuario import GestorUsuariosUI
from adaptadores.ui.ui_estudiante import UIEstudiante

def abrir_panel_seguridad(root_principal, repositorio_usuario):
    """Intenta abrir la ventana de seguridad."""
    GestorUsuariosUI(root_principal, repositorio_usuario)

# ============================================
# NUEVO: Función para orquestar la Asistencia
# ============================================
def abrir_modulo_asistencia(conexion):
    """
    Inyecta las dependencias necesarias al ControladorAsistencia 
    a través del punto de entrada simplificado GestorAsistenciaUI.
    """
    repo_asistencia = RepositorioAsistenciaSQLite(conexion)
    respaldo_emergencia = RespaldoAsistenciaJSON() # Por defecto usa 'memoria_emergencia.json'
    
    # Instanciamos la UI pasándole lo requerido. Internamente, 
    # tu GestorAsistenciaUI creará el ControladorAsistencia, el Servicio y el Constructor.
    ui_asistencia = GestorAsistenciaUI(repo_asistencia, respaldo_emergencia, conexion)
    ui_asistencia.mostrar()

def iniciar_aplicacion():
    # 1. Base de datos y Repositorios
    conexion = ConexionBD()
    repositorio_prof = SQLiteRepositorioProfesor(conexion)
    repositorio_clase = SQLiteRepositorioClase(conexion)
    repositorio_user = SQLiteRepositorioUsuario(conexion) 
    repositorio_estudiante = RepositorioEstudianteSQLite(conexion)

    # 2. Ventana Principal
    root = tk.Tk()
    root.title("Sistema Escolar - Principal")
    root.geometry("800x600")
    
    # Botón de Administración General arriba
    tk.Button(root, text="⚙️ Abrir Panel de Seguridad (Usuarios)", bg="#2c3e50", fg="white", font=("Arial", 10, "bold"),
              command=lambda: abrir_panel_seguridad(root, repositorio_user)).pack(pady=5, fill="x", padx=20)

    # Botón para el Panel de Estudiantes
    tk.Button(root, text="🎓 Abrir Oficina de Inscripciones (Estudiantes)", bg="#2980b9", fg="white", font=("Arial", 12, "bold"),
              command=lambda: UIEstudiante(repositorio_estudiante)).pack(pady=10, fill="x", padx=20)

    # ============================================
    # NUEVO: Botón para el Módulo de Asistencia
    # ============================================
    tk.Button(root, text="📋 Pasar Lista de Asistencia (Núcleo)", bg="#27ae60", fg="white", font=("Arial", 12, "bold"),
              command=lambda: abrir_modulo_asistencia(conexion)).pack(pady=10, fill="x", padx=20)

    # 3. Cuaderno de pestañas Académicas (Profesores y Clases)
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=20, pady=10)
    
    # Pestaña Profesores
    
    GestorProfesoresUI(notebook, repositorio_prof)
    
    # Pestaña Clases
    
    GestorClasesUI(notebook, repositorio_clase)

    root.mainloop()

if __name__ == "__main__":
    iniciar_aplicacion()