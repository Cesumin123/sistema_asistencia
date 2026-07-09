import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry

# Importamos el Dominio
from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia

class GestorAsistenciaUI:
    def __init__(self, repo_asistencia, respaldo_emergencia, db_conexion):
        """
        Inyectamos los puertos (BD y JSON) y la conexión general (solo para 
        leer las listas desplegables de forma KISS sin complicar la arquitectura por ahora).
        """
        self.repo = repo_asistencia
        self.respaldo = respaldo_emergencia
        self.db = db_conexion
        
        # Aquí vivirá el objeto de dominio que controla las reglas
        self.planilla_actual = None 
        
        self.root_selector = tk.Toplevel()
        self.root_selector.title("Paso 1: Seleccionar Clase")
        self.root_selector.geometry("500x350")
        self.root_selector.state('zoomed')
        
        self.crear_interfaz_selector()

    def crear_interfaz_selector(self):
        tk.Label(self.root_selector, text="Seleccione la Clase:", font=("Arial", 11)).pack(pady=10)
        self.combo_clases = ttk.Combobox(self.root_selector, width=60, state="readonly")
        self.combo_clases.pack()
        
        self.ids_clases = [] 
        self.cargar_clases_bd() # Carga visual de solo lectura
        
        tk.Label(self.root_selector, text="Fecha de Asistencia:", font=("Arial", 11)).pack(pady=10)
        self.cal_fecha = DateEntry(self.root_selector, width=12, background='darkblue', 
                                   foreground='white', borderwidth=2, 
                                   date_pattern='dd/mm/yyyy', locale='es_ES')
        self.cal_fecha.pack()
        
        tk.Button(self.root_selector, text="COMENZAR CLASE ▶", bg="#2980b9", fg="white", 
                  font=("Arial", 10, "bold"), cursor="hand2",
                  command=self.preparar_planilla).pack(pady=20)

    def cargar_clases_bd(self):
        """KISS: Lectura directa para el Combobox."""
        conn = self.db.conectar()
        if not conn: return
        try:
            cursor = conn.cursor()
            sql = """SELECT C.ID_CLASE, 
                            C.NOMBRE_MATERIA || ' - ' || G.DESCRIPCION || ' ' || S.DESCRIPCION 
                     FROM TBL_CLASES C 
                     JOIN TBL_GRADOS G ON C.ID_GRADO=G.ID_GRADO 
                     JOIN TBL_SECCIONES S ON C.ID_SECCION=S.ID_SECCION"""
            cursor.execute(sql)
            
            nombres = []
            for row in cursor.fetchall():
                self.ids_clases.append(row[0])
                nombres.append(row[1])
            
            self.combo_clases['values'] = nombres
            if nombres: self.combo_clases.current(0)
        finally: 
            self.db.cerrar()

    def preparar_planilla(self):
        """Orquesta la creación del dominio antes de dibujar la ventana."""
        idx = self.combo_clases.current()
        if idx == -1: return
        
        id_clase = self.ids_clases[idx]
        nombre_clase = self.combo_clases.get()
        # Regla de Arquitectura: La fecha es siempre texto (str)
        fecha_str = self.cal_fecha.get_date().strftime("%d/%m/%Y") 
        
        # 1. Intentamos recuperar una planilla del apagón
        planilla_recuperada = self.respaldo.recuperar_respaldo(id_clase, fecha_str)
        
        if planilla_recuperada:
            resp = messagebox.askyesno("Recuperación", 
                "¡ATENCIÓN! Se encontró una lista sin guardar del apagón.\n"
                "¿Deseas recuperar lo que llevabas?")
            if resp:
                self.planilla_actual = planilla_recuperada
            else:
                self.respaldo.limpiar_respaldo()
                self.planilla_actual = self.crear_nueva_planilla(id_clase, fecha_str)
        else:
            self.planilla_actual = self.crear_nueva_planilla(id_clase, fecha_str)

        self.root_selector.destroy() 
        self.crear_ventana_planilla(nombre_clase)

    def crear_nueva_planilla(self, id_clase: int, fecha_str: str) -> PlanillaAsistencia:
        """KISS: Busca los alumnos y construye el objeto de Dominio."""
        nueva_planilla = PlanillaAsistencia(id_clase=id_clase, fecha=fecha_str)
        conn = self.db.conectar()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT ID_GRADO, ID_SECCION FROM TBL_CLASES WHERE ID_CLASE=?", (id_clase,))
                datos = cur.fetchone()
                if datos:
                    sql = "SELECT ID_ESTUDIANTE, NOMBRE FROM TBL_ESTUDIANTES WHERE ID_GRADO=? AND ID_SECCION=? ORDER BY NOMBRE"
                    cur.execute(sql, (datos[0], datos[1]))
                    for alum in cur.fetchall():
                        # Por defecto todos se crean PRESENTES en el dominio
                        nueva_planilla.registros.append(RegistroAsistencia(id_estudiante=alum[0]))
                        # Guardamos el nombre dinámicamente en el objeto visual, no en el dominio
                        # para no ensuciar la entidad con datos que son solo visuales.
                        alum_nombres = getattr(self, '_nombres_temp', {})
                        alum_nombres[alum[0]] = alum[1]
                        self._nombres_temp = alum_nombres
            finally: 
                self.db.cerrar()
        return nueva_planilla

    def crear_ventana_planilla(self, nombre_clase):
        """Dibuja la tabla visual basándose 100% en el Dominio."""
        self.win_planilla = tk.Toplevel()
        self.win_planilla.title("Planilla de Asistencia")
        self.win_planilla.geometry("850x600")
        self.win_planilla.state('zoomed')
        
        # Encabezado
        frame_head = tk.Frame(self.win_planilla, bg="#ecf0f1", pady=10)
        frame_head.pack(fill="x")
        tk.Label(frame_head, text=nombre_clase, font=("Arial", 12, "bold"), bg="#ecf0f1").pack()
        tk.Label(frame_head, text=f"Fecha: {self.planilla_actual.fecha}", font=("Arial", 10), bg="#ecf0f1").pack()
        
        # Tabla
        self.tree = ttk.Treeview(self.win_planilla, columns=("id", "nom", "st"), show="headings", height=15)
        self.tree.heading("id", text="Cédula"); self.tree.column("id", width=100)
        self.tree.heading("nom", text="Estudiante"); self.tree.column("nom", width=400)
        self.tree.heading("st", text="Estado"); self.tree.column("st", width=80, anchor="center")
        
        self.tree.tag_configure("presente", foreground="green")
        self.tree.tag_configure("ausente", foreground="red")
        self.tree.tag_configure("justificado", foreground="#d35400")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.refrescar_tabla()
        
        # Botones
        fb = tk.Frame(self.win_planilla, pady=10); fb.pack()
        
        tk.Button(fb, text="✅ PRESENTE", bg="#2ecc71", fg="white", 
                  command=lambda: self.cambiar_estado(EstadoAsistencia.PRESENTE)).pack(side="left", padx=5)
        
        tk.Button(fb, text="❌ AUSENTE", bg="#e74c3c", fg="white", 
                  command=lambda: self.cambiar_estado(EstadoAsistencia.AUSENTE)).pack(side="left", padx=5)
        
        tk.Button(fb, text="⚠️ JUSTIFICADA", bg="#f39c12", fg="white", 
                  command=lambda: self.cambiar_estado(EstadoAsistencia.JUSTIFICADO)).pack(side="left", padx=5)
        
        tk.Button(self.win_planilla, text="💾 GUARDAR EN BASE DE DATOS", bg="#34495e", fg="white", font=("bold"), width=30,
                  command=self.guardar_final_bd).pack(pady=15)

    def refrescar_tabla(self):
        """Limpia la tabla y la vuelve a dibujar según el estado del Dominio."""
        for i in self.tree.get_children(): self.tree.delete(i)
        
        for reg in self.planilla_actual.registros:
            tag = "presente"
            if reg.estado == EstadoAsistencia.AUSENTE: tag = "ausente"
            elif reg.estado == EstadoAsistencia.JUSTIFICADO: tag = "justificado"
            
            nombre = self._nombres_temp.get(reg.id_estudiante, "Recuperado")
            self.tree.insert("", "end", values=(reg.id_estudiante, nombre, reg.estado.value), tags=(tag,))

    def cambiar_estado(self, nuevo_estado: EstadoAsistencia):
        """Le pasa la acción al Dominio y luego hace Backup."""
        seleccion = self.tree.selection()
        if not seleccion: return

        for item in seleccion:
            cedula = self.tree.item(item, "values")[0]
            
            motivo = None
            if nuevo_estado == EstadoAsistencia.JUSTIFICADO:
                motivo = simpledialog.askstring("Motivo", "¿Por qué faltó el estudiante?")
                if not motivo: continue # Cancela si lo deja en blanco
            
            # --- DELEGAMOS AL DOMINIO ---
            self.planilla_actual.actualizar_registro(cedula, nuevo_estado, motivo)
            
        self.refrescar_tabla()
        
        # --- BLINDAJE ANTI-APAGONES: Guardamos el dominio completo ---
        self.respaldo.guardar_respaldo(self.planilla_actual)

    def guardar_final_bd(self):
        """Envía el Dominio final al adaptador SQLite."""
        if not self.planilla_actual.registros: return

        try:
            # 1. Guardamos usando nuestro Puerto
            self.repo.guardar_planilla(self.planilla_actual)
            
            # 2. Limpiamos el archivo JSON porque ya no hay emergencia
            self.respaldo.limpiar_respaldo()
            
            messagebox.showinfo("Éxito", f"Se guardó la asistencia de {len(self.planilla_actual.registros)} alumnos.")
            self.win_planilla.destroy()
            
        except Exception as err:
            messagebox.showerror("Error Crítico", str(err))