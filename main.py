import tkinter as tk
from tkinter import ttk

# Importamos la Infraestructura (Conexión y Adaptadores de Base de Datos)
from db_conexion import ConexionBD
from adaptadores.db.sqlite_profesor import SQLiteRepositorioProfesor
from adaptadores.db.sqlite_clase import SQLiteRepositorioClase # NUEVO

# Importamos la Interfaz Visual (Adaptadores de UI)
from adaptadores.ui.ui_profesor import GestorProfesoresUI
from adaptadores.ui.ui_clase import GestorClasesUI # NUEVO

def iniciar_aplicacion():
    # 1. PREPARAMOS LA BASE DE DATOS
    conexion = ConexionBD()
    repositorio_profesor = SQLiteRepositorioProfesor(conexion)
    repositorio_clase = SQLiteRepositorioClase(conexion) # NUEVO

    # 2. PREPARAMOS LA VENTANA PRINCIPAL
    root = tk.Tk()
    root.title("Gestión Académica Integral (SOLID)")
    root.geometry("800x600")
    
    # Creamos el cuaderno de pestañas
    notebook = ttk.Notebook(root)
    notebook.pack(pady=10, fill="both", expand=True)

    # 3. CONECTAMOS TODO (Inyección de Dependencias)
    ui_profesores = GestorProfesoresUI(notebook, repositorio_profesor)
    ui_clases = GestorClasesUI(notebook, repositorio_clase) # NUEVO

    root.mainloop()

if __name__ == "__main__":
    iniciar_aplicacion()