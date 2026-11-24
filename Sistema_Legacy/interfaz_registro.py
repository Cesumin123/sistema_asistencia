import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from db_conexion import ConexionBD
from tkcalendar import DateEntry 
from datetime import datetime
import string

# --- CLASE DE AYUDA VISUAL ---
class AyudaVisual:
    """
    Esta clase crea pequeños carteles amarillos (Tooltips)
    que aparecen cuando pasas el mouse por encima de una caja.
    Sirven para guiar al usuario.
    """
    def __init__(self, widget, texto):
        self.widget = widget
        self.texto = texto
        self.ventana_ayuda = None
        # Cuando el mouse entra -> Mostrar cartel
        self.widget.bind("<Enter>", self.mostrar_cartel)
        # Cuando el mouse sale -> Ocultar cartel
        self.widget.bind("<Leave>", self.ocultar_cartel)

    def mostrar_cartel(self, event=None):
        # Calculamos dónde poner el cartelito cerca del mouse
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Creamos una ventanita sin bordes
        self.ventana_ayuda = tk.Toplevel(self.widget)
        self.ventana_ayuda.wm_overrideredirect(True) 
        self.ventana_ayuda.wm_geometry(f"+{x}+{y}")
        
        # Ponemos el texto con fondo amarillo clarito
        etiqueta = tk.Label(self.ventana_ayuda, text=self.texto, background="#ffffe0", 
                         relief="solid", borderwidth=1, font=("Arial", 8))
        etiqueta.pack()

    def ocultar_cartel(self, event=None):
        # Si el cartel existe, lo destruimos
        if self.ventana_ayuda:
            self.ventana_ayuda.destroy()
            self.ventana_ayuda = None

