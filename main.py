import tkinter as tk
from tkinter import ttk

from db_conexion import ConexionBD
from adaptadores.db.sqlite_profesor import SQLiteRepositorioProfesor
from adaptadores.db.sqlite_clase import SQLiteRepositorioClase
from adaptadores.db.sqlite_usuario import SQLiteRepositorioUsuario # NUEVO

from adaptadores.ui.ui_profesor import GestorProfesoresUI
from adaptadores.ui.ui_clase import GestorClasesUI
from adaptadores.ui.ui_usuario import GestorUsuariosUI

# --- IMPORTS PARA ESTUDIANTES ---
from adaptadores.db.sqlite_estudiante import RepositorioEstudianteSQLite
from adaptadores.ui.ui_estudiante import UIEstudiante

def abrir_panel_seguridad(root_principal, repositorio_usuario):
    """Intenta abrir la ventana de seguridad."""
    GestorUsuariosUI(root_principal, repositorio_usuario)

def iniciar_aplicacion():
    def iniciar_aplicacion():
    # 1. Base de datos y Repositorios
        conexion = ConexionBD()
        repositorio_prof = SQLiteRepositorioProfesor(conexion)
        repositorio_clase = SQLiteRepositorioClase(conexion)
        repositorio_user = SQLiteRepositorioUsuario(conexion) 
    
    # --- NUEVO: Repositorio de Estudiantes ---
        repositorio_estudiante = RepositorioEstudianteSQLite(conexion)

    # 2. Ventana Principal
        root = tk.Tk()
        root.title("Sistema Escolar - Principal")
        root.geometry("800x600")
    
    # Botón de Administración General arriba
        tk.Button(root, text="⚙️ Abrir Panel de Seguridad (Usuarios)", bg="#2c3e50", fg="white", font=("Arial", 10, "bold"),
              command=lambda: abrir_panel_seguridad(root, repositorio_user)).pack(pady=5, fill="x", padx=20)

    # --- NUEVO: Botón para el Panel de Estudiantes ---
        tk.Button(root, text="🎓 Abrir Oficina de Inscripciones (Estudiantes)", bg="#2980b9", fg="white", font=("Arial", 12, "bold"),
              command=lambda: UIEstudiante(repositorio_estudiante)).pack(pady=10, fill="x", padx=20)

    

    # 3. Cuaderno de pestañas Académicas
        notebook = ttk.Notebook(root)
        notebook.pack(pady=10, fill="both", expand=True)

    # 4. Inyección de las otras UI
        GestorProfesoresUI(notebook, repositorio_prof)
        GestorClasesUI(notebook, repositorio_clase)

        root.mainloop()

if __name__ == "__main__":
    iniciar_aplicacion()