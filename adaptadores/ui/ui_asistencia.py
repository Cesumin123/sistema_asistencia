# adaptadores/ui/ui_asistencia.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
from typing import Dict, Optional, List
from abc import ABC, abstractmethod

# Importamos nuestro Dominio
from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia

# ============================================
# NUEVO: Interfaz para la vista (DIP)
# ============================================
class VistaAsistencia(ABC):
    """Abstracción de la vista para facilitar testing y desacoplamiento."""
    
    @abstractmethod
    def mostrar_seleccion_clase(self) -> tuple: pass
    
    @abstractmethod
    def mostrar_planilla(self, planilla: PlanillaAsistencia, nombres: Dict[str, str]) -> None: pass
    
    @abstractmethod
    def actualizar_planilla(self, planilla: PlanillaAsistencia, nombres: Dict[str, str]) -> None: pass
    
    @abstractmethod
    def obtener_accion_usuario(self) -> EstadoAsistencia: pass
    
    @abstractmethod
    def mostrar_error(self, mensaje: str) -> None: pass
    
    @abstractmethod
    def mostrar_exito(self, mensaje: str) -> None: pass

# ============================================
# NUEVO: Servicio de selección de clases (SRP)
# ============================================
class ServicioSeleccionClase:
    """Encapsula la lógica de selección de clases (SRP)."""
    
    def __init__(self, db_conexion):
        self.db = db_conexion
        self._cached_clases = []
        self._cached_ids = []
    
    def obtener_clases_disponibles(self) -> tuple:
        """Retorna (lista_nombres, lista_ids)."""
        if self._cached_clases:
            return self._cached_clases, self._cached_ids
        
        conn = self.db.conectar()
        if not conn:
            return [], []
        
        try:
            cursor = conn.cursor()
            sql = """SELECT C.ID_CLASE, 
                            C.NOMBRE_MATERIA || ' - ' || G.DESCRIPCION || ' ' || S.DESCRIPCION 
                     FROM TBL_CLASES C 
                     JOIN TBL_GRADOS G ON C.ID_GRADO=G.ID_GRADO 
                     JOIN TBL_SECCIONES S ON C.ID_SECCION=S.ID_SECCION
                     ORDER BY G.ID_GRADO, S.DESCRIPCION, C.NOMBRE_MATERIA"""
            cursor.execute(sql)
            
            nombres = []
            ids = []
            for row in cursor.fetchall():
                ids.append(row[0])
                nombres.append(row[1])
            
            self._cached_clases = nombres
            self._cached_ids = ids
            return nombres, ids
        finally: 
            self.db.cerrar()
    
    def obtener_estudiantes_por_clase(self, id_clase: int) -> List[tuple]:
        """Retorna lista de (id_estudiante, nombre)."""
        conn = self.db.conectar()
        if not conn:
            return []
        
        try:
            cur = conn.cursor()
            cur.execute("SELECT ID_GRADO, ID_SECCION FROM TBL_CLASES WHERE ID_CLASE=?", (id_clase,))
            datos = cur.fetchone()
            if not datos:
                return []
            
            sql = """SELECT ID_ESTUDIANTE, NOMBRE 
                     FROM TBL_ESTUDIANTES 
                     WHERE ID_GRADO=? AND ID_SECCION=? 
                       AND ESTADO_ACTIVO = 1
                     ORDER BY NOMBRE"""
            cur.execute(sql, (datos[0], datos[1]))
            return cur.fetchall()
        finally: 
            self.db.cerrar()

