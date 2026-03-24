import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3 
import string
from db_conexion import ConexionBD

class GestorAcademico:
    """
    Módulo para configurar la Escuela.
    Aquí es donde el Director dice: 
    "El profesor Pedro va a dar Matemáticas en 1er año A, B y C".
    """

    def __init__(self):
        # Creamos la ventana flotante
        self.root = tk.Toplevel()
        self.root.title("Gestión Académica Integral")
        self.root.geometry("650x600")
        # Esta instrucción le dice a la ventana que se expanda al máximo al abrirse
        self.root.state('zoomed')
        
        # Creamos las pestañas (Como en un navegador web)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, fill="both", expand=True)
        
        # Pestaña 1: Profesores
        self.crear_tab_profesores()
        # Pestaña 2: Materias
        self.crear_tab_materias()

    def convertir_mayus(self, event):
        """Truco para que todo lo que escribas se ponga en MAYÚSCULAS solo."""
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            widget.index(pos)

    # =========================================================================
    # PARTE 1: LOS PROFESORES
    # =========================================================================
    
    def crear_tab_profesores(self):
        """Diseña la pantalla para registrar profes."""
        tab = tk.Frame(self.notebook, bg="#e8f8f5")
        self.notebook.add(tab, text="  👨‍🏫  REGISTRAR PROFESOR  ")
        
        frame = tk.Frame(tab, bg="#e8f8f5"); frame.pack(pady=30)
        
        # --- Cédula ---
        tk.Label(frame, text="Cédula de Identidad:", bg="#e8f8f5", font=("Arial", 10)).pack()
        f_ced = tk.Frame(frame, bg="#e8f8f5"); f_ced.pack()
        
        self.combo_nac_prof = ttk.Combobox(f_ced, values=["V", "E", "P"], width=3, state="readonly")
        self.combo_nac_prof.pack(side="left"); self.combo_nac_prof.current(0)
        
        self.entry_ced_prof = tk.Entry(f_ced, width=15)
        self.entry_ced_prof.pack(side="left", padx=5)
        
        # --- Nombre ---
        tk.Label(frame, text="Nombre Completo:", bg="#e8f8f5", font=("Arial", 10)).pack(pady=(15, 0))
        self.entry_nom_prof = tk.Entry(frame, width=35)
        self.entry_nom_prof.pack()
        self.entry_nom_prof.bind("<KeyRelease>", self.convertir_mayus)
        
        # --- Botón Guardar ---
        tk.Button(frame, text="GUARDAR PROFESOR", bg="#16a085", fg="white", font=("Arial", 10, "bold"),
                  command=self.guardar_profesor).pack(pady=25)

    def guardar_profesor(self):
        """Guarda al profe en la base de datos."""
        nombre = self.entry_nom_prof.get().strip().upper()
        ced_num = self.entry_ced_prof.get().strip()
        cedula = f"{self.combo_nac_prof.get()}-{ced_num}"
        
        if not ced_num or not nombre:
            messagebox.showwarning("Faltan datos", "Escribe la cédula y el nombre.")
            return

        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # SQLITE: Usamos '?'
                sql = "INSERT INTO TBL_PROFESORES (NOMBRE_COMPLETO, CEDULA) VALUES (?, ?)"
                cursor.execute(sql, (nombre, cedula))
                conn.commit()
                messagebox.showinfo("Listo", f"Profesor {nombre} registrado.")
                self.root.destroy() # Cerramos para volver al menú
                
            except sqlite3.IntegrityError: 
                messagebox.showerror("Duplicado", "Esa cédula ya existe.")
            except Exception as err:
                messagebox.showerror("Error", str(err))
            finally:
                db.cerrar()

    # =========================================================================
    # PARTE 2: LAS MATERIAS (Aquí está la magia)
    # =========================================================================

    def crear_tab_materias(self):
        """Diseña la pantalla para crear materias masivamente."""
        tab = tk.Frame(self.notebook, bg="#f4ecf7")
        self.notebook.add(tab, text="  📚  CREAR MATERIA  ")
        
        frame = tk.Frame(tab, bg="#f4ecf7"); frame.pack(pady=20)
        
        # --- Nombre Materia ---
        tk.Label(frame, text="Nombre de la Materia (Ej: MATEMÁTICA):", bg="#f4ecf7").pack()
        self.entry_materia = tk.Entry(frame, width=35)
        self.entry_materia.pack()
        self.entry_materia.bind("<KeyRelease>", self.convertir_mayus)
        
        # --- Elegir Profesor ---
        tk.Label(frame, text="Profesor Encargado:", bg="#f4ecf7").pack(pady=(10,0))
        self.combo_profesores = ttk.Combobox(frame, width=40, state="readonly")
        self.combo_profesores.pack()
        self.cargar_lista_profesores() 
        
        # --- Elegir Año ---
        tk.Label(frame, text="Año Escolar (1-5):", bg="#f4ecf7").pack(pady=(10,0))
        self.entry_grado_mat = tk.Entry(frame, width=10, justify="center")
        self.entry_grado_mat.pack()
        
        # --- Elegir Secciones (Multiselección) ---
        tk.Label(frame, text="Seleccione Secciones (Click + Ctrl para varias):", 
                 bg="#f4ecf7", fg="#8e44ad", font=("bold")).pack(pady=(15,5))
        
        f_list = tk.Frame(frame); f_list.pack()
        scroll = tk.Scrollbar(f_list)
        scroll.pack(side="right", fill="y")
        
        # Listbox es una lista donde puedes seleccionar varias cosas a la vez
        self.listbox_secciones = tk.Listbox(f_list, selectmode="multiple", height=5, 
                                            exportselection=False, yscrollcommand=scroll.set)
        # Llenamos con letras A, B, C, D...
        for letra in string.ascii_uppercase: 
            self.listbox_secciones.insert(tk.END, letra)
            
        self.listbox_secciones.pack(side="left")
        scroll.config(command=self.listbox_secciones.yview)
        
        # --- Botón Crear ---
        tk.Button(frame, text="CREAR MATERIAS", bg="#9b59b6", fg="white", font=("Arial", 10, "bold"),
                  command=self.guardar_materia_masiva).pack(pady=20)

    def cargar_lista_profesores(self):
        """Busca a los profes en la BD para ponerlos en la lista desplegable."""
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT ID_PROFESOR, NOMBRE_COMPLETO, CEDULA FROM TBL_PROFESORES ORDER BY NOMBRE_COMPLETO")
                
                # Creamos textos bonitos tipo: "15 - PEDRO PEREZ (V-123)"
                data = [f"{row[0]} - {row[1]} ({row[2]})" for row in cursor.fetchall()]
                self.combo_profesores['values'] = data
                
                # PROTECCIÓN: Si no hay profes, no intentamos seleccionar nada
                if data: 
                    self.combo_profesores.current(0)
                else:
                    self.combo_profesores.set("--- No hay profesores registrados ---")
            finally: 
                db.cerrar()

    def guardar_materia_masiva(self):
        """
        Esta función ahorra trabajo.
        Si eliges "Matemática", "1er Año" y seleccionas las secciones "A", "B" y "C",
        el sistema crea las 3 materias automáticamente (Mate 1-A, Mate 1-B, Mate 1-C).
        """
        materia = self.entry_materia.get().strip().upper()
        prof_txt = self.combo_profesores.get()
        grado = self.entry_grado_mat.get().strip()
        indices = self.listbox_secciones.curselection() # ¿Qué letras seleccionó?
        
        if not materia or not prof_txt or not grado:
            messagebox.showwarning("Faltan Datos", "Debe llenar todos los campos.")
            return
        
        if not indices:
            messagebox.showwarning("Ojo", "Selecciona al menos una sección de la lista.")
            return
            
        try:
            # Sacamos el ID del profesor del texto "15 - PEDRO..."
            id_prof = int(prof_txt.split(" - ")[0])
        except:
            messagebox.showerror("Error", "Profesor inválido.")
            return

        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                count = 0
                
                # Repetimos el proceso por cada sección seleccionada
                for idx in indices:
                    letra = self.listbox_secciones.get(idx)
                    
                    # 1. Buscamos el ID de la letra 'A'
                    cursor.execute("SELECT ID_SECCION FROM TBL_SECCIONES WHERE DESCRIPCION=?", (letra,))
                    res = cursor.fetchone()
                    
                    if res:
                        id_sec = res[0]
                        # 2. Creamos la materia
                        # SQLITE: Usamos '?'
                        sql = """INSERT INTO TBL_CLASES 
                                 (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) 
                                 VALUES (?, ?, ?, ?)"""
                        cursor.execute(sql, (materia, id_prof, grado, id_sec))
                        count += 1
                
                conn.commit()
                messagebox.showinfo("Éxito", f"Se creó la materia '{materia}' para {count} secciones.")
                self.root.destroy()
            except Exception as err:
                messagebox.showerror("Error BD", str(err))
            finally: 
                db.cerrar()

if __name__ == "__main__":
    GestorAcademico()