# --- CLASE PRINCIPAL DEL GESTOR ---
class GestorEstudiantes:
    """
    Esta es la OFICINA DE INSCRIPCIONES.
    Aquí registramos, modificamos o borramos a los alumnos del colegio.
    """
    def __init__(self):
        # Creamos la ventana principal de esta oficina
        self.root = tk.Toplevel()
        self.root.title("Gestión Profesional de Estudiantes")
        self.root.geometry("1150x780")
        self.root.state('zoomed') # Abrir en pantalla completa 
        
        # Esta variable es como una 'Memoria Temporal'.
        # Sirve para recordar qué alumno estamos editando.
        self.cedula_seleccionada = None 
        
        # 1. Dibujamos los campos y botones
        self.crear_interfaz()
        # 2. Llenamos la tabla con los datos de la base de datos
        self.cargar_datos()

    def crear_interfaz(self):
        """
        Esta función dibuja todo lo que ves en pantalla:
        Las cajas de texto, los botones y la tabla.
        """
        frame_form = tk.Frame(self.root, pady=10, padx=10, bg="#f0f0f0", relief="groove", bd=2)
        frame_form.pack(fill="x", padx=10, pady=10)
        
        tk.Label(frame_form, text="FICHA TÉCNICA DEL ESTUDIANTE", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=5)
        
        # Variables para las listas desplegables
        self.var_nac = tk.StringVar(value="V")
        self.var_genero = tk.StringVar(value="M")
        self.var_seccion = tk.StringVar(value="A")
        # Variables Nuevas (Agregadas según lo pedido)
        self.var_escolaridad = tk.StringVar(value="Regular")
        self.var_turno = tk.StringVar(value="Mañana")
        self.var_condicion = tk.StringVar(value="Activo")
        
        # --- FILA 1: Identificación (Quién es el alumno) ---
        f1 = tk.Frame(frame_form, bg="#f0f0f0"); f1.pack(pady=5)
        
        # Campo Cédula
        tk.Label(f1, text="Cédula:", bg="#f0f0f0").pack(side="left")
        self.combo_nac = ttk.Combobox(f1, textvariable=self.var_nac, values=["V", "E", "P"], width=3, state="readonly")
        self.combo_nac.pack(side="left")
        self.entry_cedula = tk.Entry(f1, width=15)
        self.entry_cedula.pack(side="left", padx=(5, 20))
        # Agregamos la ayuda visual
        AyudaVisual(self.entry_cedula, "Escribe el número de cédula sin puntos.")

        # Campo Nombre
        tk.Label(f1, text="Nombre Completo:", bg="#f0f0f0").pack(side="left")
        self.entry_nombre = tk.Entry(f1, width=35)
        self.entry_nombre.pack(side="left", padx=(5, 20))
        self.entry_nombre.bind("<KeyRelease>", self.convertir_mayus) 
        AyudaVisual(self.entry_nombre, "Nombre y Apellido del estudiante.")
        
        # Campo Género
        tk.Label(f1, text="Género:", bg="#f0f0f0").pack(side="left")
        self.combo_genero = ttk.Combobox(f1, textvariable=self.var_genero, values=["M", "F"], width=4, state="readonly")
        self.combo_genero.pack(side="left")
        AyudaVisual(self.combo_genero, "Selecciona M (Masculino) o F (Femenino).")

        # --- FILA 2: Datos Básicos ---
        f2 = tk.Frame(frame_form, bg="#f0f0f0"); f2.pack(pady=5)
        
        # Fecha Nacimiento
        tk.Label(f2, text="Fecha Nacimiento:", bg="#f0f0f0").pack(side="left")
        self.calendario = DateEntry(f2, width=12, date_pattern='dd/mm/y', locale='es_ES', background='darkblue')
        self.calendario.pack(side="left", padx=(5, 20))
        AyudaVisual(self.calendario, "Haz clic para elegir el cumpleaños.")
        
        # Grado
        tk.Label(f2, text="Año Escolar (1-5):", bg="#f0f0f0").pack(side="left")
        self.entry_grado = tk.Entry(f2, width=5)
        self.entry_grado.pack(side="left", padx=(5, 20))
        AyudaVisual(self.entry_grado, "Escribe solo el número del año (Ej: 1).")
        
        # Sección
        tk.Label(f2, text="Sección:", bg="#f0f0f0").pack(side="left")
        self.combo_seccion = ttk.Combobox(f2, textvariable=self.var_seccion, values=list(string.ascii_uppercase), width=4, state="readonly")
        self.combo_seccion.pack(side="left")
        AyudaVisual(self.combo_seccion, "La letra de la sección.")

        # --- FILA 3: Contacto (Padres) ---
        f3 = tk.Frame(frame_form, bg="#f0f0f0"); f3.pack(pady=5)
        
        tk.Label(f3, text="Representante:", bg="#f0f0f0", fg="#2980b9").pack(side="left")
        self.entry_repre = tk.Entry(f3, width=35)
        self.entry_repre.pack(side="left", padx=(5, 20))
        self.entry_repre.bind("<KeyRelease>", self.convertir_mayus)
        AyudaVisual(self.entry_repre, "Nombre de mamá, papá o tutor.")
        
        tk.Label(f3, text="Teléfono:", bg="#f0f0f0", fg="#2980b9").pack(side="left")
        self.entry_telf = tk.Entry(f3, width=15)
        self.entry_telf.pack(side="left")
        AyudaVisual(self.entry_telf, "Número para llamar en emergencias.")

        # --- FILA 4: DATOS ADMINISTRATIVOS (Los nuevos campos) ---
        f4 = tk.Frame(frame_form, bg="#e8f8f5", pady=5, padx=5, relief="flat") 
        f4.pack(pady=10)
        
        # Escolaridad (Regular, Repite...)
        tk.Label(f4, text="Escolaridad:", bg="#e8f8f5").pack(side="left")
        self.combo_escolaridad = ttk.Combobox(f4, textvariable=self.var_escolaridad, 
                                            values=["Regular", "Materia Pendiente", "Repite"], 
                                            width=15, state="readonly")
        self.combo_escolaridad.pack(side="left", padx=(2, 20))
        AyudaVisual(self.combo_escolaridad, "¿Pasó todo, debe materias o repite año?")

        # Turno (Mañana/Tarde)
        tk.Label(f4, text="Turno:", bg="#e8f8f5").pack(side="left")
        self.combo_turno = ttk.Combobox(f4, textvariable=self.var_turno, 
                                      values=["Mañana", "Tarde"], 
                                      width=10, state="readonly")
        self.combo_turno.pack(side="left", padx=(2, 20))
        AyudaVisual(self.combo_turno, "¿En qué horario estudia?")

        # Condición (Activo/Preinscrito)
        tk.Label(f4, text="Condición:", bg="#e8f8f5").pack(side="left")
        self.combo_condicion = ttk.Combobox(f4, textvariable=self.var_condicion, 
                                          values=["Activo", "Preinscrito"], 
                                          width=12, state="readonly")
        self.combo_condicion.pack(side="left", padx=(2, 20))
        AyudaVisual(self.combo_condicion, "¿Ya es alumno oficial o está en proceso?")

        # --- BOTONERA (Los controles) ---
        f_btns = tk.Frame(self.root); f_btns.pack(pady=10)
        
        tk.Button(f_btns, text="💾 GUARDAR", bg="#27ae60", fg="white", font=("bold"), 
                  command=self.guardar_nuevo).pack(side="left", padx=10)
        
        tk.Button(f_btns, text="📝 MODIFICAR", bg="#f39c12", fg="white", font=("bold"), 
                  command=self.modificar_existente).pack(side="left", padx=10)
        
        tk.Button(f_btns, text="🗑️ ELIMINAR", bg="#c0392b", fg="white", font=("bold"), 
                  command=self.eliminar_estudiante).pack(side="left", padx=10)
        
        tk.Button(f_btns, text="🧹 Limpiar", command=self.limpiar_formulario).pack(side="left", padx=10)

        # --- TABLA DE DATOS (Donde se ve la lista) ---
        cols = ("cedula", "nombre", "nac", "repre", "telf", "gen", "esc", "tur", "cond", "anio", "sec")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        
        headers = ["Cédula", "Nombre", "F. Nac", "Representante", "Telf", "Sx", "Escolaridad", "Turno", "Cond", "Año", "Sec"]
        widths = [90, 200, 80, 150, 90, 30, 90, 60, 60, 40, 40]
        
        for i, col in enumerate(cols):
            self.tree.heading(col, text=headers[i])
            self.tree.column(col, width=widths[i])
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.cargar_formulario_desde_tabla)

    # ---------------- HERRAMIENTAS ÚTILES ----------------
    def convertir_mayus(self, event):
        """Si escribes en minúsculas, esta función lo cambia a MAYÚSCULAS."""
        widget = event.widget
        texto = widget.get()
        if texto != texto.upper():
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, texto.upper())
            widget.index(pos)

    def limpiar_formulario(self):
        """Esta función borra todo lo que escribiste en las cajas (Borrador)."""
        self.cedula_seleccionada = None
        self.entry_cedula.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        self.entry_repre.delete(0, tk.END)
        self.entry_telf.delete(0, tk.END)
        self.entry_grado.delete(0, tk.END)
        self.combo_nac.current(0)
        self.combo_genero.current(0)
        self.combo_seccion.current(0)
        
        # Reseteamos los nuevos campos a su valor por defecto
        self.combo_escolaridad.current(0) # Regular
        self.combo_turno.current(0)       # Mañana
        self.combo_condicion.current(0)   # Activo
        
        self.calendario.set_date(datetime.now())
        self.entry_cedula.focus()

    def obtener_datos_formulario(self):
        """
        Recoge lo que escribiste, lo mete en una bolsa (Diccionario)
        y revisa si no se te olvidó nada importante.
        """
        nac = self.combo_nac.get()
        num = self.entry_cedula.get().strip()
        nombre = self.entry_nombre.get().strip()
        grado = self.entry_grado.get().strip()
        
        if not num or not nombre or not grado:
            messagebox.showwarning("Faltan Datos", "¡Oye! La Cédula, Nombre y Año son obligatorios.")
            return None
            
        return {
            'cedula_full': f"{nac}-{num}",
            'nombre': nombre,
            'nacimiento': self.calendario.get_date(),
            'repre': self.entry_repre.get().strip(),
            'telf': self.entry_telf.get().strip(),
            'genero': self.combo_genero.get(),
            'escolaridad': self.combo_escolaridad.get(), # Dato Nuevo
            'turno': self.combo_turno.get(),             # Dato Nuevo
            'condicion': self.combo_condicion.get(),     # Dato Nuevo
            'grado': grado,
            'seccion_letra': self.combo_seccion.get()
        }

    def cargar_datos(self):
        """Va al archivo de base de datos, trae la lista de alumnos y la pone en pantalla."""
        for item in self.tree.get_children(): self.tree.delete(item)
            
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # Pedimos todos los datos, incluyendo los nuevos
                sql = """SELECT E.ID_ESTUDIANTE, E.NOMBRE, E.FECHA_NACIMIENTO, 
                                E.REPRESENTANTE, E.TELEFONO, E.GENERO, 
                                E.ESCOLARIDAD, E.TURNO, E.CONDICION,
                                E.ID_GRADO, S.DESCRIPCION 
                         FROM TBL_ESTUDIANTES E
                         JOIN TBL_SECCIONES S ON E.ID_SECCION = S.ID_SECCION
                         ORDER BY E.NOMBRE ASC"""
                cursor.execute(sql)
                for fila in cursor.fetchall():
                    self.tree.insert("", "end", values=fila)
            finally: db.cerrar()

    def cargar_formulario_desde_tabla(self, event):
        """Si haces clic en un alumno de la lista, rellena las cajas de arriba."""
        seleccion = self.tree.selection()
        if not seleccion: return
        
        valores = self.tree.item(seleccion[0])['values']
        self.limpiar_formulario()
        
        self.cedula_seleccionada = str(valores[0]) 
        
        if '-' in self.cedula_seleccionada:
            p = self.cedula_seleccionada.split('-')
            self.combo_nac.set(p[0])
            self.entry_cedula.insert(0, p[1])
        else:
            self.entry_cedula.insert(0, self.cedula_seleccionada)

        self.entry_nombre.insert(0, valores[1])
        if valores[2]: self.calendario.set_date(valores[2])
            
        self.entry_repre.insert(0, valores[3] or "")
        self.entry_telf.insert(0, valores[4] or "")
        self.combo_genero.set(valores[5])
        
        # Cargamos los datos nuevos
        self.combo_escolaridad.set(valores[6] or "Regular")
        self.combo_turno.set(valores[7] or "Mañana")
        self.combo_condicion.set(valores[8] or "Activo")
        
        self.entry_grado.insert(0, str(valores[9]))
        self.combo_seccion.set(valores[10])

    # ---------------- FUNCIONES DE GUARDADO (EL CEREBRO) ----------------

    def guardar_nuevo(self):
        """Crea un alumno nuevo en el sistema."""
        datos = self.obtener_datos_formulario()
        if not datos: return

        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # Buscamos qué ID tiene la letra de la sección (A=1, B=2...)
                cursor.execute("SELECT ID_SECCION FROM TBL_SECCIONES WHERE DESCRIPCION=?", (datos['seccion_letra'],))
                res = cursor.fetchone()
                if not res: return
                sec_id = res[0]
                
                # Preparamos la orden para guardar
                sql = """INSERT INTO TBL_ESTUDIANTES 
                         (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO, 
                          ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                
                valores = (datos['cedula_full'], datos['nombre'], datos['nacimiento'], datos['repre'], 
                           datos['telf'], datos['genero'], 
                           datos['escolaridad'], datos['turno'], datos['condicion'], 
                           datos['grado'], sec_id)
                
                cursor.execute(sql, valores)
                conn.commit() # ¡Guardado confirmado!
                messagebox.showinfo("Éxito", "Estudiante registrado correctamente.")
                self.limpiar_formulario()
                self.cargar_datos()
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Ya existe un alumno con esa cédula.")
            except Exception as err:
                messagebox.showerror("Error BD", str(err))
            finally: db.cerrar()

    def modificar_existente(self):
        """Corrige los datos de un alumno que ya existe."""
        if not self.cedula_seleccionada:
            messagebox.showwarning("Ojo", "Primero toca un estudiante en la lista de abajo.")
            return

        datos = self.obtener_datos_formulario()
        if not datos: return

        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT ID_SECCION FROM TBL_SECCIONES WHERE DESCRIPCION=?", (datos['seccion_letra'],))
                sec_id = cursor.fetchone()[0]
                
                # Actualizamos todo
                sql = """UPDATE TBL_ESTUDIANTES SET 
                         ID_ESTUDIANTE=?, NOMBRE=?, FECHA_NACIMIENTO=?, REPRESENTANTE=?, 
                         TELEFONO=?, GENERO=?, ESCOLARIDAD=?, TURNO=?, CONDICION=?, 
                         ID_GRADO=?, ID_SECCION=? 
                         WHERE ID_ESTUDIANTE=?"""
                         
                valores = (datos['cedula_full'], datos['nombre'], datos['nacimiento'], datos['repre'], 
                           datos['telf'], datos['genero'], 
                           datos['escolaridad'], datos['turno'], datos['condicion'],
                           datos['grado'], sec_id, 
                           self.cedula_seleccionada) 
                
                cursor.execute(sql, valores)
                conn.commit()
                messagebox.showinfo("Éxito", "Datos actualizados.")
                self.limpiar_formulario()
                self.cargar_datos()
            except Exception as err:
                messagebox.showerror("Error BD", str(err))
            finally: db.cerrar()

    def eliminar_estudiante(self):
        """Borra al alumno para siempre (y sus notas/asistencias)."""
        if not self.cedula_seleccionada:
            messagebox.showwarning("Ojo", "Selecciona un estudiante para borrar.")
            return
        
        confirm = messagebox.askyesno("Confirmar", f"¿Seguro que quieres borrar a {self.cedula_seleccionada}?")
        if not confirm: return

        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM TBL_ESTUDIANTES WHERE ID_ESTUDIANTE=?", (self.cedula_seleccionada,))
                conn.commit()
                messagebox.showinfo("Listo", "Estudiante borrado.")
                self.limpiar_formulario()
                self.cargar_datos()
            except Exception as err:
                messagebox.showerror("Error BD", str(err))
            finally: db.cerrar()

if __name__ == "__main__":
    GestorEstudiantes()
