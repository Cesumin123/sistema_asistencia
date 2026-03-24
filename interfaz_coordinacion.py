import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from db_conexion import ConexionBD

# El secretario de impresión
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import date

class GestorCoordinacion:
    """
    EL CUARTO DE COORDINACIÓN.
    Aquí vemos la estructura de la escuela desde arriba.
    """
    def __init__(self):
        self.root = tk.Toplevel()
        self.root.title("Coordinación Académica")
        self.root.geometry("1100x700")
        self.root.state('zoomed') # Abrimos en pantalla completa automáticamente
        
        # Creamos las dos mesas de trabajo (Pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.crear_pestaña_profesores()
        self.crear_pestaña_explorador_salones()

    # =========================================================================
    # MESA 1: LA CARGA DE SECCION DE LOS DOCENTES
    # =========================================================================
    def crear_pestaña_profesores(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="👨‍🏫 Carga Seccion Docente")
        
        # Botonera superior
        f_top = tk.Frame(tab, pady=10); f_top.pack()
        tk.Button(f_top, text="🔄 Refrescar Lista", command=self.cargar_tabla_profesores).pack(side="left", padx=10)
        tk.Button(f_top, text="🖨️ Exportar a PDF", bg="#c0392b", fg="white", 
                  command=self.imprimir_pdf_profesores).pack(side="left", padx=10)
        
        # La Pizarra (Tabla)
        columnas = ("Profesor", "Materia", "Año Escolar", "Sección")
        self.tree_prof = ttk.Treeview(tab, columns=columnas, show="headings")
        
        for col in columnas:
            self.tree_prof.heading(col, text=col)
            
        self.tree_prof.column("Profesor", width=300)
        self.tree_prof.column("Materia", width=250)
        self.tree_prof.column("Año Escolar", width=150)
        self.tree_prof.column("Sección", width=100)
        
        self.tree_prof.pack(fill="both", expand=True, padx=20, pady=10)
        self.cargar_tabla_profesores() # Llenamos la pizarra al entrar

    def cargar_tabla_profesores(self):
        """Busca en el archivo central qué materias da cada profesor."""
        for item in self.tree_prof.get_children(): self.tree_prof.delete(item)
            
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # Unimos 4 hojas distintas para armar el reporte completo
                sql = """
                    SELECT P.NOMBRE_COMPLETO, C.NOMBRE_MATERIA, G.DESCRIPCION, S.DESCRIPCION
                    FROM TBL_CLASES C
                    JOIN TBL_PROFESORES P ON C.ID_PROFESOR = P.ID_PROFESOR
                    JOIN TBL_GRADOS G ON C.ID_GRADO = G.ID_GRADO
                    JOIN TBL_SECCIONES S ON C.ID_SECCION = S.ID_SECCION
                    ORDER BY P.NOMBRE_COMPLETO, G.ID_GRADO, S.DESCRIPCION
                """
                cursor.execute(sql)
                for fila in cursor.fetchall():
                    self.tree_prof.insert("", "end", values=fila)
            finally: db.cerrar()

    def imprimir_pdf_profesores(self):
        """El secretario toma la tabla y la pasa a PDF con el logo y el fondo transparente."""
        if not self.tree_prof.get_children(): return
        
        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Carga_Docentes.pdf")
        if not ruta: return

        try:
            c = canvas.Canvas(ruta, pagesize=letter)
            ancho, alto = letter
            
            # Membrete y Logo (Con mask='auto' para el fondo transparente)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(40, alto - 40, "República Bolivariana de Venezuela")
            c.drawString(40, alto - 55, "Ministerio del Poder Popular para la Educación")
            c.drawString(40, alto - 70, "Complejo Educativo 'Colinas del Llano'")
            try:
                c.drawImage("LOGOLICEO.png", ancho - 100, alto - 90, width=60, height=60, mask='auto')
            except: pass
            
            y = alto - 120
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(ancho/2, y, "CARGA SECCION DOCENTE")
            y -= 30
            
            # Títulos de las columnas
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, "Profesor"); c.drawString(250, y, "Materia")
            c.drawString(420, y, "Año"); c.drawString(500, y, "Sección")
            y -= 10; c.line(40, y, 550, y); y -= 20
            
            # Dictado de los datos
            c.setFont("Helvetica", 9)
            for item in self.tree_prof.get_children():
                if y < 50: c.showPage(); y = alto - 50; c.setFont("Helvetica", 9)
                
                valores = self.tree_prof.item(item)['values']
                c.drawString(40, y, str(valores[0])[:35])  # Profesor
                c.drawString(250, y, str(valores[1])[:25]) # Materia
                c.drawString(420, y, str(valores[2]))      # Año
                c.drawString(500, y, str(valores[3]))      # Sección
                y -= 15
                
            c.save()
            messagebox.showinfo("Listo", "PDF guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # =========================================================================
    # MESA 2: EL EXPLORADOR DE SALONES (GAVETAS)
    # =========================================================================
    def crear_pestaña_explorador_salones(self):
        tab = tk.Frame(self.notebook, bg="#f4f6f7")
        self.notebook.add(tab, text="🏫 Explorador de Salones")
        
        # -- SECCIÓN SUPERIOR: Las Gavetas (Filtros) --
        f_filtros = tk.Frame(tab, bg="#e5e8e8", pady=15, relief="ridge", bd=2)
        f_filtros.pack(fill="x", padx=20, pady=10)
        
        tk.Label(f_filtros, text="1. Seleccione el Año:", bg="#e5e8e8", font=("bold")).pack(side="left", padx=10)
        self.combo_grados = ttk.Combobox(f_filtros, state="readonly", width=15)
        self.combo_grados.pack(side="left", padx=5)
        
        tk.Label(f_filtros, text="2. Seleccione la Sección:", bg="#e5e8e8", font=("bold")).pack(side="left", padx=(30, 10))
        self.combo_secciones = ttk.Combobox(f_filtros, state="readonly", width=10)
        self.combo_secciones.pack(side="left", padx=5)
        
        tk.Button(f_filtros, text="🔍 ABRIR SALÓN", bg="#2980b9", fg="white", font=("bold"),
                  command=self.abrir_gaveta_salon).pack(side="left", padx=30)
        
        # Cargamos las opciones de las gavetas
        self.cargar_opciones_comboboxes()

        # -- SECCIÓN INFERIOR: La Información del Salón --
        f_info = tk.Frame(tab, bg="#f4f6f7")
        f_info.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Dividimos la pantalla en dos mitades (Izquierda: Materias, Derecha: Alumnos)
        f_izq = tk.Frame(f_info, bg="#f4f6f7"); f_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))
        f_der = tk.Frame(f_info, bg="#f4f6f7"); f_der.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Tabla de Materias
        tk.Label(f_izq, text="📚 Materias y Profesores Asignados", bg="#f4f6f7", font=("Arial", 11, "bold")).pack(pady=5)
        self.tree_clases = ttk.Treeview(f_izq, columns=("Materia", "Profesor"), show="headings")
        self.tree_clases.heading("Materia", text="Materia"); self.tree_clases.heading("Profesor", text="Profesor")
        self.tree_clases.pack(fill="both", expand=True)

        # Tabla de Alumnos
        tk.Label(f_der, text="🎓 Alumnos Inscritos", bg="#f4f6f7", font=("Arial", 11, "bold")).pack(pady=5)
        self.tree_alumnos = ttk.Treeview(f_der, columns=("Cédula", "Nombre"), show="headings")
        self.tree_alumnos.heading("Cédula", text="Cédula"); self.tree_alumnos.heading("Nombre", text="Nombre del Estudiante")
        self.tree_alumnos.column("Cédula", width=100); self.tree_alumnos.column("Nombre", width=300)
        self.tree_alumnos.pack(fill="both", expand=True)

    def cargar_opciones_comboboxes(self):
        """Busca en el archivo qué Años y qué Secciones existen para mostrarlos en las listas."""
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cur = conn.cursor()
                
                # Buscamos los años (Ej: 1 - 1er AÑO)
                cur.execute("SELECT ID_GRADO, DESCRIPCION FROM TBL_GRADOS")
                self.lista_ids_grados = []
                opciones_grados = []
                for row in cur.fetchall():
                    self.lista_ids_grados.append(row[0])
                    opciones_grados.append(row[1])
                self.combo_grados['values'] = opciones_grados
                if opciones_grados: self.combo_grados.current(0)
                
                # Buscamos las secciones (Ej: 1 - A)
                cur.execute("SELECT ID_SECCION, DESCRIPCION FROM TBL_SECCIONES")
                self.lista_ids_secciones = []
                opciones_secciones = []
                for row in cur.fetchall():
                    self.lista_ids_secciones.append(row[0])
                    opciones_secciones.append(row[1])
                self.combo_secciones['values'] = opciones_secciones
                if opciones_secciones: self.combo_secciones.current(0)
            finally: db.cerrar()

    def abrir_gaveta_salon(self):
        """Al darle click al botón, vaciamos las mesas y traemos los papeles nuevos del salón elegido."""
        idx_grado = self.combo_grados.current()
        idx_seccion = self.combo_secciones.current()
        
        if idx_grado == -1 or idx_seccion == -1: return
        
        id_g = self.lista_ids_grados[idx_grado]
        id_s = self.lista_ids_secciones[idx_seccion]
        
        # Limpiamos las tablas
        for i in self.tree_clases.get_children(): self.tree_clases.delete(i)
        for i in self.tree_alumnos.get_children(): self.tree_alumnos.delete(i)
        
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cur = conn.cursor()
                
                # 1. Buscamos las materias de ese salón
                cur.execute("""
                    SELECT C.NOMBRE_MATERIA, P.NOMBRE_COMPLETO 
                    FROM TBL_CLASES C 
                    JOIN TBL_PROFESORES P ON C.ID_PROFESOR = P.ID_PROFESOR 
                    WHERE C.ID_GRADO = ? AND C.ID_SECCION = ?
                """, (id_g, id_s))
                for row in cur.fetchall(): self.tree_clases.insert("", "end", values=row)
                
                # 2. Buscamos a los alumnos sentados en ese salón
                cur.execute("""
                    SELECT ID_ESTUDIANTE, NOMBRE 
                    FROM TBL_ESTUDIANTES 
                    WHERE ID_GRADO = ? AND ID_SECCION = ? 
                    ORDER BY NOMBRE
                """, (id_g, id_s))
                for row in cur.fetchall(): self.tree_alumnos.insert("", "end", values=row)
                
            finally: db.cerrar()

if __name__ == "__main__":
    GestorCoordinacion()