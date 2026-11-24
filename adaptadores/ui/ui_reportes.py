# adaptadores/ui/ui_reportes.py
"""
Adaptador de Interfaz Gráfica para el Módulo de Reportes.
Desacoplado de SQL. Pestañas limpias, alertas rojo/ámbar para < 75%
según Art. 109 RGLOE. Sistema de diseño unificado.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from typing import List, Optional
from tkcalendar import DateEntry

from puertos.repositorio_reportes import PuertoRepositorioReportes, PuertoExportadorPDF
from dominio.reportes import AnalizadorEstadistico, AsistenciaEnriquecida, AlertaRiesgo
from adaptadores.ui.utilidades_ui import (
    centrar_ventana, maximizar_ventana,
    COLOR_FONDO_APP, COLOR_TARJETA, COLOR_PRIMARIO, COLOR_ACENTO,
    COLOR_PELIGRO, COLOR_PELIGRO_HOVER, COLOR_ADVERTENCIA,
    COLOR_TEXTO_PRINCIPAL, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_CLARO,
    COLOR_SEPARADOR, COLOR_ALERTA_RIESGO_BG, COLOR_ALERTA_RIESGO_FG,
    COLOR_SECUNDARIO, COLOR_SECUNDARIO_HOVER,
    FUENTE_TITULO, FUENTE_SUBTITULO, FUENTE_ENCABEZADO,
    FUENTE_CUERPO, FUENTE_CUERPO_BOLD, FUENTE_ETIQUETA,
    FUENTE_PEQUEÑA, FUENTE_PEQUEÑA_BOLD,
    crear_boton, crear_tarjeta, crear_separador,
    crear_treeview_zebra, insertar_fila_zebra,
)


class UIReportes:
    """
    Adaptador de UI para reportes escolares con pestañas para Reporte Diario,
    Mensual e Historial. Resalta alumnos en riesgo legal (< 75.0% Art. 109 RGLOE).
    """

    MESES_NOMBRES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]

    def __init__(self, repo_reportes: PuertoRepositorioReportes,
                 exportador_pdf: PuertoExportadorPDF,
                 parent: Optional[tk.Widget] = None):
        self.repo = repo_reportes
        self.exportador = exportador_pdf

        if parent:
            self.root = tk.Toplevel(parent)
        else:
            try:
                self.root = tk.Toplevel()
            except Exception:
                self.root = tk.Tk()

        self.root.title("Reportes y Estadísticas — Art. 109 RGLOE")
        self.root.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.root, 1100, 750)
        maximizar_ventana(self.root)

        self.contexto_actual = "GENERAL"
        self.info_contexto = ""
        self.registros_actuales: List[AsistenciaEnriquecida] = []
        self._crear_interfaz()

    def _crear_interfaz(self):
        # ═══ ENCABEZADO ═══
        f_header = tk.Frame(self.root, bg=COLOR_PRIMARIO, pady=10)
        f_header.pack(fill="x")
        tk.Label(f_header, text="📊  REPORTES Y ANÁLISIS DE RIESGO (ART. 109 RGLOE)", font=FUENTE_ENCABEZADO, fg=COLOR_TEXTO_CLARO, bg=COLOR_PRIMARIO).pack()

        # Pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, fill="x", padx=15)
        self._crear_pestañas()

        # Tabla de resultados
        self._crear_tabla_resultados()

        # Barra de resumen
        self._crear_barra_resumen()

        # Botones de acción
        self._crear_botones_accion()

    def _crear_pestañas(self):
        # 1. Reporte Diario
        tab_dia = tk.Frame(self.notebook, padx=10, pady=10, bg=COLOR_FONDO_APP)
        self.notebook.add(tab_dia, text="📅 Reporte Diario")
        f1 = tk.Frame(tab_dia, bg=COLOR_FONDO_APP)
        f1.pack(pady=5)
        tk.Label(f1, text="Fecha:", font=FUENTE_ETIQUETA, bg=COLOR_FONDO_APP).pack(side="left", padx=5)
        self.cal_dia = DateEntry(f1, width=14, background='darkblue', foreground='white', date_pattern='yyyy-mm-dd', locale='es_ES', font=FUENTE_CUERPO)
        self.cal_dia.pack(side="left", padx=10)
        crear_boton(f1, "🔍 Buscar por Día", self.buscar_por_dia, COLOR_SECUNDARIO, COLOR_TEXTO_CLARO, COLOR_SECUNDARIO_HOVER).pack(side="left", padx=5)

        # 2. Reporte Mensual
        tab_mes = tk.Frame(self.notebook, padx=10, pady=10, bg=COLOR_FONDO_APP)
        self.notebook.add(tab_mes, text="📆 Reporte Mensual")
        f2 = tk.Frame(tab_mes, bg=COLOR_FONDO_APP)
        f2.pack(pady=5)
        tk.Label(f2, text="Mes:", font=FUENTE_ETIQUETA, bg=COLOR_FONDO_APP).pack(side="left", padx=5)
        self.combo_mes = ttk.Combobox(f2, values=self.MESES_NOMBRES, state="readonly", width=15, font=FUENTE_CUERPO)
        self.combo_mes.pack(side="left", padx=5)
        self.combo_mes.current(date.today().month - 1)
        tk.Label(f2, text="Año:", font=FUENTE_CUERPO, bg=COLOR_FONDO_APP).pack(side="left", padx=5)
        self.entry_anio = tk.Entry(f2, width=8, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_anio.insert(0, str(date.today().year))
        self.entry_anio.pack(side="left", padx=5)
        crear_boton(f2, "🔍 Buscar por Mes", self.buscar_por_mes, COLOR_SECUNDARIO, COLOR_TEXTO_CLARO, COLOR_SECUNDARIO_HOVER).pack(side="left", padx=10)

        # 3. Historial Estudiante
        tab_hist = tk.Frame(self.notebook, padx=10, pady=10, bg=COLOR_FONDO_APP)
        self.notebook.add(tab_hist, text="👤 Historial Estudiante")
        f3 = tk.Frame(tab_hist, bg=COLOR_FONDO_APP)
        f3.pack(pady=5)
        tk.Label(f3, text="Cédula:", font=FUENTE_ETIQUETA, bg=COLOR_FONDO_APP).pack(side="left", padx=5)
        self.entry_cedula = tk.Entry(f3, width=20, font=FUENTE_CUERPO, relief="solid", bd=1)
        self.entry_cedula.pack(side="left", padx=5)
        self.entry_cedula.bind("<Return>", lambda e: self.buscar_por_cedula())
        crear_boton(f3, "🔍 Buscar Historial", self.buscar_por_cedula, COLOR_SECUNDARIO, COLOR_TEXTO_CLARO, COLOR_SECUNDARIO_HOVER).pack(side="left", padx=10)

    def _crear_tabla_resultados(self):
        columnas = ("fecha", "cedula", "nombre", "genero", "materia", "estado", "observacion", "pct_estudiante")
        encabezados = ["Fecha", "Cédula", "Estudiante", "Gen", "Materia", "ST", "Justificación", "% Asist."]
        anchos = [90, 100, 220, 40, 160, 50, 200, 110]
        anclas = ["center", "center", "w", "center", "w", "center", "w", "center"]

        self.tree, frame_tabla = crear_treeview_zebra(self.root, columnas, encabezados, anchos, anclas, alto=15)
        frame_tabla.pack(fill="both", expand=True, padx=15)

    def _crear_barra_resumen(self):
        self.frame_resumen = tk.Frame(self.root, bg="#EAEDED", padx=15, pady=6)
        self.frame_resumen.pack(fill="x", padx=15, pady=4)
        self.lbl_resumen = tk.Label(self.frame_resumen, text="Esperando consulta...", font=FUENTE_PEQUEÑA_BOLD, bg="#EAEDED", fg=COLOR_TEXTO_PRINCIPAL)
        self.lbl_resumen.pack(side="left")

    def _crear_botones_accion(self):
        fb = tk.Frame(self.root, bg=COLOR_FONDO_APP, pady=8)
        fb.pack()
        crear_boton(fb, "⚠️  VER ALERTAS DE RIESGO (< 75%)", self.mostrar_alertas_riesgo, "#D35400", COLOR_TEXTO_CLARO).pack(side="left", padx=15)
        crear_boton(fb, "🖨️  EXPORTAR A PDF", self.generar_pdf, COLOR_PELIGRO, COLOR_TEXTO_CLARO, COLOR_PELIGRO_HOVER).pack(side="left", padx=15)

    def _poblar_tabla(self, registros: List[AsistenciaEnriquecida]):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.registros_actuales = registros

        if not registros:
            self.lbl_resumen.config(text="Sin registros en el lapso consultado.", fg=COLOR_TEXTO_SECUNDARIO)
            messagebox.showinfo("Sin Resultados", "No se encontraron registros para el período consultado.")
            return

        resumenes = AnalizadorEstadistico.generar_resumen_estudiantes(registros)
        mapa_resumen = {r.id_estudiante: r for r in resumenes}
        total_en_riesgo = sum(1 for r in resumenes if r.es_critico)
        demografia = AnalizadorEstadistico.calcular_demografia(registros)

        for reg in registros:
            res_est = mapa_resumen.get(reg.id_estudiante)
            pct_texto = f"{res_est.porcentaje_asistencia:.1f}%" if res_est else "-"
            tag = "alerta_riesgo" if (res_est and res_est.es_critico) else "regular"
            self.tree.insert("", "end", values=(
                reg.fecha, reg.id_estudiante, reg.nombre, reg.genero,
                reg.materia or "-", reg.estado, reg.observacion or "-", pct_texto,
            ), tags=(tag,))

        total_regs = len(registros)
        efectivas = (demografia["masculino_presente"] + demografia["masculino_justificado"] +
                     demografia["femenino_presente"] + demografia["femenino_justificado"])
        faltas = demografia["masculino_ausente"] + demografia["femenino_ausente"]
        texto = (f"Total: {total_regs} | Asistencias (P+J): {efectivas} | "
                 f"Faltas (A): {faltas} | En Riesgo (< 75%): {total_en_riesgo}")
        color = "#900C3F" if total_en_riesgo > 0 else "#196F3D"
        self.lbl_resumen.config(text=texto, fg=color)

    def buscar_por_dia(self):
        fecha_str = self.cal_dia.get_date().strftime('%Y-%m-%d')
        self.contexto_actual = f"DIARIO_{fecha_str}"
        self.info_contexto = f"Fecha: {fecha_str}"
        self._poblar_tabla(self.repo.obtener_asistencia_por_fecha(fecha_str))

    def buscar_por_mes(self):
        mes_idx = self.combo_mes.current() + 1
        mes_str = f"{mes_idx:02d}"
        anio_str = self.entry_anio.get().strip()
        self.contexto_actual = f"MENSUAL_{self.combo_mes.get().upper()}_{anio_str or 'TODOS'}"
        self.info_contexto = f"Mes: {self.combo_mes.get()} {anio_str}".strip()
        self._poblar_tabla(self.repo.obtener_asistencia_por_mes(mes_str, anio_str))

    def buscar_por_cedula(self):
        ced = self.entry_cedula.get().strip()
        if not ced:
            messagebox.showwarning("Campo Vacío", "Ingrese una cédula o identificador.")
            return
        self.contexto_actual = f"HISTORIAL_{ced}"
        self.info_contexto = f"Estudiante: {ced}"
        self._poblar_tabla(self.repo.obtener_historial_estudiante(ced))

    def mostrar_alertas_riesgo(self):
        if not self.registros_actuales:
            messagebox.showinfo("Información", "Primero realice una búsqueda.")
            return

        alertas = AnalizadorEstadistico.detectar_riesgo(self.registros_actuales)
        win = tk.Toplevel(self.root)
        win.title("Alertas de Riesgo — Art. 109 RGLOE")
        win.config(bg=COLOR_FONDO_APP)
        centrar_ventana(win, 800, 500)

        tk.Label(win, text="⚠️  ALUMNOS EN RIESGO DE REPROBACIÓN (< 75%)", font=FUENTE_SUBTITULO, fg=COLOR_PELIGRO, bg=COLOR_FONDO_APP, pady=10).pack()

        if not alertas:
            tk.Label(win, text="✅ ¡No hay alumnos en riesgo en este grupo de registros!", font=FUENTE_CUERPO, fg=COLOR_ACENTO, bg=COLOR_FONDO_APP, pady=20).pack()
            return

        cols = ("cedula", "nombre", "total", "efectivas", "faltas", "pct", "estado")
        enc = ["Cédula", "Estudiante", "Total", "Asist. (P+J)", "Faltas (A)", "% Asist.", "Condición"]
        anch = [90, 200, 80, 80, 80, 90, 110]
        anclas = ["center", "w", "center", "center", "center", "center", "center"]

        tr, fr = crear_treeview_zebra(win, cols, enc, anch, anclas, alto=12)
        fr.pack(fill="both", expand=True, padx=15, pady=10)

        for a in alertas:
            tr.insert("", "end", values=(
                a.id_estudiante, a.nombre, a.total_clases, a.asistencias_efectivas,
                a.faltas_injustificadas, f"{a.porcentaje_asistencia:.1f}%", "EN RIESGO",
            ), tags=("alerta_riesgo",))

    def generar_pdf(self):
        if not self.registros_actuales:
            messagebox.showwarning("Sin Datos", "Primero realice una búsqueda antes de exportar.")
            return
        nombre_sugerido = f"Reporte_{self.contexto_actual}.pdf".replace(" ", "_")
        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=nombre_sugerido)
        if not ruta:
            return
        try:
            encabezados = ["Fecha", "Cédula", "Estudiante", "Gen", "Materia", "ST", "Justificación", "% Asist."]
            datos_filas = [[str(v) for v in self.tree.item(item)['values']] for item in self.tree.get_children()]
            titulo = f"REPORTE DE ASISTENCIA: {self.contexto_actual.replace('_', ' ')}"
            if self.exportador.exportar_tabla(titulo, encabezados, datos_filas, ruta):
                messagebox.showinfo("Éxito", f"Reporte PDF generado en:\n{ruta}")
            else:
                messagebox.showerror("Error", "No se pudo generar el PDF.")
        except Exception as error:
            messagebox.showerror("Error", f"Fallo al exportar: {error}")


# Alias
GestorReportesUI = UIReportes