# ============================================
# NUEVO: Constructor de planillas (SRP)
# ============================================
class ConstructorPlanilla:
    """Encapsula la creación de planillas (SRP)."""
    
    def __init__(self, servicio_clase: ServicioSeleccionClase):
        self.servicio_clase = servicio_clase
    
    def crear_planilla(self, id_clase: int, fecha_str: str) -> tuple:
        """
        Crea una nueva planilla.
        Retorna: (PlanillaAsistencia, dict_nombres)
        """
        estudiantes = self.servicio_clase.obtener_estudiantes_por_clase(id_clase)
        
        planilla = PlanillaAsistencia(id_clase=id_clase, fecha=fecha_str)
        nombres = {}
        
        for id_est, nombre in estudiantes:
            planilla.registros.append(RegistroAsistencia(id_estudiante=id_est))
            nombres[id_est] = nombre
        
        return planilla, nombres

# ============================================
# NUEVO: Controlador de la UI (SRP)
# ============================================
class ControladorAsistencia:
    """
    Controlador que orquesta la interacción entre la UI y el dominio.
    Sigue el patrón MVC/MVP.
    """
    
    def __init__(self, repo_asistencia, respaldo_emergencia, db_conexion):
        self.repo = repo_asistencia
        self.respaldo = respaldo_emergencia
        self.db = db_conexion
        
        self.servicio_clase = ServicioSeleccionClase(db_conexion)
        self.constructor = ConstructorPlanilla(self.servicio_clase)
        
        self.planilla_actual: Optional[PlanillaAsistencia] = None
        self.nombres_estudiantes: Dict[str, str] = {}
        
        self.vista = None  # Se inyectará más tarde
    
    def iniciar_seleccion(self):
        """Inicia el proceso de selección de clase."""
        clases, ids = self.servicio_clase.obtener_clases_disponibles()
        if not clases:
            messagebox.showerror("Error", "No hay clases disponibles en el sistema.")
            return
        
        # Crear y mostrar selector
        selector = SelectorClaseUI(self, clases, ids)
        selector.mostrar()
    
    def preparar_planilla(self, id_clase: int, fecha_str: str, nombre_clase: str):
        """Prepara la planilla antes de mostrar."""
        # Intentar recuperar respaldo
        planilla_recuperada = self.respaldo.recuperar_respaldo(id_clase, fecha_str)
        
        if planilla_recuperada:
            resp = messagebox.askyesno(
                "Recuperación", 
                "¡ATENCIÓN! Se encontró una lista sin guardar del apagón.\n"
                "¿Deseas recuperar lo que llevabas?"
            )
            if resp:
                self.planilla_actual = planilla_recuperada
                # Recuperar nombres (desde BD)
                self._cargar_nombres_estudiantes()
            else:
                self.respaldo.limpiar_respaldo()
                self.planilla_actual, self.nombres_estudiantes = self.constructor.crear_planilla(
                    id_clase, fecha_str
                )
        else:
            self.planilla_actual, self.nombres_estudiantes = self.constructor.crear_planilla(
                id_clase, fecha_str
            )
        
        # Crear y mostrar la vista de planilla
        planilla_ui = PlanillaUI(self, self.planilla_actual, self.nombres_estudiantes, nombre_clase)
        planilla_ui.mostrar()
    
    def _cargar_nombres_estudiantes(self):
        """Carga los nombres de los estudiantes de la planilla actual."""
        if not self.planilla_actual:
            return
        
        ids = [reg.id_estudiante for reg in self.planilla_actual.registros]
        conn = self.db.conectar()
        if not conn:
            return
        
        try:
            cur = conn.cursor()
            placeholders = ','.join(['?'] * len(ids))
            cur.execute(f"SELECT ID_ESTUDIANTE, NOMBRE FROM TBL_ESTUDIANTES WHERE ID_ESTUDIANTE IN ({placeholders})", ids)
            self.nombres_estudiantes = {row[0]: row[1] for row in cur.fetchall()}
        finally:
            self.db.cerrar()
    
    def cambiar_estado(self, id_estudiante: str, nuevo_estado: EstadoAsistencia, motivo: Optional[str] = None):
        """Cambia el estado de un estudiante en la planilla."""
        if not self.planilla_actual:
            return False
        
        self.planilla_actual.actualizar_registro(id_estudiante, nuevo_estado, motivo)
        self.respaldo.guardar_respaldo(self.planilla_actual)
        return True
    
    def guardar_planilla(self):
        """Guarda la planilla en la base de datos."""
        if not self.planilla_actual or not self.planilla_actual.registros:
            return
        
        try:
            self.repo.guardar_planilla(self.planilla_actual)
            self.respaldo.limpiar_respaldo()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
            return False

