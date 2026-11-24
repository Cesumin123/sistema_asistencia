# adaptadores/ui/ui_reportes.py
"""
Adaptador de Interfaz Gráfica (Tkinter/ttk) para el Módulo de Reportes.
Completamente desacoplado de SQL: interactúa exclusivamente con el dominio
y los puertos de repositorio y exportador PDF.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from typing import List, Optional
from tkcalendar import DateEntry

from puertos.repositorio_reportes import PuertoRepositorioReportes, PuertoExportadorPDF
from dominio.reportes import AnalizadorEstadistico, AsistenciaEnriquecida, AlertaRiesgo


class UIReportes:
    """
    Adaptador de UI para generación y visualización de reportes escolares.
    Soporta pestañas para Reporte Diario, Reporte Mensual e Historial de Estudiante.
    Resalta alumnos en riesgo legal (< 75.0% según Art. 109 RGLOE) y exporta a PDF.
    """

    MESES_NOMBRES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    def __init__(
        self,
        repo_reportes: PuertoRepositorioReportes,
        exportador_pdf: PuertoExportadorPDF,
        parent: Optional[tk.Widget] = None
    ):
        self.repo = repo_reportes
        self.exportador = exportador_pdf

        if parent:
            self.root = tk.Toplevel(parent)
        else:
            try:
                self.root = tk.Toplevel()
            except Exception:
                self.root = tk.Tk()

        self.root.title("Gestor Profesional de Reportes y Estadísticas (Hexagonal)")
        self.root.geometry("1100x750")
        try:
            self.root.state('zoomed')
        except Exception:
            pass

        # Variables de contexto para reportes
        self.contexto_actual = "GENERAL"
        self.info_contexto = ""
        self.registros_actuales: List[AsistenciaEnriquecida] = []

        self._crear_interfaz()

    def _crear_interfaz(self):
        """Construye todos los componentes visuales."""
        # Título superior
        frame_titulo = tk.Frame(self.root, bg="#2c3e50", pady=10)
        frame_titulo.pack(fill="x")
        tk.Label(
            frame_titulo,
            text="SISTEMA DE ASISTENCIA — REPORTES Y ANÁLISIS DE RIESGO (ART. 109 RGLOE)",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#2c3e50"
        ).pack()

        # Cuaderno de pestañas de filtrado
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, fill="x", padx=15)

        self._crear_pestañas()
        self._crear_tabla_resultados()
        self._crear_barra_resumen()
        self._crear_botones_accion()

    def _crear_pestañas(self):
        """Crea las pestañas de Reporte Diario, Mensual e Historial."""
        # 1. Pestaña: Reporte Diario
        tab_dia = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(tab_dia, text="📅 Reporte Diario")
        
        f1 = tk.Frame(tab_dia)
        f1.pack(pady=5)
        tk.Label(f1, text="Seleccione Fecha (AAAA-MM-DD):", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.cal_dia = DateEntry(
            f1, width=14, background='darkblue', foreground='white',
            date_pattern='yyyy-mm-dd', locale='es_ES'
        )
        self.cal_dia.pack(side="left", padx=10)
        tk.Button(
            f1, text="🔍 Buscar por Día", bg="#2980b9", fg="white", font=("Arial", 9, "bold"),
            cursor="hand2", command=self.buscar_por_dia
        ).pack(side="left", padx=5)

        # 2. Pestaña: Reporte Mensual
        tab_mes = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(tab_mes, text="📆 Reporte Mensual")
        
        f2 = tk.Frame(tab_mes)
        f2.pack(pady=5)
        tk.Label(f2, text="Mes:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.combo_mes = ttk.Combobox(f2, values=self.MESES_NOMBRES, state="readonly", width=15)
        self.combo_mes.pack(side="left", padx=5)
        # Seleccionar mes actual por defecto
        mes_actual_idx = date.today().month - 1
        self.combo_mes.current(mes_actual_idx)

        tk.Label(f2, text="Año (opcional):", font=("Arial", 10)).pack(side="left", padx=5)
        self.entry_anio = tk.Entry(f2, width=8)
        self.entry_anio.insert(0, str(date.today().year))
        self.entry_anio.pack(side="left", padx=5)

        tk.Button(
            f2, text="🔍 Buscar por Mes", bg="#2980b9", fg="white", font=("Arial", 9, "bold"),
            cursor="hand2", command=self.buscar_por_mes
        ).pack(side="left", padx=10)

        # 3. Pestaña: Historial Estudiante
        tab_hist = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(tab_hist, text="👤 Historial Estudiante")
        
        f3 = tk.Frame(tab_hist)
        f3.pack(pady=5)
        tk.Label(f3, text="Cédula / Identificador:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.entry_cedula = tk.Entry(f3, width=20)
        self.entry_cedula.pack(side="left", padx=5)
        self.entry_cedula.bind("<Return>", lambda e: self.buscar_por_cedula())

        tk.Button(
            f3, text="🔍 Buscar Historial", bg="#2980b9", fg="white", font=("Arial", 9, "bold"),
            cursor="hand2", command=self.buscar_por_cedula
        ).pack(side="left", padx=10)

    def _crear_tabla_resultados(self):
        """Crea el Treeview para visualizar los datos."""
        frame_tabla = tk.Frame(self.root, padx=15)
        frame_tabla.pack(fill="both", expand=True)

        columnas = ("fecha", "cedula", "nombre", "genero", "materia", "estado", "observacion", "pct_estudiante")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15)

        self.tree.heading("fecha", text="Fecha")
        self.tree.column("fecha", width=90, anchor="center")
        self.tree.heading("cedula", text="Cédula")
        self.tree.column("cedula", width=100, anchor="center")
        self.tree.heading("nombre", text="Estudiante")
        self.tree.column("nombre", width=220, anchor="w")
        self.tree.heading("genero", text="Gen")
        self.tree.column("genero", width=40, anchor="center")
        self.tree.heading("materia", text="Materia")
        self.tree.column("materia", width=160, anchor="w")
        self.tree.heading("estado", text="ST")
        self.tree.column("estado", width=50, anchor="center")
        self.tree.heading("observacion", text="Motivo / Justificación")
        self.tree.column("observacion", width=200, anchor="w")
        self.tree.heading("pct_estudiante", text="% Asist. Efectiva")
        self.tree.column("pct_estudiante", width=110, anchor="center")

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Configuración de estilos y etiquetas de color para riesgo < 75.0%
        # Rojo suave / ámbar para filas de estudiantes en riesgo
        self.tree.tag_configure("alerta_riesgo", background="#fadbd8", foreground="#78281f")
        self.tree.tag_configure("regular", background="#ffffff", foreground="#17202a")

    def _crear_barra_resumen(self):
        """Barra de estado inferior que muestra métricas demográficas y de riesgo."""
        self.frame_resumen = tk.Frame(self.root, bg="#eaeded", padx=15, pady=6)
        self.frame_resumen.pack(fill="x", padx=15, pady=4)

        self.lbl_resumen = tk.Label(
            self.frame_resumen,
            text="Esperando consulta... Seleccione un criterio y presione 'Buscar'.",
            font=("Arial", 9, "bold"),
            bg="#eaeded",
            fg="#2c3e50"
        )
        self.lbl_resumen.pack(side="left")

    def _crear_botones_accion(self):
        """Botones inferiores para ver alertas de riesgo y exportar a PDF."""
        frame_botones = tk.Frame(self.root, pady=10)
        frame_botones.pack()

        tk.Button(
            frame_botones,
            text="⚠️ VER ALERTAS DE RIESGO (< 75% Art. 109)",
            bg="#d35400",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            command=self.mostrar_alertas_riesgo
        ).pack(side="left", padx=15)

        tk.Button(
            frame_botones,
            text="🖨️ EXPORTAR A PDF",
            bg="#c0392b",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            command=self.generar_pdf
        ).pack(side="left", padx=15)

    def _poblar_tabla(self, registros: List[AsistenciaEnriquecida]):
        """
        Limpia y llena la tabla con los registros obtenidos.
        Calcula el porcentaje de asistencia de cada estudiante y resalta en rojo/ámbar
        aquellas filas donde el porcentaje de asistencia efectiva sea < 75.0%.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.registros_actuales = registros

        if not registros:
            self.lbl_resumen.config(
                text="Sin registros en el lapso consultado.",
                fg="#7f8c8d"
            )
            messagebox.showinfo(
                "Sin Resultados",
                "No se encontraron registros de asistencia para el período consultado."
            )
            return

        # Calcular métricas individuales a través del servicio de dominio
        resumenes = AnalizadorEstadistico.generar_resumen_estudiantes(registros)
        mapa_resumen = {r.id_estudiante: r for r in resumenes}

        total_en_riesgo = sum(1 for r in resumenes if r.es_critico)
        demografia = AnalizadorEstadistico.calcular_demografia(registros)

        for reg in registros:
            res_est = mapa_resumen.get(reg.id_estudiante)
            pct_texto = f"{res_est.porcentaje_asistencia:.1f}%" if res_est else "-"
            
            # Resaltado visual en rojo/ámbar si < 75.0%
            tag = "alerta_riesgo" if (res_est and res_est.es_critico) else "regular"

            valores = (
                reg.fecha,
                reg.id_estudiante,
                reg.nombre,
                reg.genero,
                reg.materia or "-",
                reg.estado,
                reg.observacion or "-",
                pct_texto
            )
            self.tree.insert("", "end", values=valores, tags=(tag,))

        # Actualizar texto de la barra de resumen
        total_regs = len(registros)
        efectivas = (
            demografia["masculino_presente"] + demografia["masculino_justificado"] +
            demografia["femenino_presente"] + demografia["femenino_justificado"]
        )
        faltas = demografia["masculino_ausente"] + demografia["femenino_ausente"]
        
        texto_resumen = (
            f"Total Registros: {total_regs} | "
            f"Asistencias Efectivas (P+J): {efectivas} | "
            f"Faltas Injustificadas (A): {faltas} | "
            f"Estudiantes en Riesgo (< 75% Art. 109): {total_en_riesgo}"
        )
        color_texto = "#900C3F" if total_en_riesgo > 0 else "#196f3d"
        self.lbl_resumen.config(text=texto_resumen, fg=color_texto)

    def buscar_por_dia(self):
        """Consulta asistencias para la fecha seleccionada."""
        fecha_obj = self.cal_dia.get_date()
        fecha_str = fecha_obj.strftime('%Y-%m-%d')
        
        self.contexto_actual = f"DIARIO_{fecha_str}"
        self.info_contexto = f"Fecha: {fecha_str}"
        
        registros = self.repo.obtener_asistencia_por_fecha(fecha_str)
        self._poblar_tabla(registros)

    def buscar_por_mes(self):
        """Consulta asistencias para el mes y año seleccionados."""
        mes_idx = self.combo_mes.current() + 1
        mes_str = f"{mes_idx:02d}"
        mes_nombre = self.combo_mes.get()
        anio_str = self.entry_anio.get().strip()

        self.contexto_actual = f"MENSUAL_{mes_nombre.upper()}_{anio_str or 'TODOS'}"
        self.info_contexto = f"Mes: {mes_nombre} {anio_str}".strip()

        registros = self.repo.obtener_asistencia_por_mes(mes_str, anio_str)
        self._poblar_tabla(registros)

    def buscar_por_cedula(self):
        """Consulta historial completo de un estudiante."""
        ced = self.entry_cedula.get().strip()
        if not ced:
            messagebox.showwarning("Campo Vacío", "Por favor ingrese una cédula o identificador.")
            return

        self.contexto_actual = f"HISTORIAL_{ced}"
        self.info_contexto = f"Estudiante: {ced}"

        registros = self.repo.obtener_historial_estudiante(ced)
        self._poblar_tabla(registros)

    def mostrar_alertas_riesgo(self):
        """
        Abre una ventana modal con los estudiantes en riesgo (< 75.0% Art. 109 RGLOE)
        según los registros de la consulta actual.
        """
        if not self.registros_actuales:
            messagebox.showinfo("Información", "Primero realice una búsqueda para analizar alertas de riesgo.")
            return

        alertas = AnalizadorEstadistico.detectar_riesgo(self.registros_actuales)

        win = tk.Toplevel(self.root)
        win.title("Alertas de Riesgo Legal de Asistencia (Art. 109 RGLOE)")
        win.geometry("750x450")

        tk.Label(
            win,
            text="ALUMNOS EN RIESGO DE REPROBACIÓN (< 75% DE ASISTENCIA EFECTIVA)",
            font=("Arial", 11, "bold"),
            fg="#900C3F",
            pady=10
        ).pack()

        if not alertas:
            tk.Label(
                win,
                text="✅ ¡Excelente! No hay alumnos en riesgo legal en este grupo de registros.",
                font=("Arial", 10, "italic"),
                fg="green",
                pady=20
            ).pack()
            return

        cols = ("cedula", "nombre", "total", "efectivas", "faltas", "pct", "estado")
        tr = ttk.Treeview(win, columns=cols, show="headings", height=12)
        tr.heading("cedula", text="Cédula"); tr.column("cedula", width=90, anchor="center")
        tr.heading("nombre", text="Estudiante"); tr.column("nombre", width=200, anchor="w")
        tr.heading("total", text="Total Clases"); tr.column("total", width=80, anchor="center")
        tr.heading("efectivas", text="Asist. (P+J)"); tr.column("efectivas", width=80, anchor="center")
        tr.heading("faltas", text="Faltas (A)"); tr.column("faltas", width=80, anchor="center")
        tr.heading("pct", text="% Asistencia"); tr.column("pct", width=90, anchor="center")
        tr.heading("estado", text="Condición"); tr.column("estado", width=110, anchor="center")

        tr.tag_configure("critico", background="#f9d5d5", foreground="#78281f")

        for a in alertas:
            tr.insert(
                "", "end",
                values=(
                    a.id_estudiante,
                    a.nombre,
                    a.total_clases,
                    a.asistencias_efectivas,
                    a.faltas_injustificadas,
                    f"{a.porcentaje_asistencia:.1f}%",
                    "EN RIESGO"
                ),
                tags=("critico",)
            )

        tr.pack(fill="both", expand=True, padx=15, pady=10)

    def generar_pdf(self):
        """Exporta la vista actual a un archivo PDF mediante el adaptador de ReportLab."""
        if not self.registros_actuales:
            messagebox.showwarning("Sin Datos", "Primero realice una búsqueda antes de exportar.")
            return

        nombre_sugerido = f"Reporte_{self.contexto_actual}.pdf".replace(" ", "_")
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documentos PDF", "*.pdf")],
            initialfile=nombre_sugerido
        )

        if not ruta:
            return

        try:
            encabezados = ["Fecha", "Cédula", "Estudiante", "Gen", "Materia", "ST", "Justificación", "% Asist."]
            
            # Obtener datos formateados
            datos_filas = []
            for item in self.tree.get_children():
                vals = self.tree.item(item)['values']
                fila = [str(v) for v in vals]
                datos_filas.append(fila)

            titulo = f"REPORTE DE ASISTENCIA: {self.contexto_actual.replace('_', ' ')}"
            exito = self.exportador.exportar_tabla(titulo, encabezados, datos_filas, ruta)

            if exito:
                messagebox.showinfo("Éxito", f"Reporte PDF generado exitosamente en:\n{ruta}")
            else:
                messagebox.showerror("Error", "No se pudo generar el documento PDF.")

        except Exception as error:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al exportar: {error}")


# Alias para retrocompatibilidad
GestorReportesUI = UIReportes
