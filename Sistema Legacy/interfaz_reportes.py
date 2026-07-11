import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from db_conexion import ConexionBD
from plantilla_pdf import ImprentaPDF  # Importamos la plantilla para el membrete y formato PDF 
from datetime import date
from tkcalendar import DateEntry 

class GestorReportes:
    """
    Módulo de Inteligencia (Reportes).
    Aquí convertimos los datos crudos en información útil para el Director.
    Permite filtrar por Día, Mes o Alumno y exportar a PDF.
    """
    
    def __init__(self):
        self.root = tk.Toplevel()
        self.root.title("Gestor de Reportes y Estadísticas")
        self.root.geometry("1100x750")
        self.root.state('zoomed')  # Abrir en pantalla completa
        
        # --- Memoria del Reporte ---
        # Guardamos qué estamos viendo para ponerlo en el título del PDF
        self.contexto_actual = "GENERAL"  
        self.info_contexto = ""           
        self.sql_filtro_actual = ""       
        self.params_filtro_actual = ()
        
        # Pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, fill="both", expand=True)
        
        self.crear_tabs()
        self.crear_tabla_comun()
        self.crear_botones_accion()

    def crear_tabs(self):
        """Crea las 3 pestañas de búsqueda."""
        
        # 1. Por Día
        t1 = tk.Frame(self.notebook); self.notebook.add(t1, text="📅 Reporte Diario")
        f1 = tk.Frame(t1); f1.pack(pady=10)
        tk.Label(f1, text="Seleccione Fecha:").pack(side="left")
        self.cal_dia = DateEntry(f1, width=12, date_pattern='dd/mm/y', locale='es_ES', background='darkblue')
        self.cal_dia.pack(side="left", padx=10)
        tk.Button(f1, text="🔍 Buscar Día", command=self.buscar_por_dia).pack(side="left")

        # 2. Por Mes
        t2 = tk.Frame(self.notebook); self.notebook.add(t2, text="📅 Reporte Mensual")
        f2 = tk.Frame(t2); f2.pack(pady=10)
        # Lista de meses
        self.combo_mes = ttk.Combobox(f2, values=["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                                                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], 
                                      state="readonly")
        self.combo_mes.pack(side="left"); self.combo_mes.current(0)
        tk.Button(f2, text="🔍 Buscar Mes", command=self.buscar_por_mes).pack(side="left", padx=5)

        # 3. Por Alumno
        t3 = tk.Frame(self.notebook); self.notebook.add(t3, text="👤 Historial Estudiante")
        f3 = tk.Frame(t3); f3.pack(pady=10)
        tk.Label(f3, text="Cédula:").pack(side="left")
        self.entry_ced_buscar = tk.Entry(f3); self.entry_ced_buscar.pack(side="left", padx=5)
        tk.Button(f3, text="🔍 Buscar Historial", command=self.buscar_por_cedula).pack(side="left")

    def crear_tabla_comun(self):
        """La tabla central donde se ven los resultados."""
        tk.Label(self.root, text="💡 Tip: Doble Click en una fila para ver la ficha del estudiante", fg="#7f8c8d").pack()
        
        cols = ("Fecha", "Cédula", "Materia", "Estudiante", "Estado", "Observacion")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        
        self.tree.heading("Fecha", text="Fecha"); self.tree.column("Fecha", width=80)
        self.tree.heading("Cédula", text="Cédula"); self.tree.column("Cédula", width=80)
        self.tree.heading("Materia", text="Materia"); self.tree.column("Materia", width=150)
        self.tree.heading("Estudiante", text="Estudiante"); self.tree.column("Estudiante", width=250)
        self.tree.heading("Estado", text="ST"); self.tree.column("Estado", width=50, anchor="center")
        self.tree.heading("Observacion", text="Motivo / Justificación"); self.tree.column("Observacion", width=200)
        
        self.tree.pack(fill="both", expand=True, padx=20)
        self.tree.bind("<Double-1>", self.ver_detalle_alumno)

    def crear_botones_accion(self):
        """Botones de abajo."""
        bf = tk.Frame(self.root, pady=10); bf.pack()
        
        tk.Button(bf, text="📊 VER ALERTAS DE RIESGO", bg="#e67e22", fg="white", font=("Arial", 10, "bold"), 
                  command=self.mostrar_alertas).pack(side="left", padx=20)
        
        tk.Button(bf, text="🖨️ EXPORTAR A PDF", bg="#c0392b", fg="white", font=("Arial", 10, "bold"), 
                  command=self.generar_pdf).pack(side="left", padx=20)

    # -------------------------------------------------------------------------
    # MOTORES DE BÚSQUEDA (ADAPTADOS A SQLITE)
    # -------------------------------------------------------------------------
    
    def ejecutar_busqueda(self, where_sql, params, tipo, info):
        """
        Función Maestra: Recibe un trozo de SQL (el filtro) y llena la tabla.
        """
        self.contexto_actual = tipo
        self.info_contexto = info
        self.sql_filtro_actual = where_sql 
        self.params_filtro_actual = params

        # Limpiar tabla visual
        for i in self.tree.get_children(): self.tree.delete(i)
        
        # Consulta Base: Unimos Asistencia + Clases + Estudiantes + Justificaciones
        # SQLITE: Usamos COALESCE en lugar de IFNULL
        sql_base = """
            SELECT A.FECHA, A.ID_ESTUDIANTE, C.NOMBRE_MATERIA, E.NOMBRE, A.ESTADO, COALESCE(J.MOTIVO, '-') 
            FROM TBL_ASISTENCIA A
            JOIN TBL_CLASES C ON A.ID_CLASE = C.ID_CLASE
            JOIN TBL_ESTUDIANTES E ON A.ID_ESTUDIANTE = E.ID_ESTUDIANTE
            LEFT JOIN TBL_JUSTIFICACIONES J ON A.ID_ASISTENCIA = J.ID_ASISTENCIA
        """
        
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cur = conn.cursor()
                # Unimos la base + el filtro (WHERE ...)
                cur.execute(sql_base + where_sql, params)
                registros = cur.fetchall()
                
                for row in registros:
                    self.tree.insert("", "end", values=row)
                
                if not registros:
                    messagebox.showinfo("Sin Resultados", "No se encontraron datos.")
            finally: db.cerrar()

    def buscar_por_dia(self):
        # SQLITE guarda fechas como YYYY-MM-DD
        fecha_obj = self.cal_dia.get_date()
        fecha_str = fecha_obj.strftime('%Y-%m-%d')
        self.ejecutar_busqueda(" WHERE A.FECHA = ? ORDER BY C.NOMBRE_MATERIA", (fecha_str,), "DIA", str(fecha_str))

    def buscar_por_mes(self):
        # SQLITE: Para sacar el mes usamos strftime('%m', FECHA)
        # Ojo: strftime devuelve "01", "02"... así que formateamos el número.
        mes_idx = self.combo_mes.current() + 1
        mes_str = f"{mes_idx:02d}" # Convierte 1 en "01", 10 en "10"
        
        mes_nombre = self.combo_mes.get()
        
        self.ejecutar_busqueda(" WHERE strftime('%m', A.FECHA) = ? ORDER BY A.FECHA DESC", (mes_str,), "MES", mes_nombre)

    def buscar_por_cedula(self):
        ced = self.entry_ced_buscar.get().strip()
        if not ced: return
        self.ejecutar_busqueda(" WHERE A.ID_ESTUDIANTE LIKE ? ORDER BY A.FECHA DESC", (f"%{ced}%",), "ALUMNO", ced)

   # -------------------------------------------------------------------------
    # GENERADOR DE PDF (Refactorizado para Integración con ImprentaPDF)
    # -------------------------------------------------------------------------
    def generar_pdf(self):
        # 1. Validación de Estado Inicial:
        # Se verifica si la estructura de datos subyacente del Treeview contiene elementos.
        # Si la tupla devuelta por get_children() está vacía, se interrumpe la ejecución.
        if not self.tree.get_children():
            messagebox.showwarning("Vacío", "Primero haz una búsqueda.")
            return

        # 2. Inicialización de E/S (Input/Output):
        # Se define el string base para el nombre del archivo utilizando el contexto actual de búsqueda.
        nombre_archivo = f"Reporte_{self.contexto_actual}.pdf"
        # Se invoca el diálogo del sistema operativo para obtener la ruta absoluta de destino.
        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=nombre_archivo)
        
        if not ruta: return # Terminación temprana si el usuario cancela la operación de guardado.
        
        try:
            # 3. Extracción y Transformación de Datos:
            # Se inicializa una lista vacía que actuará como la matriz principal de datos para ReportLab.
            datos_para_pdf = []
            
            # Se itera sobre los identificadores (IIDs) de los nodos del Treeview.
            for item in self.tree.get_children():
                # Extracción de la tupla de valores correspondientes a la fila actual.
                vals = self.tree.item(item)['values']
                
                # Transformación de tipos: Se aplica casting a 'str' a cada elemento iterado de 'vals'
                # para garantizar la serialización correcta del texto en el objeto Table de ReportLab.
                fila = [str(v) for v in vals] 
                
                # Inserción de la fila procesada en la matriz principal.
                datos_para_pdf.append(fila)
            
            # 4. Definición de la Cabecera de Datos:
            # Se define estáticamente la primera fila de la tabla que contendrá los metadatos de las columnas.
            encabezados = ["Fecha", "Cédula", "Materia", "Estudiante", "ST", "Justificación"]

            # 5. Generación Dinámica del Título:
            # Se construye la cadena de texto para el título del reporte basándose en las variables de estado de la clase.
            titulo_dinamico = f"REPORTE: {self.contexto_actual} - {self.info_contexto}"
            
            # 6. Delegación de la Generación del Documento:
            # Se invoca al método estático de la clase externa ImprentaPDF.
            # Se transfiere la responsabilidad de la renderización gráfica (coordenadas, bordes, paginación)
            # al motor Platypus configurado dentro de dicha clase.
            ImprentaPDF.generar_reporte_tabla(ruta, titulo_dinamico, encabezados, datos_para_pdf)
            
            # 7. Confirmación de Éxito:
            messagebox.showinfo("Éxito", "Reporte PDF generado exitosamente a través de la plantilla central.")

        except Exception as e:
            # Captura de excepciones generales (I/O, permisos, o errores de ReportLab) durante el proceso.
            messagebox.showerror("Error PDF", str(e))

    def obtener_estadisticas_pdf(self):
        """Calcula cuántos hombres y mujeres faltaron o vinieron."""
        stats = {}
        
        db = ConexionBD()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # Limpiamos el 'ORDER BY' para que no choque con el conteo
                filtro_limpio = self.sql_filtro_actual.split(" ORDER BY")[0]
                
                sql = f"""
                    SELECT E.GENERO, A.ESTADO, COUNT(*)
                    FROM TBL_ASISTENCIA A
                    JOIN TBL_ESTUDIANTES E ON A.ID_ESTUDIANTE = E.ID_ESTUDIANTE
                    JOIN TBL_CLASES C ON A.ID_CLASE = C.ID_CLASE
                    {filtro_limpio}
                    GROUP BY E.GENERO, A.ESTADO
                """
                cursor.execute(sql, self.params_filtro_actual)
                
                for row in cursor.fetchall():
                    # Creamos una clave tipo "M_P" (Masculino_Presente)
                    clave = f"{row[0]}_{row[1]}" 
                    stats[clave] = row[2]
            finally: db.cerrar()
        return stats

    # -------------------------------------------------------------------------
    # EXTRAS: VER FICHA Y ALERTAS
    # -------------------------------------------------------------------------
    
    def ver_detalle_alumno(self, event):
        """Si das doble clic, te muestra los datos personales del alumno."""
        sel = self.tree.selection()
        if not sel: return
        cedula = self.tree.item(sel[0])['values'][1]
        
        db = ConexionBD(); conn = db.conectar()
        if conn:
            cur = conn.cursor()
            sql = """SELECT E.NOMBRE, E.ID_ESTUDIANTE, E.FECHA_NACIMIENTO, E.GENERO, E.REPRESENTANTE, E.TELEFONO, G.DESCRIPCION, S.DESCRIPCION
                     FROM TBL_ESTUDIANTES E JOIN TBL_GRADOS G ON E.ID_GRADO = G.ID_GRADO
                     JOIN TBL_SECCIONES S ON E.ID_SECCION = S.ID_SECCION WHERE E.ID_ESTUDIANTE = ?"""
            cur.execute(sql, (cedula,))
            datos = cur.fetchone()
            if datos: 
                self.mostrar_ventana_ficha(datos)
            db.cerrar()

    def mostrar_ventana_ficha(self, datos):
        """Ventanita flotante con los datos."""
        win = tk.Toplevel(); win.title("Ficha del Estudiante"); win.geometry("500x450")
        tk.Label(win, text="FICHA TÉCNICA", font=("Arial", 14, "bold")).pack(pady=10)
        
        f = tk.Frame(win, padx=20); f.pack(fill="both")
        lbls = ["Nombre:", "Cédula:", "F. Nac:", "Género:", "Representante:", "Teléfono:", "Año:", "Sección:"]
        
        for i, l in enumerate(lbls):
            val = str(datos[i]) if datos[i] else "-"
            tk.Label(f, text=l, font=("bold")).grid(row=i, column=0, sticky="w", pady=5)
            tk.Label(f, text=val).grid(row=i, column=1, sticky="w", padx=10)

    def mostrar_alertas(self):
        """Busca alumnos con más de 3 faltas en el mes actual."""
        win = tk.Toplevel(); win.title("Alertas de Riesgo"); win.geometry("600x500")
        
        # SQLITE: Mes actual como texto "01", "02"...
        mes_actual = f"{date.today().month:02d}"
        
        db = ConexionBD(); conn = db.conectar()
        if conn:
            cur = conn.cursor()
            
            # 1. Total ausencias del colegio
            cur.execute("SELECT COUNT(*) FROM TBL_ASISTENCIA WHERE strftime('%m', FECHA)=? AND ESTADO='A'", (mes_actual,))
            total = cur.fetchone()[0]
            tk.Label(win, text=f"Total Ausencias en el Colegio (Mes {mes_actual}): {total}", font=("Arial", 12)).pack(pady=10)
            
            # 2. Lista de Alumnos Peligrosos
            tk.Label(win, text="⚠️ ALUMNOS EN RIESGO (>3 Faltas)", fg="red", font=("bold")).pack()
            
            tr = ttk.Treeview(win, columns=("c","n","f"), show="headings")
            tr.heading("c", text="Cédula"); tr.heading("n", text="Nombre"); tr.heading("f", text="Faltas")
            tr.pack(fill="both", padx=20, pady=10)
            
            # SQL Complejo adaptado a SQLite
            sql = """SELECT A.ID_ESTUDIANTE, E.NOMBRE, COUNT(*) as F 
                     FROM TBL_ASISTENCIA A 
                     JOIN TBL_ESTUDIANTES E ON A.ID_ESTUDIANTE=E.ID_ESTUDIANTE 
                     WHERE strftime('%m', A.FECHA)=? AND A.ESTADO='A' 
                     GROUP BY A.ID_ESTUDIANTE 
                     HAVING F>=3 
                     ORDER BY F DESC"""
            
            cur.execute(sql, (mes_actual,))
            for r in cur.fetchall(): 
                tr.insert("", "end", values=r)
            
            db.cerrar()

if __name__ == "__main__":
    GestorReportes()