# ============================================
# UI: Selector de Clase (SRP)
# ============================================
class SelectorClaseUI:
    """Vista para seleccionar clase y fecha."""
    
    def __init__(self, controlador: ControladorAsistencia, clases: List[str], ids: List[int]):
        self.controlador = controlador
        self.clases = clases
        self.ids = ids
        
        self.root = tk.Toplevel()
        self.root.title("Seleccionar Clase")
        self.root.geometry("500x350")
        self.root.state('zoomed')
    
    def mostrar(self):
        """Muestra la ventana de selección."""
        # Selección de clase
        tk.Label(self.root, text="Seleccione la Clase:", font=("Arial", 11)).pack(pady=10)
        self.combo_clases = ttk.Combobox(self.root, width=60, state="readonly", values=self.clases)
        self.combo_clases.pack()
        if self.clases:
            self.combo_clases.current(0)
        
        # Selección de fecha - CONFIGURADA EN FORMATO ESTRICTO ISO 8601 (AAAA-MM-DD)
        tk.Label(self.root, text="Fecha de Asistencia (AAAA-MM-DD):", font=("Arial", 11, "bold")).pack(pady=10)
        self.cal_fecha = DateEntry(
            self.root, width=14, background='darkblue', 
            foreground='white', borderwidth=2, 
            date_pattern='yyyy-mm-dd', locale='es_ES'
        )
        self.cal_fecha.pack()
        
        # Botón comenzar
        tk.Button(
            self.root, text="COMENZAR CLASE ▶", 
            bg="#2980b9", fg="white", font=("Arial", 10, "bold"), 
            cursor="hand2", command=self._on_comenzar
        ).pack(pady=20)
        
        self.root.mainloop()
    
    def _on_comenzar(self):
        """Callback cuando se presiona Comenzar."""
        idx = self.combo_clases.current()
        if idx == -1:
            return
        
        id_clase = self.ids[idx]
        nombre_clase = self.combo_clases.get()
        
        # Extracción y formateo directo a string ISO para la capa de Dominio e Infraestructura
        fecha_str = self.cal_fecha.get_date().strftime("%Y-%m-%d")
        
        self.root.destroy()
        self.controlador.preparar_planilla(id_clase, fecha_str, nombre_clase)

