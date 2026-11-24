# adaptadores/ui/ui_asistencia.py
"""
Adaptador de Interfaz Gráfica para Pase de Lista de Asistencia.
DESACOPLADO de SQL: toda consulta de clases/estudiantes se delega
al RepositorioClase inyectado (FASE 1 - Corrección Hexagonal).

Flujo intuitivo: seleccionar clase/fecha → marcar P/A/J con colores →
modal para justificaciones → indicador visual del respaldo anti-apagones.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
from typing import Dict, Optional, List

from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia
from adaptadores.ui.utilidades_ui import (
    centrar_ventana, maximizar_ventana,
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_ACENTO,
    COLOR_ACENTO_HOVER, COLOR_PELIGRO, COLOR_ADVERTENCIA,
    COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_CLARO,
    COLOR_SEPARADOR, COLOR_BORDE_TARJETA,
    FUENTE_TITULO, FUENTE_SUBTITULO, FUENTE_ENCABEZADO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_ETIQUETA,
    FUENTE_PEQUEÑA, FUENTE_PEQUEÑA_BOLD, FUENTE_BOTON,
    crear_boton, crear_tarjeta, crear_separador,
    crear_treeview_zebra, insertar_fila_zebra,
    configurar_ventana_hija, restaurar_foco, agregar_barra_superior_volver,
)


# ============================================
# CONTROLADOR (orquesta UI ↔ Dominio)
# ============================================
class ControladorAsistencia:
    """Controlador MVC que orquesta la interacción entre UI y dominio."""

    def __init__(self, repo_asistencia, respaldo_emergencia, repo_clase, parent=None):
        self.repo = repo_asistencia
        self.respaldo = respaldo_emergencia
        self.repo_clase = repo_clase  # ← Inyección hexagonal (ya no SQL directo)
        self.parent = parent

        self.planilla_actual: Optional[PlanillaAsistencia] = None
        self.nombres_estudiantes: Dict[str, str] = {}

    def obtener_clases_disponibles(self) -> List[tuple]:
        """Obtiene las clases a través del repositorio (sin SQL)."""
        return self.repo_clase.obtener_clases_disponibles()

    def iniciar_seleccion(self, parent=None):
        """Inicia el proceso de selección de clase."""
        if parent:
            self.parent = parent
        datos = self.obtener_clases_disponibles()
        if not datos:
            messagebox.showerror("Error", "No hay clases disponibles en el sistema.", parent=self.parent)
            if self.parent:
                restaurar_foco(self.parent)
            return
        ids = [d[0] for d in datos]
        nombres = [d[1] for d in datos]
        SelectorClaseUI(self, nombres, ids, parent=self.parent).mostrar()

    def preparar_planilla(self, id_clase: int, fecha_str: str, nombre_clase: str):
        """Prepara la planilla antes de mostrar."""
        planilla_recuperada = self.respaldo.recuperar_respaldo(id_clase, fecha_str)

        if planilla_recuperada:
            resp = messagebox.askyesno(
                "Recuperación",
                "¡ATENCIÓN! Se encontró una lista sin guardar del apagón.\n"
                "¿Deseas recuperar lo que llevabas?",
                parent=self.parent
            )
            if self.parent:
                restaurar_foco(self.parent)
            if resp:
                self.planilla_actual = planilla_recuperada
                ids = [reg.id_estudiante for reg in self.planilla_actual.registros]
                self.nombres_estudiantes = self.repo_clase.obtener_nombres_estudiantes(ids)
            else:
                self.respaldo.limpiar_respaldo()
                self._crear_planilla_nueva(id_clase, fecha_str)
        else:
            self._crear_planilla_nueva(id_clase, fecha_str)

        PlanillaUI(self, self.planilla_actual, self.nombres_estudiantes, nombre_clase, parent=self.parent).mostrar()

    def _crear_planilla_nueva(self, id_clase: int, fecha_str: str):
        """Crea planilla consultando estudiantes a través del repositorio."""
        estudiantes = self.repo_clase.obtener_estudiantes_por_clase(id_clase)
        self.planilla_actual = PlanillaAsistencia(id_clase=id_clase, fecha=fecha_str)
        self.nombres_estudiantes = {}
        for id_est, nombre in estudiantes:
            self.planilla_actual.registros.append(RegistroAsistencia(id_estudiante=id_est))
            self.nombres_estudiantes[id_est] = nombre

    def cambiar_estado(self, id_estudiante: str, nuevo_estado: EstadoAsistencia, motivo: Optional[str] = None):
        if not self.planilla_actual:
            return False
        self.planilla_actual.actualizar_registro(id_estudiante, nuevo_estado, motivo)
        self.respaldo.guardar_respaldo(self.planilla_actual)
        return True

    def guardar_planilla(self):
        if not self.planilla_actual or not self.planilla_actual.registros:
            return False
        try:
            self.repo.guardar_planilla(self.planilla_actual)
            self.respaldo.limpiar_respaldo()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}", parent=self.parent)
            if self.parent:
                restaurar_foco(self.parent)
            return False


# ============================================
# UI: Selector de Clase
# ============================================
class SelectorClaseUI:
    """Vista para seleccionar clase y fecha."""

    def __init__(self, controlador: ControladorAsistencia, clases: List[str], ids: List[int], parent=None):
        self.controlador = controlador
        self.clases = clases
        self.ids = ids

        self.root = tk.Toplevel(parent) if parent else tk.Toplevel()
        self.root.title("Seleccionar Clase — Pase de Lista")
        self.root.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.root, 550, 380)
        configurar_ventana_hija(self.root, parent, es_modal=True)
        agregar_barra_superior_volver(self.root, parent, "Asistencia")

    def mostrar(self):
        contenedor = tk.Frame(self.root, bg=COLOR_FONDO_APP)
        contenedor.pack(expand=True, fill="both", padx=30, pady=20)

        tarjeta = crear_tarjeta(contenedor, padx=30, pady=25)
        tarjeta.pack(expand=True, fill="both")

        tk.Label(tarjeta, text="📋  SELECCIÓN DE CLASE", font=FUENTE_SUBTITULO, bg=COLOR_TARJETA, fg=COLOR_PRIMARIO).pack(pady=(0, 15))
        crear_separador(tarjeta).pack(fill="x", pady=(0, 15))

        tk.Label(tarjeta, text="Clase / Materia:", font=FUENTE_ETIQUETA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL).pack(anchor="w")
        self.combo_clases = ttk.Combobox(tarjeta, width=50, state="readonly", values=self.clases, font=FUENTE_CUERPO)
        self.combo_clases.pack(fill="x", pady=(4, 15))
        if self.clases:
            self.combo_clases.current(0)

        tk.Label(tarjeta, text="Fecha de Asistencia:", font=FUENTE_ETIQUETA, bg=COLOR_TARJETA, fg=COLOR_TEXTO_PRINCIPAL).pack(anchor="w")
        self.cal_fecha = DateEntry(
            tarjeta, width=20, background='darkblue', foreground='white',
            borderwidth=2, date_pattern='yyyy-mm-dd', locale='es_ES',
            font=FUENTE_CUERPO,
        )
        self.cal_fecha.pack(anchor="w", pady=(4, 20))

        crear_boton(tarjeta, "COMENZAR CLASE  ▶", self._on_comenzar, COLOR_ACENTO, COLOR_TEXTO_CLARO, COLOR_ACENTO_HOVER).pack(fill="x", ipady=4)
        self.root.mainloop()

    def _on_comenzar(self):
        idx = self.combo_clases.current()
        if idx == -1:
            return
        id_clase = self.ids[idx]
        nombre_clase = self.combo_clases.get()
        fecha_str = self.cal_fecha.get_date().strftime("%Y-%m-%d")
        self.root.destroy()
        self.controlador.preparar_planilla(id_clase, fecha_str, nombre_clase)


# ============================================
# UI: Planilla de Asistencia
# ============================================
class PlanillaUI:
    """Vista para mostrar y editar la planilla de asistencia."""

    def __init__(self, controlador: ControladorAsistencia, planilla: PlanillaAsistencia,
                 nombres: Dict[str, str], nombre_clase: str, parent=None):
        self.controlador = controlador
        self.planilla = planilla
        self.nombres = nombres
        self.nombre_clase = nombre_clase

        self.win = tk.Toplevel(parent) if parent else tk.Toplevel()
        self.win.title("Planilla de Asistencia — Pase de Lista")
        self.win.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.win, 900, 650)
        configurar_ventana_hija(self.win, parent)
        agregar_barra_superior_volver(self.win, parent, f"Planilla: {nombre_clase}")
        maximizar_ventana(self.win)

        self.tree = None
        self.lbl_stats = None
        self.lbl_respaldo = None
        self._crear_interfaz()

    def _crear_interfaz(self):
        self._crear_encabezado()
        self._crear_tabla()
        self._crear_botones()
        self.refrescar()

    def _crear_encabezado(self):
        f_head = tk.Frame(self.win, bg=COLOR_PRIMARIO, pady=10)
        f_head.pack(fill="x")

        tk.Label(f_head, text=f"📋  {self.nombre_clase}", font=FUENTE_ENCABEZADO, fg=COLOR_TEXTO_CLARO, bg=COLOR_PRIMARIO).pack()
        tk.Label(f_head, text=f"Fecha: {self.planilla.fecha}", font=FUENTE_PEQUEÑA_BOLD, fg="#BDC3C7", bg=COLOR_PRIMARIO).pack()

        # Estadísticas
        self.lbl_stats = tk.Label(f_head, text="", font=FUENTE_PEQUEÑA, fg=COLOR_TEXTO_CLARO, bg=COLOR_PRIMARIO)
        self.lbl_stats.pack()

        # Indicador de respaldo anti-apagones
        self.lbl_respaldo = tk.Label(
            f_head, text="💾 Respaldo automático activo", font=FUENTE_PEQUEÑA,
            fg="#2ECC71", bg=COLOR_PRIMARIO,
        )
        self.lbl_respaldo.pack()

    def _crear_tabla(self):
        cols = ("id", "nom", "st")
        encabezados = ["Cédula", "Estudiante", "Estado"]
        anchos = [120, 450, 100]
        anclas = ["center", "w", "center"]

        self.tree, frame_tree = crear_treeview_zebra(self.win, cols, encabezados, anchos, anclas, alto=15)
        frame_tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree.bind("<Double-Button-1>", self._on_doble_click)

    def _crear_botones(self):
        fb = tk.Frame(self.win, bg=COLOR_FONDO_APP, pady=8)
        fb.pack()

        crear_boton(fb, "✅ PRESENTE", lambda: self._cambiar_seleccionados(EstadoAsistencia.PRESENTE), COLOR_ACENTO, COLOR_TEXTO_CLARO).pack(side="left", padx=6)
        crear_boton(fb, "❌ AUSENTE", lambda: self._cambiar_seleccionados(EstadoAsistencia.AUSENTE), COLOR_PELIGRO, COLOR_TEXTO_CLARO).pack(side="left", padx=6)
        crear_boton(fb, "⚠️ JUSTIFICADA", lambda: self._cambiar_seleccionados(EstadoAsistencia.JUSTIFICADO), COLOR_ADVERTENCIA, COLOR_TEXTO_CLARO).pack(side="left", padx=6)

        f_acciones = tk.Frame(self.win, bg=COLOR_FONDO_APP, pady=4)
        f_acciones.pack()

        crear_boton(f_acciones, "💾  GUARDAR EN BASE DE DATOS", self._guardar, COLOR_PRIMARIO, COLOR_TEXTO_CLARO, ancho=35).pack(side="left", padx=8, ipady=4)
        crear_boton(f_acciones, "✖  CERRAR SIN GUARDAR", self._cerrar_sin_guardar, "#7F8C8D", COLOR_TEXTO_CLARO).pack(side="left", padx=8)

    def _on_doble_click(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        for item in seleccion:
            cedula = self.tree.item(item, "values")[0]
            for reg in self.planilla.registros:
                if reg.id_estudiante == cedula:
                    nuevo = EstadoAsistencia.AUSENTE if reg.estado == EstadoAsistencia.PRESENTE else EstadoAsistencia.PRESENTE
                    self.controlador.cambiar_estado(cedula, nuevo)
                    break
        self.refrescar()

    def _cambiar_seleccionados(self, nuevo_estado: EstadoAsistencia):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Info", "Selecciona al menos un estudiante.", parent=self.win)
            restaurar_foco(self.win)
            return
        for item in seleccion:
            cedula = self.tree.item(item, "values")[0]
            motivo = None
            if nuevo_estado == EstadoAsistencia.JUSTIFICADO:
                nombre = self.nombres.get(cedula, "Estudiante")
                motivo = simpledialog.askstring("Motivo", f"¿Por qué faltó {nombre}?", parent=self.win)
                restaurar_foco(self.win)
                if not motivo:
                    continue
            self.controlador.cambiar_estado(cedula, nuevo_estado, motivo)
        self.refrescar()

    def refrescar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for reg in self.planilla.registros:
            tag = "presente" if reg.estado == EstadoAsistencia.PRESENTE else ("ausente" if reg.estado == EstadoAsistencia.AUSENTE else "justificado")
            nombre = self.nombres.get(reg.id_estudiante, "Desconocido")
            self.tree.insert("", "end", values=(reg.id_estudiante, nombre, reg.estado.value), tags=(tag,))

        # Actualizar estadísticas
        total = len(self.planilla.registros)
        p = sum(1 for r in self.planilla.registros if r.estado == EstadoAsistencia.PRESENTE)
        a = sum(1 for r in self.planilla.registros if r.estado == EstadoAsistencia.AUSENTE)
        j = sum(1 for r in self.planilla.registros if r.estado == EstadoAsistencia.JUSTIFICADO)
        if self.lbl_stats:
            self.lbl_stats.config(text=f"Total: {total}  |  ✅ Presentes: {p}  |  ❌ Ausentes: {a}  |  ⚠️ Justificados: {j}")

    def _guardar(self):
        if self.controlador.guardar_planilla():
            messagebox.showinfo("Éxito", f"Se guardó la asistencia de {len(self.planilla.registros)} alumnos.", parent=self.win)
            restaurar_foco(self.win)
            self.win.destroy()

    def _cerrar_sin_guardar(self):
        if messagebox.askyesno("Confirmar", "¿Cerrar sin guardar? Se perderán los cambios.", parent=self.win):
            self.win.destroy()
        else:
            restaurar_foco(self.win)

    def mostrar(self):
        self.win.mainloop()


# ============================================
# PUNTO DE ENTRADA
# ============================================
class GestorAsistenciaUI:
    """Clase de interfaz simplificada para compatibilidad con main.py."""

    def __init__(self, repo_asistencia, respaldo_emergencia, repo_clase_o_conexion, parent=None):
        # Soporte defensivo: si se pasa una instancia de ConexionBD, se adapta con SQLiteRepositorioClase
        if hasattr(repo_clase_o_conexion, "conectar"):
            from adaptadores.db.sqlite_clase import SQLiteRepositorioClase
            repo_clase = SQLiteRepositorioClase(repo_clase_o_conexion)
        else:
            repo_clase = repo_clase_o_conexion

        self.controlador = ControladorAsistencia(repo_asistencia, respaldo_emergencia, repo_clase, parent=parent)

    def mostrar(self, parent=None):
        self.controlador.iniciar_seleccion(parent=parent)
