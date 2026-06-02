# Este archivo contiene el código para la ventana de coordinación académica.
# La coordinación académica es la parte del sistema que permite ver y organizar la información de profesores, materias y estudiantes por grados y secciones.

# Aquí importamos las bibliotecas que necesitamos para hacer funcionar el programa.
# tkinter es una biblioteca que nos permite crear ventanas y botones en la pantalla.
import tkinter as tk
# De tkinter importamos más cosas específicas: ttk para tablas, messagebox para mostrar mensajes, filedialog para elegir archivos.
from tkinter import ttk, messagebox, filedialog
# sqlite3 es para trabajar con bases de datos, donde guardamos la información.
import sqlite3
# ConexionBD es una clase que hicimos nosotros para conectar con la base de datos.
from db_conexion import ConexionBD

# reportlab es una biblioteca para crear archivos PDF.
# Importamos las partes que necesitamos: pagesizes para el tamaño de la página, canvas para dibujar en el PDF.
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
# datetime es para trabajar con fechas, importamos date para obtener la fecha actual.
from datetime import date

# Esta es la clase principal del módulo. Se llama GestorCoordinacion.
# Una clase es como un plano para crear objetos. Esta clase crea la ventana de coordinación.
class GestorCoordinacion:
    """
    Esta clase maneja la ventana de coordinación académica.
    Aquí podemos ver la información de profesores y salones.
    """
    def __init__(self):
        # Este método se ejecuta cuando creamos un objeto de la clase.
        # Aquí configuramos la ventana principal.
        
        # Creamos una nueva ventana que aparece encima de otras.
        self.root = tk.Toplevel()
        # Ponemos un título a la ventana.
        self.root.title("Coordinación Académica")
        # Establecemos el tamaño inicial de la ventana.
        self.root.geometry("1100x700")
        # Hacemos que la ventana se abra en pantalla completa automáticamente.
        self.root.state('zoomed') # Abrimos en pantalla completa automáticamente
        
        # Creamos un contenedor con pestañas para organizar la información.
        self.notebook = ttk.Notebook(self.root)
        # Ponemos el contenedor en la ventana para que ocupe todo el espacio.
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Llamamos a los métodos para crear las pestañas.
        self.crear_pestaña_profesores()
        self.crear_pestaña_explorador_salones()

    # =========================================================================
    # Esta sección crea la primera pestaña, que muestra la carga de secciones de los docentes.
    # =========================================================================
    def crear_pestaña_profesores(self):
        # Este método crea la pestaña para ver qué materias dan los profesores.
        
        # Creamos un marco (frame) para esta pestaña.
        tab = tk.Frame(self.notebook)
        # Agregamos el marco al contenedor de pestañas con un texto.
        self.notebook.add(tab, text="👨‍🏫 Carga Seccion Docente")
        
        # Creamos un marco para los botones en la parte superior.
        f_top = tk.Frame(tab, pady=10); f_top.pack()
        # Creamos un botón para refrescar la lista de profesores.
        tk.Button(f_top, text="🔄 Refrescar Lista", command=self.cargar_tabla_profesores).pack(side="left", padx=10)
        # Creamos un botón para exportar la información a un archivo PDF.
        tk.Button(f_top, text="🖨️ Exportar a PDF", bg="#c0392b", fg="white", 
                  command=self.imprimir_pdf_profesores).pack(side="left", padx=10)
        
        # Creamos una tabla (Treeview) para mostrar la información.
        # Definimos las columnas que tendrá la tabla.
        columnas = ("Profesor", "Materia", "Año Escolar", "Sección")
        self.tree_prof = ttk.Treeview(tab, columns=columnas, show="headings")
        
        # Ponemos los títulos a las columnas.
        for col in columnas:
            self.tree_prof.heading(col, text=col)
            
        # Ajustamos el ancho de cada columna.
        self.tree_prof.column("Profesor", width=300)
        self.tree_prof.column("Materia", width=250)
        self.tree_prof.column("Año Escolar", width=150)
        self.tree_prof.column("Sección", width=100)
        
        # Ponemos la tabla en la pestaña para que ocupe el espacio disponible.
        self.tree_prof.pack(fill="both", expand=True, padx=20, pady=10)
        # Llamamos al método para llenar la tabla con datos.
        self.cargar_tabla_profesores() # Llenamos la pizarra al entrar

    def cargar_tabla_profesores(self):
        # Este método busca en la base de datos qué materias da cada profesor y las muestra en la tabla.
        
        # Primero, borramos todos los datos que había en la tabla.
        for item in self.tree_prof.get_children(): self.tree_prof.delete(item)
            
        # Creamos una conexión a la base de datos.
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                # Creamos un cursor para hacer consultas a la base de datos.
                cursor = conn.cursor()
                # Esta es la consulta SQL que une varias tablas para obtener la información completa.
                # Une las tablas de clases, profesores, grados y secciones.
                sql = """
                    SELECT P.NOMBRE_COMPLETO, C.NOMBRE_MATERIA, G.DESCRIPCION, S.DESCRIPCION
                    FROM TBL_CLASES C
                    JOIN TBL_PROFESORES P ON C.ID_PROFESOR = P.ID_PROFESOR
                    JOIN TBL_GRADOS G ON C.ID_GRADO = G.ID_GRADO
                    JOIN TBL_SECCIONES S ON C.ID_SECCION = S.ID_SECCION
                    ORDER BY P.NOMBRE_COMPLETO, G.ID_GRADO, S.DESCRIPCION
                """
                # Ejecutamos la consulta.
                cursor.execute(sql)
                # Para cada fila que obtenemos, la agregamos a la tabla.
                for fila in cursor.fetchall():
                    self.tree_prof.insert("", "end", values=fila)
            finally: 
                # Al final, cerramos la conexión a la base de datos.
                db.cerrar()

    def imprimir_pdf_profesores(self):
        # Este método toma la información de la tabla y la guarda en un archivo PDF.
        
        # Primero, verificamos si hay datos en la tabla. Si no hay, no hacemos nada.
        if not self.tree_prof.get_children(): return
        
        # Pedimos al usuario que elija dónde guardar el archivo PDF.
        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Carga_Docentes.pdf")
        # Si el usuario cancela, no hacemos nada.
        if not ruta: return

        try:
            # Creamos un objeto canvas para dibujar en el PDF.
            c = canvas.Canvas(ruta, pagesize=letter)
            # Obtenemos el ancho y alto de la página.
            ancho, alto = letter
            
            # Dibujamos el membrete en la parte superior.
            c.setFont("Helvetica-Bold", 9)
            c.drawString(40, alto - 40, "República Bolivariana de Venezuela")
            c.drawString(40, alto - 55, "Ministerio del Poder Popular para la Educación")
            c.drawString(40, alto - 70, "Complejo Educativo 'Colinas del Llano'")
            # Intentamos dibujar el logo, si no se puede, continuamos.
            try:
                c.drawImage("LOGOLICEO.png", ancho - 100, alto - 90, width=60, height=60, mask='auto')
            except: pass
            
            # Ponemos el título del documento.
            y = alto - 120
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(ancho/2, y, "CARGA SECCION DOCENTE")
            y -= 30
            
            # Dibujamos los títulos de las columnas.
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, "Profesor"); c.drawString(250, y, "Materia")
            c.drawString(420, y, "Año"); c.drawString(500, y, "Sección")
            y -= 10; c.line(40, y, 550, y); y -= 20
            
            # Ahora, dibujamos los datos fila por fila.
            c.setFont("Helvetica", 9)
            for item in self.tree_prof.get_children():
                # Si nos quedamos sin espacio en la página, creamos una nueva página.
                if y < 50: c.showPage(); y = alto - 50; c.setFont("Helvetica", 9)
                
                # Obtenemos los valores de la fila.
                valores = self.tree_prof.item(item)['values']
                # Dibujamos cada columna.
                c.drawString(40, y, str(valores[0])[:35])  # Profesor
                c.drawString(250, y, str(valores[1])[:25]) # Materia
                c.drawString(420, y, str(valores[2]))      # Año
                c.drawString(500, y, str(valores[3]))      # Sección
                y -= 15
                
            # Guardamos el PDF.
            c.save()
            # Mostramos un mensaje de que se guardó correctamente.
            messagebox.showinfo("Listo", "PDF guardado correctamente.")
        except Exception as e:
            # Si hay un error, mostramos el mensaje de error.
            messagebox.showerror("Error", str(e))

    # =========================================================================
    # Esta sección crea la segunda pestaña, que permite explorar los salones.
    # =========================================================================
    def crear_pestaña_explorador_salones(self):
        # Este método crea la pestaña para ver los salones con sus materias y alumnos.
        
        # Creamos el marco para esta pestaña con un color de fondo.
        tab = tk.Frame(self.notebook, bg="#f4f6f7")
        # Agregamos la pestaña al contenedor.
        self.notebook.add(tab, text="🏫 Explorador de Salones")
        
        # -- SECCIÓN SUPERIOR: Los filtros para elegir grado y sección --
        # Creamos un marco para los filtros con un color diferente.
        f_filtros = tk.Frame(tab, bg="#e5e8e8", pady=15, relief="ridge", bd=2)
        f_filtros.pack(fill="x", padx=20, pady=10)
        
        # Etiqueta y lista desplegable para seleccionar el año (grado).
        tk.Label(f_filtros, text="1. Seleccione el Año:", bg="#e5e8e8", font=("bold")).pack(side="left", padx=10)
        self.combo_grados = ttk.Combobox(f_filtros, state="readonly", width=15)
        self.combo_grados.pack(side="left", padx=5)
        
        # Etiqueta y lista desplegable para seleccionar la sección.
        tk.Label(f_filtros, text="2. Seleccione la Sección:", bg="#e5e8e8", font=("bold")).pack(side="left", padx=(30, 10))
        self.combo_secciones = ttk.Combobox(f_filtros, state="readonly", width=10)
        self.combo_secciones.pack(side="left", padx=5)
        
        # Botón para abrir el salón seleccionado.
        tk.Button(f_filtros, text="🔍 ABRIR SALÓN", bg="#2980b9", fg="white", font=("bold"),
                  command=self.abrir_gaveta_salon).pack(side="left", padx=30)
        
        # Botón para imprimir la lista de alumnos.
        tk.Button(f_filtros, text="🖨️ IMPRIMIR LISTA", bg="#c0392b", fg="white", font=("bold"),
                  command=self.imprimir_lista_salon).pack(side="left", padx=10)
        # Llamamos al método para cargar las opciones en las listas desplegables.
        self.cargar_opciones_comboboxes()

        # -- SECCIÓN INFERIOR: La información del salón --
        # Creamos un marco para mostrar la información.
        f_info = tk.Frame(tab, bg="#f4f6f7")
        f_info.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Dividimos la sección inferior en dos partes: izquierda y derecha.
        f_izq = tk.Frame(f_info, bg="#f4f6f7"); f_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))
        f_der = tk.Frame(f_info, bg="#f4f6f7"); f_der.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # En la parte izquierda, tabla de materias.
        tk.Label(f_izq, text="📚 Materias y Profesores Asignados", bg="#f4f6f7", font=("Arial", 11, "bold")).pack(pady=5)
        self.tree_clases = ttk.Treeview(f_izq, columns=("Materia", "Profesor"), show="headings")
        self.tree_clases.heading("Materia", text="Materia"); self.tree_clases.heading("Profesor", text="Profesor")
        self.tree_clases.pack(fill="both", expand=True)

        # En la parte derecha, tabla de alumnos.
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

    def imprimir_lista_salon(self):
        """El secretario revisa qué gaveta está abierta y genera el PDF."""
        
        # 1. Verificar si hay hojas en la mesa (Si hay alumnos en la tabla)
        if not self.tree_alumnos.get_children():
            messagebox.showwarning("Atención", "No hay alumnos en este salón para imprimir.")
            return

        # 2. Saber qué gaveta estamos viendo (Para el título del PDF)
        grado = self.combo_grados.get()
        seccion = self.combo_secciones.get()
        titulo_pdf = f"Listado de Alumnos - {grado} Seccion {seccion}"
        
        # 3. Preguntar dónde guardar el archivo
        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Lista_{grado}_{seccion}.pdf")
        if not ruta: return

        try:
            # 4. Preparar el papel membretado
            c = canvas.Canvas(ruta, pagesize=letter)
            ancho, alto = letter
            y = alto - 50
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, "Complejo Educativo 'Colinas del Llano'")
            y -= 30
            
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(ancho/2, y, titulo_pdf.upper())
            y -= 30
            
            # Títulos de las columnas
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, "Cédula")
            c.drawString(200, y, "Nombre del Estudiante")
            c.drawString(500, y, "Firma") # Espacio para que firmen asistencia manual
            y -= 10; c.line(50, y, 550, y); y -= 20
            
            # 5. El Dictado (Leer la tabla visual fila por fila)
            c.setFont("Helvetica", 10)
            numero_lista = 1
            
            for item in self.tree_alumnos.get_children():
                if y < 50: c.showPage(); y = alto - 50; c.setFont("Helvetica", 10)
                
                valores = self.tree_alumnos.item(item)['values']
                
                c.drawString(50, y, str(valores[0])) # Cédula
                c.drawString(200, y, f"{numero_lista}. {str(valores[1])}") # Nombre numerado
                c.drawString(500, y, "__________________") # Línea para firmar
                
                y -= 20
                numero_lista += 1
                
            c.save()
            messagebox.showinfo("Éxito", "La lista del salón ha sido generada en PDF.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    GestorCoordinacion()