# ============================================
# UI: Planilla de Asistencia (SRP)
# ============================================
class PlanillaUI:
    """Vista para mostrar y editar la planilla de asistencia."""
    
    def __init__(
        self, 
        controlador: ControladorAsistencia,
        planilla: PlanillaAsistencia,
        nombres: Dict[str, str],
        nombre_clase: str
    ):
        self.controlador = controlador
        self.planilla = planilla
        self.nombres = nombres
        self.nombre_clase = nombre_clase
        
        self.win = tk.Toplevel()
        self.win.title("Planilla de Asistencia")
        self.win.geometry("850x600")
        self.win.state('zoomed')
        
        self.tree = None
        self._crear_interfaz()
    
    def _crear_interfaz(self):
        """Crea toda la interfaz de la planilla."""
        # Encabezado
        self._crear_encabezado()
        
        # Tabla
        self._crear_tabla()
        
        # Botones
        self._crear_botones()
        
        # Refrescar tabla inicial
        self.refrescar()
    
    def _crear_encabezado(self):
        """Crea el encabezado con información de la clase."""
        frame_head = tk.Frame(self.win, bg="#ecf0f1", pady=10)
        frame_head.pack(fill="x")
        
        tk.Label(frame_head, text=self.nombre_clase, font=("Arial", 12, "bold"), bg="#ecf0f1").pack()
        tk.Label(
            frame_head, 
            text=f"Fecha: {self.planilla.fecha}", # Se mostrará en formato AAAA-MM-DD de forma nativa
            font=("Arial", 10, "bold"), 
            bg="#ecf0f1"
        ).pack()
        
        # Mostrar estadísticas
        total = len(self.planilla.registros)
        presentes = sum(1 for r in self.planilla.registros if r.estado == EstadoAsistencia.PRESENTE)
        ausentes = sum(1 for r in self.planilla.registros if r.estado == EstadoAsistencia.AUSENTE)
        justificados = sum(1 for r in self.planilla.registros if r.estado == EstadoAsistencia.JUSTIFICADO)
        
        stats = f"Total: {total} | Presentes: {presentes} | Ausentes: {ausentes} | Justificados: {justificados}"
        tk.Label(frame_head, text=stats, font=("Arial", 9), bg="#ecf0f1", fg="#2c3e50").pack()
    
    def _crear_tabla(self):
        """Crea el TreeView para mostrar los estudiantes."""
        self.tree = ttk.Treeview(
            self.win, 
            columns=("id", "nom", "st"), 
            show="headings", 
            height=15
        )
        self.tree.heading("id", text="Cédula")
        self.tree.column("id", width=100)
        self.tree.heading("nom", text="Estudiante")
        self.tree.column("nom", width=400)
        self.tree.heading("st", text="Estado")
        self.tree.column("st", width=80, anchor="center")
        
        # Tags para colores
        self.tree.tag_configure("presente", foreground="green")
        self.tree.tag_configure("ausente", foreground="red")
        self.tree.tag_configure("justificado", foreground="#d35400")
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Bind de doble click para cambiar estado rápidamente
        self.tree.bind("<Double-Button-1>", self._on_doble_click)
    
    def _crear_botones(self):
        """Crea los botones de acción."""
        # Botones de estado
        fb = tk.Frame(self.win, pady=10)
        fb.pack()
        
        tk.Button(
            fb, text="✅ PRESENTE", bg="#2ecc71", fg="white", 
            command=lambda: self._cambiar_estado_seleccionados(EstadoAsistencia.PRESENTE)
        ).pack(side="left", padx=5)
        
        tk.Button(
            fb, text="❌ AUSENTE", bg="#e74c3c", fg="white", 
            command=lambda: self._cambiar_estado_seleccionados(EstadoAsistencia.AUSENTE)
        ).pack(side="left", padx=5)
        
        tk.Button(
            fb, text="⚠️ JUSTIFICADA", bg="#f39c12", fg="white", 
            command=lambda: self._cambiar_estado_seleccionados(EstadoAsistencia.JUSTIFICADO)
        ).pack(side="left", padx=5)
        
        # Botón de guardar
        tk.Button(
            self.win, text="💾 GUARDAR EN BASE DE DATOS", 
            bg="#34495e", fg="white", font=("bold"), width=30,
            command=self._guardar
        ).pack(pady=10)
        
        # Botón de cerrar sin guardar
        tk.Button(
            self.win, text="✖ CERRAR SIN GUARDAR", 
            bg="#7f8c8d", fg="white", width=20,
            command=self._cerrar_sin_guardar
        ).pack(pady=5)
    
    def _on_doble_click(self, event):
        """Alterna entre Presente/Ausente al hacer doble click."""
        seleccion = self.tree.selection()
        if not seleccion:
            return
        
        for item in seleccion:
            cedula = self.tree.item(item, "values")[0]
            # Buscar estado actual en la planilla
            for reg in self.planilla.registros:
                if reg.id_estudiante == cedula:
                    # Alternar: Presente <-> Ausente
                    if reg.estado == EstadoAsistencia.PRESENTE:
                        nuevo_estado = EstadoAsistencia.AUSENTE
                    else:
                        nuevo_estado = EstadoAsistencia.PRESENTE
                    
                    self.controlador.cambiar_estado(cedula, nuevo_estado)
                    break
        
        self.refrescar()
    
    def _cambiar_estado_seleccionados(self, nuevo_estado: EstadoAsistencia):
        """Cambia el estado de los estudiantes seleccionados."""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Info", "Selecciona al menos un estudiante.")
            return
        
        for item in seleccion:
            cedula = self.tree.item(item, "values")[0]
            
            motivo = None
            if nuevo_estado == EstadoAsistencia.JUSTIFICADO:
                # Obtener nombre del estudiante
                nombre = self.nombres.get(cedula, "Estudiante")
                motivo = simpledialog.askstring(
                    "Motivo", 
                    f"¿Por qué faltó {nombre}?",
                    parent=self.win
                )
                if not motivo:  # Si cancela o deja vacío
                    continue
            
            self.controlador.cambiar_estado(cedula, nuevo_estado, motivo)
        
        self.refrescar()
    
    def refrescar(self):
        """Refresca la tabla con los datos actuales de la planilla."""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insertar datos actualizados
        for reg in self.planilla.registros:
            tag = "presente"
            if reg.estado == EstadoAsistencia.AUSENTE:
                tag = "ausente"
            elif reg.estado == EstadoAsistencia.JUSTIFICADO:
                tag = "justificado"
            
            nombre = self.nombres.get(reg.id_estudiante, "Desconocido")
            self.tree.insert(
                "", "end", 
                values=(reg.id_estudiante, nombre, reg.estado.value), 
                tags=(tag,)
            )
        
        # Actualizar estadísticas
        self._actualizar_estadisticas()
    
    def _actualizar_estadisticas(self):
        """Actualiza las estadísticas en el encabezado."""
        # Encontrar el frame de estadísticas y actualizarlo
        for child in self.win.winfo_children():
            if isinstance(child, tk.Frame) and child.winfo_children():
                for sub_child in child.winfo_children():
                    if isinstance(sub_child, tk.Label) and "Total:" in sub_child.cget("text"):
                        total = len(self.planilla.registros)
                        presentes = sum(1 for r in self.planilla.registros if r.estado == EstadoAsistencia.PRESENTE)
                        ausentes = sum(1 for r in self.planilla.registros if r.estado == EstadoAsistencia.AUSENTE)
                        justificados = sum(1 for r in self.planilla.registros if r.estado == EstadoAsistencia.JUSTIFICADO)
                        
                        sub_child.config(
                            text=f"Total: {total} | Presentes: {presentes} | Ausentes: {ausentes} | Justificados: {justificados}"
                        )
                        break
                break
    
    def _guardar(self):
        """Guarda la planilla en la base de datos."""
        if self.controlador.guardar_planilla():
            messagebox.showinfo(
                "Éxito", 
                f"Se guardó la asistencia de {len(self.planilla.registros)} alumnos."
            )
            self.win.destroy()
    
    def _cerrar_sin_guardar(self):
        """Cierra sin guardar, preguntando primero."""
        resp = messagebox.askyesno(
            "Confirmar", 
            "¿Estás seguro de cerrar sin guardar?\nSe perderán los cambios."
        )
        if resp:
            self.win.destroy()
    
    def mostrar(self):
        """Muestra la ventana."""
        self.win.mainloop()

# ============================================
# PUNTO DE ENTRADA - Interface simplificada
# ============================================
class GestorAsistenciaUI:
    """
    Clase de interfaz simplificada para mantener compatibilidad con el código existente.
    Pero SOLID internamente.
    """
    
    def __init__(self, repo_asistencia, respaldo_emergencia, db_conexion):
        self.controlador = ControladorAsistencia(repo_asistencia, respaldo_emergencia, db_conexion)
    
    def mostrar(self):
        """Muestra la ventana de selección."""
        self.controlador.iniciar_seleccion()