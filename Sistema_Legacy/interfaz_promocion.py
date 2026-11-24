import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3 
from db_conexion import ConexionBD

class GestorPromocion:
    """
    Módulo de "Fin de Año Escolar".
    
    ¡CUIDADO! Esta es la herramienta más poderosa.
    Mueve a TODOS los estudiantes al siguiente grado de un solo golpe.
    Ejemplo: Todos los de 1ro pasan a 2do.
    """
    
    # Esta es la contraseña secreta para que solo el Director pueda hacer esto.
    CLAVE_MAESTRA = "DIRECTOR2025" 

    def __init__(self):
        self.root = tk.Toplevel()
        self.root.title("Cierre y Promoción de Año Escolar")
        self.root.geometry("500x450")
        self.root.state('zoomed') # Abrir en pantalla completa
        
        # Ponemos el fondo ROJO para indicar que es una zona de peligro/atención
        self.root.config(bg="#c0392b") 

        tk.Label(self.root, text="ZONA DE ALTO RIESGO", font=("Arial", 22, "bold"), fg="white", bg="#c0392b").pack(pady=20)
        
        info = ("Esta herramienta realiza el CIERRE DEL AÑO ESCOLAR.\n\n"
                "1. Promueve a todos los alumnos al siguiente grado.\n"
                "2. Los de 5to año pasan a 'Graduados' (Grado 6).\n"
                "3. ¡Es irreversible! No se puede deshacer.")
        
        tk.Label(self.root, text=info, font=("Arial", 11), fg="white", bg="#c0392b", justify="center").pack(pady=20)
        
        # Botón con candado
        tk.Button(self.root, text="🔒 EJECUTAR PROMOCIÓN", font=("Arial", 12, "bold"), 
                  bg="white", fg="#c0392b", padx=20, pady=10,
                  command=self.verificar_seguridad).pack(pady=20)

    def verificar_seguridad(self):
        """
        Sistema de doble seguridad:
        1. Pregunta "¿Estás seguro?"
        2. Pide la contraseña maestra.
        """
        # Paso 1: Confirmación simple
        respuesta = messagebox.askyesno("Confirmar", "¿Está realmente seguro de cerrar el año escolar actual?")
        if not respuesta: return

        # Paso 2: Contraseña
        clave = simpledialog.askstring("Seguridad", "Ingrese la CLAVE MAESTRA para autorizar:", show="*")
        
        # Paso 3: Verificar contraseña
        # En Python, 'self.CLAVE_MAESTRA' accede a la variable que definimos arriba
        if clave == self.CLAVE_MAESTRA:
            self.ejecutar_promocion()
        else:
            messagebox.showerror("Acceso Denegado", "Clave incorrecta. No se hicieron cambios.")

    def ejecutar_promocion(self):
        """
        Aquí ocurre la magia del movimiento de estudiantes.
        """
        db = ConexionBD()
        conn = db.conectar()
        
        if conn:
            try:
                cursor = conn.cursor()
                
                # Paso A: Asegurarnos de que exista el grado 6 ("Graduado")
                # SQLITE: Usamos 'INSERT OR IGNORE' (En MySQL era INSERT IGNORE)
                cursor.execute("INSERT OR IGNORE INTO TBL_GRADOS (ID_GRADO, DESCRIPCION) VALUES (6, 'GRADUADO / EGRESADO')")
                
                # Paso B: El Efecto Dominó (Lógica Inversa)
                # IMPORTANTE: Debemos mover primero a los de 5to, luego a los de 4to, etc.
                # Si movemos primero a los de 1ro a 2do... ¡se mezclarían con los de 2do actuales!
                
                # 1. Los de 5to se gradúan (Pasan al grado 6)
                cursor.execute("UPDATE TBL_ESTUDIANTES SET ID_GRADO = 6 WHERE ID_GRADO = 5")
                
                # 2. Los de 4to pasan a 5to
                cursor.execute("UPDATE TBL_ESTUDIANTES SET ID_GRADO = 5 WHERE ID_GRADO = 4")
                
                # 3. Los de 3ro pasan a 4to
                cursor.execute("UPDATE TBL_ESTUDIANTES SET ID_GRADO = 4 WHERE ID_GRADO = 3")
                
                # 4. Los de 2do pasan a 3ro
                cursor.execute("UPDATE TBL_ESTUDIANTES SET ID_GRADO = 3 WHERE ID_GRADO = 2")
                
                # 5. Los de 1ro pasan a 2do
                cursor.execute("UPDATE TBL_ESTUDIANTES SET ID_GRADO = 2 WHERE ID_GRADO = 1")
                
                conn.commit() # Guardamos todos los cambios de golpe
                
                messagebox.showinfo("Proceso Exitoso", "¡Feliz Año Nuevo Escolar!\nTodos los alumnos han sido promovidos.")
                self.root.destroy()
                
            except Exception as e:
                conn.rollback() # Si algo falla, deshacemos todo para que no quede un desastre
                messagebox.showerror("Error Crítico", f"Hubo un error: {str(e)}")
            finally: 
                db.cerrar()

if __name__ == "__main__":
    GestorPromocion()
