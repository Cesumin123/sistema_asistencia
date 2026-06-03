# main.py
import tkinter as tk
from tkinter import ttk

# Importamos la conexión a la Base de Datos (Infraestructura)
from db_conexion import ConexionBD
from adaptadores.db.sqlite_profesor import SQLiteRepositorioProfesor

# Importamos nuestra nueva Interfaz refactorizada (UI)
from adaptadores.ui.ui_profesor import GestorProfesoresUI



def iniciar_aplicacion():
    """El Director de Orquesta: Conecta todas las piezas."""
    
    # 1. PREPARAMOS LA INFRAESTRUCTURA (Base de datos)
    conexion = ConexionBD()
    
    # 2. CREAMOS EL ADAPTADOR DE LA BASE DE DATOS
    # Le pasamos la conexión al repositorio
    repositorio_profesor = SQLiteRepositorioProfesor(conexion)

    # 3. PREPARAMOS LA PANTALLA PRINCIPAL (Tkinter)
    root = tk.Tk()
    root.title("Prueba de Arquitectura Hexagonal - Profesores")
    root.geometry("800x600")
    
    # Creamos el cuaderno de pestañas
    notebook = ttk.Notebook(root)
    notebook.pack(pady=10, fill="both", expand=True)

    # 4. CONECTAMOS LA UI CON LA BASE DE DATOS (Inyección de Dependencias)
    # Fíjate que le pasamos el "repositorio_profesor" a la UI. 
    # ¡La UI no sabe que es SQLite, solo sabe que puede guardar cosas!
    ui_profesores = GestorProfesoresUI(notebook, repositorio_profesor)

    # 5. Mostramos la ventana
    root.mainloop()

if __name__ == "__main__":
    iniciar_aplicacion()