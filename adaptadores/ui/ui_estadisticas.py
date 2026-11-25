# adaptadores/ui/ui_estadisticas.py
"""
Adaptador de Interfaz Gráfica para el Módulo de Estadísticas Institucionales.
Construido exclusivamente con Tkinter/ttk y tk.Canvas puro (sin matplotlib/pandas/numpy,
cumpliendo RNF-02) y desacoplado de SQLite.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from puertos.repositorio_estadisticas import PuertoRepositorioEstadisticas
from puertos.repositorio_reportes import PuertoExportadorPDF
from dominio.estadisticas import ResumenEstadisticoGeneral, CalculadoraEstadisticas
from adaptadores.ui.utilidades_ui import (
    centrar_ventana,
    maximizar_ventana,
    configurar_ventana_hija,
    agregar_barra_superior_volver,
    restaurar_foco,
    abrir_archivo_sistema,
    COLOR_FONDO_APP,
    COLOR_TARJETA,
    COLOR_BORDE_TARJETA,
    COLOR_PRIMARIO,
    COLOR_SECUNDARIO,
    COLOR_SECUNDARIO_HOVER,
    COLOR_ACENTO,
    COLOR_ADVERTENCIA,
    COLOR_PELIGRO,
    COLOR_PELIGRO_HOVER,
    COLOR_TEXTO_PRINCIPAL,
    COLOR_TEXTO_SECUNDARIO,
    COLOR_TEXTO_CLARO,
    FUENTE_TITULO,
    FUENTE_ENCABEZADO,
    FUENTE_CUERPO,
    FUENTE_CUERPO_BOLD,
    FUENTE_PEQUEÑA,
    FUENTE_PEQUEÑA_BOLD,
    crear_boton,
    crear_tarjeta,
    crear_treeview_zebra,
    AyudaVisual,
)


class UIEstadisticas:
    """Tablero liviano de indicadores institucionales y gráficos en tk.Canvas puro."""

    def __init__(
        self,
        repo_estadisticas: PuertoRepositorioEstadisticas,
        parent: Optional[tk.Widget] = None,
        exportador_pdf: Optional[PuertoExportadorPDF] = None,
    ):
        self.repo = repo_estadisticas
        self.exportador_pdf = exportador_pdf
        self.resumen_actual = ResumenEstadisticoGeneral()

        if parent:
            self.root = tk.Toplevel(parent)
        else:
            try:
                self.root = tk.Toplevel()
            except Exception:
                self.root = tk.Tk()

        self.root.title("Estadísticas Institucionales — Colinas del Llano")
        self.root.config(bg=COLOR_FONDO_APP)
        centrar_ventana(self.root, 980, 680)
        configurar_ventana_hija(self.root, parent, es_modal=False)
        self.barra_volver = agregar_barra_superior_volver(
            self.root, parent, "Módulo de Estadísticas"
        )
        botones_barra = [w for w in self.barra_volver.winfo_children() if isinstance(w, tk.Button)]
        self.btn_volver = botones_barra[0] if botones_barra else None
        maximizar_ventana(self.root)

        self._crear_interfaz()
        self.cargar_estadisticas()

    def _crear_interfaz(self):
        """Construye cabecera, 4 tarjetas KPI, 2 lienzos Canvas y tabla de alertas."""
        # ═══ ENCABEZADO INSTITUCIONAL ═══
        f_header = tk.Frame(self.root, bg=COLOR_PRIMARIO, pady=8, padx=14)
        f_header.pack(fill="x")

        tk.Label(
            f_header,
            text="📈  ESTADÍSTICAS INSTITUCIONALES",
            font=FUENTE_ENCABEZADO,
            fg=COLOR_TEXTO_CLARO,
            bg=COLOR_PRIMARIO,
        ).pack(side="left")

        self.btn_actualizar = crear_boton(
            f_header,
            "🔄  Actualizar Métricas",
            self.cargar_estadisticas,
            COLOR_SECUNDARIO,
            COLOR_TEXTO_CLARO,
            COLOR_SECUNDARIO_HOVER,
            padx=12,
            pady=5,
        )
        self.btn_actualizar.pack(side="right")
        AyudaVisual(self.btn_actualizar, "Recalcular gráficos desde la base de datos")

        self.btn_exportar_pdf = crear_boton(
            f_header,
            "🖨️  Exportar PDF",
            self.exportar_pdf_click,
            COLOR_PELIGRO,
            COLOR_TEXTO_CLARO,
            COLOR_PELIGRO_HOVER,
            padx=12,
            pady=5,
        )
        self.btn_exportar_pdf.pack(side="right", padx=(0, 8))
        AyudaVisual(self.btn_exportar_pdf, "Exportar reporte  estadístico en PDF")

        # Contenedor principal
        cuerpo = tk.Frame(self.root, bg=COLOR_FONDO_APP, padx=12, pady=8)
        cuerpo.pack(fill="both", expand=True)

        # ═══ FILA SUPERIOR: 4 TARJETAS KPI ═══
        f_kpis = tk.Frame(cuerpo, bg=COLOR_FONDO_APP)
        f_kpis.pack(fill="x", pady=(0, 8))
        for col in range(4):
            f_kpis.columnconfigure(col, weight=1, uniform="kpi")

        self.lbl_kpi_estudiantes = self._crear_tarjeta_kpi(
            f_kpis, 0, "Estudiantes Activos", "0", COLOR_SECUNDARIO
        )
        self.lbl_kpi_docentes = self._crear_tarjeta_kpi(
            f_kpis, 1, "Docentes Activos", "0", COLOR_PRIMARIO
        )
        self.lbl_kpi_asistencia = self._crear_tarjeta_kpi(
            f_kpis, 2, "% Asistencia Global", "100.0%", COLOR_ACENTO
        )
        self.lbl_kpi_riesgo = self._crear_tarjeta_kpi(
            f_kpis, 3, "Alumnos en Riesgo (< 75%)", "0", COLOR_PELIGRO
        )

        # ═══ ZONA INFERIOR: TREEVIEW DE RIESGO CRÍTICO (empaquetada antes para garantizar visibilidad) ═══
        f_tabla_wrap = tk.Frame(cuerpo, bg=COLOR_FONDO_APP)
        f_tabla_wrap.pack(side="bottom", fill="x", pady=(6, 0))

        self.lbl_titulo_riesgo = tk.Label(
            f_tabla_wrap,
            text="⚠️  Estudiantes en Alerta Crítica (< 75.0% Art. 109 RGLOE): 0",
            font=FUENTE_PEQUEÑA_BOLD,
            fg=COLOR_PELIGRO,
            bg=COLOR_FONDO_APP,
            anchor="w",
        )
        self.lbl_titulo_riesgo.pack(fill="x", pady=(0, 3))

        cols = ("cedula", "nombre", "grado_sec", "efectivas", "total", "pct")
        encabezados = ["Cédula", "Estudiante", "Grado / Sección", "Asist. (P+J)", "Clases", "% Asist."]
        anchos = [95, 260, 140, 100, 75, 85]
        anclas = ["center", "w", "center", "center", "center", "center"]

        self.tree_riesgo, frame_tree = crear_treeview_zebra(
            f_tabla_wrap, cols, encabezados, anchos, anclas, alto=4
        )
        frame_tree.pack(fill="x")

        # ═══ ZONA CENTRAL: 2 GRÁFICOS EN TK.CANVAS PURO ═══
        f_graficos = tk.Frame(cuerpo, bg=COLOR_FONDO_APP)
        f_graficos.pack(fill="both", expand=True)
        f_graficos.columnconfigure(0, weight=1, uniform="chart")
        f_graficos.columnconfigure(1, weight=1, uniform="chart")
        f_graficos.rowconfigure(0, weight=1)

        # Panel Izquierdo: Barras horizontales por sección
        card_izq = crear_tarjeta(f_graficos, padx=10, pady=8)
        card_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        tk.Label(
            card_izq,
            text="% Asistencia Efectiva por Sección (Meta Legal 75%)",
            font=FUENTE_CUERPO_BOLD,
            fg=COLOR_PRIMARIO,
            bg=COLOR_TARJETA,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.canvas_secciones = tk.Canvas(
            card_izq, bg=COLOR_TARJETA, highlightthickness=0, height=235
        )
        self.canvas_secciones.pack(fill="both", expand=True)
        self.canvas_secciones.bind("<Configure>", lambda e: self._dibujar_canvas_secciones())

        # Panel Derecho: Distribución P/A/J y Género
        card_der = crear_tarjeta(f_graficos, padx=10, pady=8)
        card_der.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        tk.Label(
            card_der,
            text="Asistencia (P / A / J) y Matrícula por Género",
            font=FUENTE_CUERPO_BOLD,
            fg=COLOR_PRIMARIO,
            bg=COLOR_TARJETA,
            wraplength=420,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.canvas_distribucion = tk.Canvas(
            card_der, bg=COLOR_TARJETA, highlightthickness=0, height=235
        )
        self.canvas_distribucion.pack(fill="both", expand=True)
        self.canvas_distribucion.bind("<Configure>", lambda e: self._dibujar_canvas_distribucion())

    def _crear_tarjeta_kpi(self, parent, columna: int, titulo: str, valor_inicial: str, color_acento: str) -> tk.Label:
        """Crea una tarjeta KPI compacta con banda de color superior."""
        tarjeta = tk.Frame(
            parent,
            bg=COLOR_TARJETA,
            highlightbackground=COLOR_BORDE_TARJETA,
            highlightthickness=1,
        )
        tarjeta.grid(row=0, column=columna, sticky="nsew", padx=4)

        tk.Frame(tarjeta, bg=color_acento, height=4).pack(fill="x")
        cuerpo = tk.Frame(tarjeta, bg=COLOR_TARJETA, padx=10, pady=6)
        cuerpo.pack(fill="both", expand=True)

        tk.Label(
            cuerpo, text=titulo, font=FUENTE_PEQUEÑA_BOLD,
            fg=COLOR_TEXTO_SECUNDARIO, bg=COLOR_TARJETA, anchor="w",
        ).pack(fill="x")

        lbl_valor = tk.Label(
            cuerpo, text=valor_inicial, font=FUENTE_TITULO,
            fg=color_acento, bg=COLOR_TARJETA, anchor="w",
        )
        lbl_valor.pack(fill="x", pady=(2, 0))
        return lbl_valor

    # ──────────────────────────────────────────────────────────────
    # CARGA DE MÉTRICAS, EXPORTACIÓN PDF Y RENDERIZADO TK.CANVAS
    # ──────────────────────────────────────────────────────────────
    def cargar_estadisticas(self):
        """Consulta el repositorio y actualiza KPIs, gráficos Canvas y tabla de riesgo."""
        try:
            self.resumen_actual = self.repo.obtener_resumen_institucional()
        except Exception as err:
            messagebox.showerror(
                "Error de Estadísticas",
                f"No se pudieron cargar las métricas institucionales:\n{err}",
                parent=self.root,
            )
            restaurar_foco(self.root)
            return

        r = self.resumen_actual
        self.lbl_kpi_estudiantes.config(text=str(r.total_estudiantes_activos))
        self.lbl_kpi_docentes.config(text=str(r.total_docentes_activos))

        color_tasa = self._color_por_semaforo(r.tasa_asistencia_global)
        self.lbl_kpi_asistencia.config(text=f"{r.tasa_asistencia_global:.1f}%", fg=color_tasa)

        color_riesgo = COLOR_PELIGRO if r.total_en_riesgo > 0 else COLOR_ACENTO
        self.lbl_kpi_riesgo.config(text=str(r.total_en_riesgo), fg=color_riesgo)

        self.lbl_titulo_riesgo.config(
            text=f"⚠️  Estudiantes en Alerta Crítica (< 75.0% Art. 109 RGLOE): {r.total_en_riesgo}",
            fg=color_riesgo,
        )

        # Poblar tabla de riesgo
        for item in self.tree_riesgo.get_children():
            self.tree_riesgo.delete(item)
        for est in r.estudiantes_en_riesgo:
            self.tree_riesgo.insert(
                "",
                "end",
                values=(
                    est.id_estudiante,
                    est.nombre,
                    f"{est.grado} {est.seccion}",
                    est.asistencias_efectivas,
                    est.total_clases,
                    f"{est.porcentaje_asistencia:.1f}%",
                ),
                tags=("alerta_riesgo",),
            )

        self._dibujar_canvas_secciones()
        self._dibujar_canvas_distribucion()

    def exportar_pdf_click(self):
        """Exporta el reporte institucional de estadísticas a PDF usando el puerto."""
        top = self.root.winfo_toplevel()
        if not self.exportador_pdf:
            messagebox.showerror(
                "Servicio No Disponible",
                "El servicio de exportación PDF no está configurado.",
                parent=top,
            )
            restaurar_foco(top)
            return

        ruta_salida = filedialog.asksaveasfilename(
            parent=top,
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            initialfile="Estadisticas_Institucionales.pdf",
            title="Guardar Reporte de Estadísticas Institucionales",
        )
        restaurar_foco(top)
        if not ruta_salida:
            return

        try:
            exito = self.exportador_pdf.generar_reporte_estadisticas(self.resumen_actual, ruta_salida)
            if exito:
                if messagebox.askyesno(
                    "Reporte Generado",
                    f"Reporte de estadísticas generado con éxito:\n{ruta_salida}\n\n¿Desea abrir el archivo ahora?",
                    parent=top,
                ):
                    abrir_archivo_sistema(ruta_salida)
            else:
                messagebox.showerror(
                    "Error de Exportación",
                    "No se pudo generar el documento PDF de estadísticas.",
                    parent=top,
                )
        except Exception as err:
            messagebox.showerror(
                "Error de Exportación",
                f"Fallo al exportar el PDF de estadísticas:\n{err}",
                parent=top,
            )
        finally:
            restaurar_foco(top)

    @staticmethod
    def _color_por_semaforo(tasa: float) -> str:
        clasif = CalculadoraEstadisticas.clasificar_semaforo(tasa)
        if clasif == "verde":
            return COLOR_ACENTO
        if clasif == "ambar":
            return COLOR_ADVERTENCIA
        return COLOR_PELIGRO

    def _dimensiones_canvas(self, canvas: tk.Canvas) -> tuple[int, int]:
        """Obtiene ancho y alto seguros incluso antes del primer mapeo en pantalla."""
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 120:
            w = 450
        if h < 120:
            h = 235
        return w, h

    def _dibujar_canvas_secciones(self):
        """Dibuja barras horizontales de % asistencia por sección con línea meta en 75%."""
        canvas = self.canvas_secciones
        canvas.delete("all")
        w, h = self._dimensiones_canvas(canvas)

        metricas = self.resumen_actual.metricas_por_seccion
        if not metricas:
            canvas.create_text(
                w / 2,
                h / 2,
                text="Sin registros de asistencia por sección todavía.",
                fill=COLOR_TEXTO_SECUNDARIO,
                font=FUENTE_CUERPO,
            )
            return

        margen_izq = 95
        margen_der = 68  # >= 65 px para que porcentajes como 100.0% nunca toquen el borde
        margen_sup = 20
        margen_inf = 18
        ancho_barra_max = max(80, w - margen_izq - margen_der)
        alto_disp = max(60, h - margen_sup - margen_inf)

        visibles = metricas[:10]
        n = len(visibles)
        paso = alto_disp / max(1, n)
        alto_barra = min(20, max(10, paso * 0.62))

        x_base = margen_izq
        x_75 = x_base + ancho_barra_max * 0.75
        y_fin = margen_sup + paso * n

        canvas.create_line(x_base, margen_sup - 4, x_base, y_fin, fill="#BDC3C7", width=1)
        canvas.create_line(x_75, margen_sup - 6, x_75, y_fin + 4, fill=COLOR_PRIMARIO, dash=(4, 3), width=2)
        canvas.create_text(
            x_75,
            margen_sup - 12,
            text="Meta 75%",
            fill=COLOR_PRIMARIO,
            font=FUENTE_PEQUEÑA_BOLD,
        )

        for idx, met in enumerate(visibles):
            y_centro = margen_sup + idx * paso + paso / 2
            y1 = y_centro - alto_barra / 2
            y2 = y_centro + alto_barra / 2

            canvas.create_rectangle(
                x_base, y1, x_base + ancho_barra_max, y2,
                fill="#F0F3F4", outline="#E5E7E9",
            )

            pct = max(0.0, min(100.0, float(met.tasa_efectiva)))
            x_val = x_base + ancho_barra_max * (pct / 100.0)
            color_barra = self._color_por_semaforo(pct)

            if x_val > x_base:
                canvas.create_rectangle(
                    x_base, y1, x_val, y2,
                    fill=color_barra, outline="",
                )

            canvas.create_text(
                x_base - 8,
                y_centro,
                text=met.etiqueta[:13],
                anchor="e",
                fill=COLOR_TEXTO_PRINCIPAL,
                font=FUENTE_PEQUEÑA_BOLD,
            )
            canvas.create_text(
                x_base + ancho_barra_max + 8,
                y_centro,
                text=f"{pct:.1f}%",
                anchor="w",
                fill=color_barra,
                font=FUENTE_PEQUEÑA_BOLD,
            )

    def _dibujar_canvas_distribucion(self):
        """Dibuja distribución global P/A/J (leyenda en 3 filas apiladas) y matrícula por género."""
        canvas = self.canvas_distribucion
        canvas.delete("all")
        w, h = self._dimensiones_canvas(canvas)

        dist = self.resumen_actual.distribucion_estados
        gen = self.resumen_actual.distribucion_genero

        if dist.total == 0 and gen.total == 0:
            canvas.create_text(
                w / 2,
                h / 2,
                text="Sin datos registrados para graficar.",
                fill=COLOR_TEXTO_SECUNDARIO,
                font=FUENTE_CUERPO,
            )
            return

        pad_x = 16
        ancho_barra = max(120, w - 2 * pad_x)

        # ── Bloque 1: Estados P / A / J ──
        canvas.create_text(
            pad_x, 14,
            text=f"Marcajes de Asistencia (Total: {dist.total})",
            anchor="w", fill=COLOR_TEXTO_PRINCIPAL, font=FUENTE_PEQUEÑA_BOLD,
        )

        y_bar1 = 28
        h_bar1 = 22
        if dist.total > 0:
            x_cur = pad_x
            segmentos = [
                ("Presentes (P)", dist.presentes, dist.porcentaje_presentes, COLOR_ACENTO),
                ("Justificadas (J)", dist.justificadas, dist.porcentaje_justificadas, COLOR_ADVERTENCIA),
                ("Ausentes (A)", dist.ausentes, dist.porcentaje_ausentes, COLOR_PELIGRO),
            ]
            for _, cant, _, col in segmentos:
                seg_w = ancho_barra * (cant / dist.total)
                if seg_w > 0:
                    canvas.create_rectangle(
                        x_cur, y_bar1, x_cur + seg_w, y_bar1 + h_bar1,
                        fill=col, outline=COLOR_TARJETA, width=1,
                    )
                    x_cur += seg_w
        else:
            canvas.create_rectangle(
                pad_x, y_bar1, pad_x + ancho_barra, y_bar1 + h_bar1,
                fill="#EAECEE", outline="#D5D8DC",
            )
            canvas.create_text(
                pad_x + ancho_barra / 2, y_bar1 + h_bar1 / 2,
                text="Sin marcajes de asistencia", fill=COLOR_TEXTO_SECUNDARIO, font=FUENTE_PEQUEÑA,
            )

        # Leyenda P / J / A en 3 filas verticales apiladas (cero solapamiento horizontal)
        items_leg = [
            ("Presentes (P)", dist.presentes, dist.porcentaje_presentes, COLOR_ACENTO, "leyenda_paj"),
            ("Justificadas (J)", dist.justificadas, dist.porcentaje_justificadas, COLOR_ADVERTENCIA, "leyenda_paj"),
            ("Ausentes (A)", dist.ausentes, dist.porcentaje_ausentes, COLOR_PELIGRO, "leyenda_paj"),
        ]
        y_leg_inicio = 60
        paso_leg = 19
        for idx, (lbl, cant, pct, col, tag_leg) in enumerate(items_leg):
            y_fila = y_leg_inicio + idx * paso_leg
            canvas.create_rectangle(pad_x, y_fila, pad_x + 10, y_fila + 10, fill=col, outline="")
            canvas.create_text(
                pad_x + 16, y_fila + 5,
                text=f"{lbl}: {cant} ({pct:.1f}%)",
                anchor="w",
                fill=COLOR_TEXTO_PRINCIPAL,
                font=FUENTE_PEQUEÑA,
                tags=(tag_leg,),
            )

        # Separador visual debajo de las 3 filas
        y_sep = max(124, int(h * 0.54))
        canvas.create_line(pad_x, y_sep, pad_x + ancho_barra, y_sep, fill="#E5E7E9", width=1)

        # ── Bloque 2: Matrícula por Género (M / F) ──
        y_titulo2 = y_sep + 14
        canvas.create_text(
            pad_x, y_titulo2,
            text=f"Matrícula Activa por Género (Total: {gen.total})",
            anchor="w", fill=COLOR_TEXTO_PRINCIPAL, font=FUENTE_PEQUEÑA_BOLD,
        )

        generos = [
            ("Masculino (M)", gen.masculino, gen.porcentaje_masculino, COLOR_SECUNDARIO),
            ("Femenino (F)", gen.femenino, gen.porcentaje_femenino, "#8E44AD"),
        ]
        lbl_w = 102
        pct_w = 88
        bar_gen_max = max(60, ancho_barra - lbl_w - pct_w)

        for idx, (nombre_gen, cant, pct, col) in enumerate(generos):
            y_row = y_titulo2 + 18 + idx * 28
            canvas.create_text(
                pad_x, y_row + 8, text=nombre_gen,
                anchor="w", fill=COLOR_TEXTO_PRINCIPAL, font=FUENTE_PEQUEÑA_BOLD,
            )
            x_g = pad_x + lbl_w
            canvas.create_rectangle(
                x_g, y_row, x_g + bar_gen_max, y_row + 16,
                fill="#F0F3F4", outline="#E5E7E9",
            )
            if gen.total > 0 and cant > 0:
                w_fill = bar_gen_max * (cant / gen.total)
                canvas.create_rectangle(
                    x_g, y_row, x_g + w_fill, y_row + 16,
                    fill=col, outline="",
                )
            canvas.create_text(
                x_g + bar_gen_max + 8, y_row + 8,
                text=f"{cant} ({pct:.1f}%)",
                anchor="w", fill=col, font=FUENTE_PEQUEÑA_BOLD,
            )
