import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3 
from db_conexion import ConexionBD
from datetime import date
from plantilla_pdf import ImprentaPDF  # Importamos la plantilla para el membrete y formato PDF

class VisorListados:
    """
    Este módulo es como una 'Lupa'.
    Sirve para ver tablas gigantes con toda la información y 
    convertirlas en documentos PDF para imprimir.
    """
    def __init__(self):
        self.root = tk.Toplevel()
        self.root.title("Listados Generales del Sistema")
        self.root.geometry("1100x650")
        self.root.state('zoomed') # Abrir en pantalla completa 
        
        # Sistema de Pestañas (Notebook)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Creamos las 3 pestañas principales
        self.crear_tab_alumnos()
        self.crear_tab_materias()
        self.crear_tab_profesores()

    def cargar_tabla(self, tree, sql):
        """
        Esta función es un 'Mesero'.
        Toma una orden (SQL), va a la cocina (Base de Datos),
        trae la comida (Datos) y la sirve en la mesa (Tabla visual).
        """
        # 1. Limpiamos la mesa (Borrar datos viejos)
        for item in tree.get_children(): tree.delete(item)
        
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql) # Ejecutamos la consulta
                
                # Servimos los datos fila por fila
                for row in cursor.fetchall():
                    tree.insert("", "end", values=row)
            finally: db.cerrar()

    def imprimir_listado(self, tree, titulo_reporte, encabezados):
        """
        Envía los datos de la tabla visual a la Imprenta Central.
        Fíjate que ya no necesitamos mandar posiciones_x.
        """
        if not tree.get_children():
            messagebox.showwarning("Vacío", "No hay nada que imprimir aquí.")
            return

        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                                            title=f"Guardar {titulo_reporte}",
                                            initialfile=f"{titulo_reporte.replace(' ', '_')}.pdf")
        if not ruta: return

        try:
            # 1. Extraemos todos los datos de la tabla visual y los guardamos en una lista
            datos_para_pdf = []
            for item in tree.get_children():
                # Extraemos los valores de la fila
                valores = tree.item(item)['values']
                
                # Convertimos todo a texto simple para que la tabla lo procese bien
                fila_texto = [str(valor) for valor in valores]
                datos_para_pdf.append(fila_texto)
            
            # 2. Le mandamos el trabajo a la Imprenta Central
            ImprentaPDF.generar_reporte_tabla(ruta, titulo_reporte, encabezados, datos_para_pdf)
            
            messagebox.showinfo("¡Listo!", "Tu documento PDF ha sido generado con la plantilla oficial.")
            
        except Exception as e:
            messagebox.showerror("Error al crear PDF", f"Algo falló: {str(e)}")
    # -------------------------------------------------------------------------
    # PESTAÑA 1: ALUMNOS
    # -------------------------------------------------------------------------
    def crear_tab_alumnos(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="👤 Todos los Alumnos")
        
        # Botonera superior
        f_top = tk.Frame(tab, pady=5); f_top.pack()
        
        # Configuración de Columnas
        cols = ("Cédula", "Nombre", "Nacimiento", "Representante", "Teléfono", "Gen", "Año", "Sec")
        tree = ttk.Treeview(tab, columns=cols, show="headings")
        
        anchos = [80, 200, 80, 200, 90, 40, 50, 40]
        for i, col in enumerate(cols):
            tree.heading(col, text=col)
            tree.column(col, width=anchos[i])
        tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        # SQL: Traemos datos de Estudiantes + Grados + Secciones
        sql = """
            SELECT E.ID_ESTUDIANTE, E.NOMBRE, E.FECHA_NACIMIENTO, 
                   E.REPRESENTANTE, E.TELEFONO,
                   E.GENERO, G.DESCRIPCION, S.DESCRIPCION 
            FROM TBL_ESTUDIANTES E 
            JOIN TBL_GRADOS G ON E.ID_GRADO=G.ID_GRADO 
            JOIN TBL_SECCIONES S ON E.ID_SECCION=S.ID_SECCION 
            ORDER BY G.ID_GRADO, S.DESCRIPCION, E.NOMBRE
        """
        
        # Configuración para el PDF (Títulos y Coordenadas X)
        headers_pdf = ["Cédula", "Estudiante", "F. Nac", "Representante", "Telf", "Gen", "Año", "Sec"]
        pos_x_pdf = [20, 75, 190, 250, 360, 420, 450, 500]

        # Botones de Acción
        tk.Button(f_top, text="🔄 Actualizar Tabla", command=lambda: self.cargar_tabla(tree, sql)).pack(side="left", padx=5)
        tk.Button(f_top, text="🖨️ Imprimir Listado", bg="#c0392b", fg="white",
                  command=lambda: self.imprimir_listado(tree, "LISTADO GENERAL DE ALUMNOS", headers_pdf)).pack(side="left", padx=5)

        # Cargar datos al iniciar
        self.cargar_tabla(tree, sql)

    # -------------------------------------------------------------------------
    # PESTAÑA 2: MATERIAS
    # -------------------------------------------------------------------------
    def crear_tab_materias(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="📚 Todas las Materias")
        f_top = tk.Frame(tab, pady=5); f_top.pack()
        
        cols = ("ID", "Materia", "Profesor", "Año", "Sección")
        tree = ttk.Treeview(tab, columns=cols, show="headings")
        
        for c in cols: tree.heading(c, text=c)
        tree.column("Materia", width=200); tree.column("Profesor", width=200)
        tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        sql = """SELECT C.ID_CLASE, C.NOMBRE_MATERIA, P.NOMBRE_COMPLETO, G.DESCRIPCION, S.DESCRIPCION
                 FROM TBL_CLASES C JOIN TBL_PROFESORES P ON C.ID_PROFESOR=P.ID_PROFESOR
                 JOIN TBL_GRADOS G ON C.ID_GRADO=G.ID_GRADO JOIN TBL_SECCIONES S ON C.ID_SECCION=S.ID_SECCION
                 ORDER BY G.ID_GRADO, C.NOMBRE_MATERIA"""
        
        headers_pdf = ["ID", "Materia", "Profesor Encargado", "Año", "Sección"]
        pos_x_pdf = [30, 60, 250, 450, 500]

        tk.Button(f_top, text="🔄 Actualizar Tabla", command=lambda: self.cargar_tabla(tree, sql)).pack(side="left", padx=5)
        tk.Button(f_top, text="🖨️ Imprimir Listado", bg="#c0392b", fg="white",
                  command=lambda: self.imprimir_listado(tree, "LISTADO GENERAL DE MATERIAS", headers_pdf)).pack(side="left", padx=5)
        self.cargar_tabla(tree, sql)

    # -------------------------------------------------------------------------
    # PESTAÑA 3: PROFESORES
    # -------------------------------------------------------------------------
    def crear_tab_profesores(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="👨‍🏫 Todos los Profesores")
        f_top = tk.Frame(tab, pady=5); f_top.pack()
        
        cols = ("ID", "Nombre", "Cédula")
        tree = ttk.Treeview(tab, columns=cols, show="headings")
        
        for c in cols: tree.heading(c, text=c)
        tree.column("Nombre", width=300)
        tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        sql = "SELECT ID_PROFESOR, NOMBRE_COMPLETO, CEDULA FROM TBL_PROFESORES ORDER BY NOMBRE_COMPLETO"
        
        headers_pdf = ["ID", "Nombre del Docente", "Cédula"]
        pos_x_pdf = [30, 80, 350]

        tk.Button(f_top, text="🔄 Actualizar Tabla", command=lambda: self.cargar_tabla(tree, sql)).pack(side="left", padx=5)
        tk.Button(f_top, text="🖨️ Imprimir Nómina", bg="#c0392b", fg="white",
                  command=lambda: self.imprimir_listado(tree, "NOMINA DE PROFESORES", headers_pdf)).pack(side="left", padx=5)
        self.cargar_tabla(tree, sql)

# Punto de entrada para probar este archivo
if __name__ == "__main__":
    VisorListados()
