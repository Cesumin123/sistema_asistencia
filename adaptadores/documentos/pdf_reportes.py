# adaptadores/documentos/pdf_reportes.py
"""
Adaptador de Exportación PDF con ReportLab Platypus.
Implementa el puerto PuertoExportadorPDF reutilizando el formato institucional
del Complejo Educativo 'Colinas del Llano' (Barinas, Venezuela).
Totalmente desacoplado de bases de datos y de la interfaz gráfica.
"""

from typing import List, Optional, Any
from datetime import datetime
import os

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from puertos.repositorio_reportes import PuertoExportadorPDF
from adaptadores.documentos.gestor_fotos import GestorFotos


class ExportadorPDFReportLab(PuertoExportadorPDF):
    """
    Imprenta PDF institucional para reportes escolares y fichas oficiales.
    Genera documentos en formato PDF con membrete oficial y tablas maquetadas.
    """

    def __init__(self, gestor_fotos: Optional[GestorFotos] = None):
        self.gestor_fotos = gestor_fotos or GestorFotos()

    @staticmethod
    def _dibujar_membrete(canvas, doc):
        """Dibuja el membrete oficial institucional en cada página."""
        canvas.saveState()
        ancho, alto = letter

        # 1. Encabezado a tres columnas
        canvas.setFont("Helvetica-Bold", 9)

        # Bloque Izquierdo
        canvas.drawString(40, alto - 40, "Gobierno Bolivariano")
        canvas.drawString(40, alto - 50, "de Venezuela")

        # Bloque Central
        canvas.drawCentredString(ancho / 2, alto - 40, "Ministerio del Poder Popular")
        canvas.drawCentredString(ancho / 2, alto - 50, "Para la Educación")

        # Bloque Derecho
        canvas.drawRightString(ancho - 40, alto - 40, "Complejo educativo")
        canvas.drawRightString(ancho - 40, alto - 50, '"Colinas Del Llano"')
        canvas.drawRightString(ancho - 40, alto - 60, "BARINAS")

        # 2. Fecha de emisión
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        hoy = datetime.now()
        fecha_texto = f"CIUDAD VARYNA, {hoy.day:02d} de {meses[hoy.month - 1]} del {hoy.year}"

        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(ancho - 40, alto - 90, fecha_texto)

        # 3. Línea separadora
        canvas.setLineWidth(1)
        canvas.line(40, alto - 100, ancho - 40, alto - 100)

        # 4. Pie de página centrado con número de página
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(ancho / 2, 30, f"Página {doc.page}")

        canvas.restoreState()

    def exportar_tabla(
        self,
        titulo: str,
        encabezados: List[str],
        datos: List[List[str]],
        ruta_salida: str
    ) -> bool:
        """
        Construye y almacena el documento PDF con membrete institucional y tabla de datos.

        Args:
            titulo: Título principal del reporte.
            encabezados: Lista con los nombres de las columnas.
            datos: Matriz con las filas de datos como cadenas de texto.
            ruta_salida: Ruta absoluta o relativa del archivo PDF a generar.

        Returns:
            bool: True si el documento se creó exitosamente, False si ocurrió un error.
        """
        try:
            # Asegurar que el directorio de salida exista
            dir_salida = os.path.dirname(ruta_salida)
            if dir_salida and not os.path.exists(dir_salida):
                os.makedirs(dir_salida, exist_ok=True)

            doc = SimpleDocTemplate(
                ruta_salida,
                pagesize=letter,
                rightMargin=40,
                leftMargin=40,
                topMargin=120,
                bottomMargin=50
            )

            elementos = []
            estilos = getSampleStyleSheet()

            # Título principal centrado
            estilo_titulo = estilos['Heading2']
            estilo_titulo.alignment = 1
            titulo_p = Paragraph(f"<b>{titulo}</b>", estilo_titulo)
            elementos.append(titulo_p)
            elementos.append(Spacer(1, 15))

            # Tabla de datos con repetición de encabezado en páginas siguientes
            tabla_completa = [encabezados] + datos
            tabla_pdf = Table(tabla_completa, repeatRows=1)

            estilo_tabla = TableStyle([
                # Fila de cabecera con fondo gris y negrita
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#d5d8dc")),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                # Cuadrícula completa
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ])
            tabla_pdf.setStyle(estilo_tabla)
            elementos.append(tabla_pdf)

            # Construir el documento con el membrete institucional
            doc.build(
                elementos,
                onFirstPage=self._dibujar_membrete,
                onLaterPages=self._dibujar_membrete
            )
            return True

        except Exception as error:
            print(f"Error al generar reporte PDF: {error}")
            return False

    def _obtener_flowable_foto(self, foto_path: Optional[str], ancho: float = 90, alto: float = 95):
        """Retorna un Image de ReportLab si la foto existe físicamente, o un recuadro 'SIN FOTO'."""
        ruta_abs = self.gestor_fotos.resolver_ruta_absoluta(foto_path)
        if ruta_abs and os.path.exists(ruta_abs):
            try:
                return RLImage(ruta_abs, width=ancho, height=alto)
            except Exception as e:
                print(f"Aviso al cargar foto en PDF: {e}")

        # Recuadro placeholder
        tbl_sin_foto = Table([["[ SIN FOTO ]"]], colWidths=[ancho], rowHeights=[alto])
        tbl_sin_foto.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#7f8c8d")),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f2f4f4")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
        ]))
        return tbl_sin_foto

    def generar_ficha_docente(
        self,
        profesor: Any,
        materias_asignadas: Optional[List[Any]] = None,
        ruta_salida: Optional[str] = None
    ) -> str:
        """
        Construye la ficha oficial de expediente del profesor y retorna la ruta del PDF.
        """
        if not ruta_salida:
            ced = getattr(profesor, "cedula", "docente").replace("-", "_").replace(".", "")
            ruta_salida = f"reportes/Ficha_Docente_{ced}.pdf"

        dir_salida = os.path.dirname(ruta_salida)
        if dir_salida and not os.path.exists(dir_salida):
            os.makedirs(dir_salida, exist_ok=True)

        doc = SimpleDocTemplate(
            ruta_salida,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=110,
            bottomMargin=40
        )

        elementos = []
        estilos = getSampleStyleSheet()

        # Título oficial
        estilo_tit = estilos['Heading2']
        estilo_tit.alignment = 1
        elementos.append(Paragraph("<b>FICHA OFICIAL DE REGISTRO DOCENTE</b>", estilo_tit))
        elementos.append(Spacer(1, 12))

        # 1. Bloque de Datos Personales con Foto a la derecha
        flow_foto = self._obtener_flowable_foto(getattr(profesor, "foto_path", ""))
        estado_str = "ACTIVO" if getattr(profesor, "estado_activo", 1) == 1 else "INACTIVO"
        profesion_str = getattr(profesor, "profesion", "") or "DOCENTE ORDINARIO"
        telefono_str = getattr(profesor, "telefono", "") or "No registrado"

        datos_personales = [
            [Paragraph("<b>Cédula de Identidad:</b>", estilos['Normal']), Paragraph(str(profesor.cedula), estilos['Normal'])],
            [Paragraph("<b>Nombre Completo:</b>", estilos['Normal']), Paragraph(str(profesor.nombre_completo), estilos['Normal'])],
            [Paragraph("<b>Profesión / Título:</b>", estilos['Normal']), Paragraph(profesion_str, estilos['Normal'])],
            [Paragraph("<b>Teléfono de Contacto:</b>", estilos['Normal']), Paragraph(telefono_str, estilos['Normal'])],
            [Paragraph("<b>Estatus en el Sistema:</b>", estilos['Normal']), Paragraph(estado_str, estilos['Normal'])],
        ]
        tbl_datos = Table(datos_personales, colWidths=[150, 270])
        tbl_datos.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8f9f9")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#d5d8dc")),
        ]))

        # Ensamblar tabla de cabecera (Datos a la izquierda + Foto a la derecha)
        cabecera_compuesta = Table([[tbl_datos, flow_foto]], colWidths=[425, 105])
        cabecera_compuesta.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        elementos.append(cabecera_compuesta)
        elementos.append(Spacer(1, 18))

        # 2. Carga Académica y Asignaciones
        elementos.append(Paragraph("<b>CARGA ACADÉMICA / MATERIAS ASIGNADAS</b>", estilos['Heading3']))
        elementos.append(Spacer(1, 6))

        if materias_asignadas:
            filas_materias = [["#", "Materia / Asignatura", "Año y Sección"]]
            for idx, mat in enumerate(materias_asignadas, start=1):
                if isinstance(mat, dict):
                    nom_mat = mat.get("materia", "")
                    sec_info = f"{mat.get('grado', '')} {mat.get('seccion', '')}".strip()
                    filas_materias.append([str(idx), nom_mat, sec_info])
                else:
                    mat_str = str(mat)
                    partes = mat_str.split(" - ") if " - " in mat_str else [mat_str, ""]
                    filas_materias.append([str(idx), partes[0], partes[1] if len(partes) > 1 else ""])

            tbl_mat = Table(filas_materias, colWidths=[35, 315, 180])
            tbl_mat.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elementos.append(tbl_mat)
        else:
            elementos.append(Paragraph("<i>No posee materias curriculares asignadas en el período activo.</i>", estilos['Italic']))

        elementos.append(Spacer(1, 40))

        # 3. Firmas y Sellos Institucionales
        tbl_firmas = Table([
            ["_____________________________________", "_____________________________________"],
            ["Firma del Docente Titular", "Coordinación de 4to Año (Sello y Firma)"]
        ], colWidths=[265, 265])
        tbl_firmas.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elementos.append(tbl_firmas)

        doc.build(elementos, onFirstPage=self._dibujar_membrete, onLaterPages=self._dibujar_membrete)
        return ruta_salida

    def generar_ficha_estudiante(
        self,
        estudiante: Any,
        resumen_asistencia: Optional[dict] = None,
        ruta_salida: Optional[str] = None
    ) -> str:
        """
        Construye la ficha oficial de inscripción/expediente del estudiante y retorna la ruta del PDF.
        """
        if not ruta_salida:
            ced = getattr(estudiante, "cedula", "estudiante").replace("-", "_").replace(".", "")
            ruta_salida = f"reportes/Ficha_Estudiante_{ced}.pdf"

        dir_salida = os.path.dirname(ruta_salida)
        if dir_salida and not os.path.exists(dir_salida):
            os.makedirs(dir_salida, exist_ok=True)

        doc = SimpleDocTemplate(
            ruta_salida,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=110,
            bottomMargin=35
        )

        elementos = []
        estilos = getSampleStyleSheet()

        # Título oficial
        estilo_tit = estilos['Heading2']
        estilo_tit.alignment = 1
        elementos.append(Paragraph("<b>EXPEDIENTE INDIVIDUAL Y FICHA DE INSCRIPCIÓN</b>", estilo_tit))
        elementos.append(Spacer(1, 10))

        # 1. Datos del Estudiante con Foto a la derecha
        flow_foto = self._obtener_flowable_foto(getattr(estudiante, "foto_path", ""))
        sec_letra = chr(estudiante.id_seccion + 64) if hasattr(estudiante, "id_seccion") and 1 <= estudiante.id_seccion <= 26 else str(getattr(estudiante, "id_seccion", ""))

        datos_personales = [
            [Paragraph("<b>Cédula Estudiantil:</b>", estilos['Normal']), Paragraph(str(estudiante.cedula), estilos['Normal'])],
            [Paragraph("<b>Nombre Completo:</b>", estilos['Normal']), Paragraph(str(estudiante.nombre), estilos['Normal'])],
            [Paragraph("<b>Fecha de Nacimiento:</b>", estilos['Normal']), Paragraph(str(estudiante.fecha_nacimiento), estilos['Normal'])],
            [Paragraph("<b>Año Escolar y Sección:</b>", estilos['Normal']), Paragraph(f"{estudiante.id_grado}do AÑO — Sección {sec_letra}", estilos['Normal'])],
            [Paragraph("<b>Género / Turno / Condición:</b>", estilos['Normal']), Paragraph(f"{estudiante.genero}  |  {estudiante.turno}  |  {estudiante.condicion}", estilos['Normal'])],
            [Paragraph("<b>Régimen de Escolaridad:</b>", estilos['Normal']), Paragraph(str(estudiante.escolaridad), estilos['Normal'])],
        ]
        tbl_datos = Table(datos_personales, colWidths=[150, 270])
        tbl_datos.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8f9f9")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#d5d8dc")),
        ]))

        cabecera_compuesta = Table([[tbl_datos, flow_foto]], colWidths=[425, 105])
        cabecera_compuesta.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        elementos.append(cabecera_compuesta)
        elementos.append(Spacer(1, 10))

        # 2. Información Familiar y Representación Legal
        elementos.append(Paragraph("<b>INFORMACIÓN FAMILIAR Y REPRESENTACIÓN LEGAL</b>", estilos['Heading3']))
        elementos.append(Spacer(1, 4))

        nombre_madre = getattr(estudiante, "nombre_madre", "") or "NO REGISTRADO"
        telf_madre = getattr(estudiante, "telefono_madre", "") or "S/N"
        nombre_padre = getattr(estudiante, "nombre_padre", "") or "NO REGISTRADO"
        telf_padre = getattr(estudiante, "telefono_padre", "") or "S/N"
        representante = getattr(estudiante, "representante", "") or "NO REGISTRADO"
        telefono_rep = getattr(estudiante, "telefono", "") or "S/N"

        datos_familia = [
            ["Representante Legal:", representante, "Teléfono:", telefono_rep],
            ["Madre del Alumno:", nombre_madre, "Teléfono Madre:", telf_madre],
            ["Padre del Alumno:", nombre_padre, "Teléfono Padre:", telf_padre],
        ]
        tbl_fam = Table(datos_familia, colWidths=[130, 180, 100, 120])
        tbl_fam.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fdfefe")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#d5d8dc")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tbl_fam)
        elementos.append(Spacer(1, 10))

        # 3. Resumen Académico / Asistencia (Art. 109 RGLOE)
        elementos.append(Paragraph("<b>HISTORIAL Y CONDICIÓN DE ASISTENCIA (ART. 109 RGLOE)</b>", estilos['Heading3']))
        elementos.append(Spacer(1, 4))

        if resumen_asistencia and isinstance(resumen_asistencia, dict):
            total_clases = resumen_asistencia.get("total_clases", 0)
            efectivas = resumen_asistencia.get("asistencias_efectivas", 0)
            faltas = resumen_asistencia.get("faltas_injustificadas", 0)
            pct = resumen_asistencia.get("porcentaje_asistencia", 100.0)
            condicion_legal = "EN REGLA (CUMPLE >= 75%)" if pct >= 75.0 else "EN RIESGO DE REPROBACIÓN (< 75%)"

            color_alerta = colors.HexColor("#27ae60") if pct >= 75.0 else colors.HexColor("#c0392b")

            datos_asist = [
                ["Clases Dictadas", "Asist. Efectivas (P+J)", "Inasistencias (A)", "% Asistencia", "Dictamen Legal"],
                [str(total_clases), str(efectivas), str(faltas), f"{pct:.1f}%", condicion_legal]
            ]
            tbl_asist = Table(datos_asist, colWidths=[95, 115, 95, 85, 140])
            tbl_asist.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TEXTCOLOR', (4, 1), (4, 1), color_alerta),
                ('FONTNAME', (4, 1), (4, 1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elementos.append(tbl_asist)
        else:
            elementos.append(Paragraph("<i>Expediente sin jornadas de inasistencias acumuladas en el período.</i>", estilos['Italic']))

        elementos.append(Spacer(1, 30))

        # 4. Firmas
        tbl_firmas = Table([
            ["___________________________", "___________________________", "___________________________"],
            ["Firma del Estudiante", "Firma del Representante", "Coordinación (Sello y Firma)"]
        ], colWidths=[175, 175, 180])
        tbl_firmas.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ]))
        elementos.append(tbl_firmas)

        doc.build(elementos, onFirstPage=self._dibujar_membrete, onLaterPages=self._dibujar_membrete)
        return ruta_salida

    def generar_reporte_estadisticas(self, resumen: Any, ruta_salida: str) -> bool:
        """
        Genera el reporte PDF institucional consolidado de estadísticas escolares
        con membrete oficial, KPIs, asistencia por sección, desglose P/A/J, género y alertas Art. 109 RGLOE.
        """
        try:
            dir_salida = os.path.dirname(ruta_salida)
            if dir_salida and not os.path.exists(dir_salida):
                os.makedirs(dir_salida, exist_ok=True)

            doc = SimpleDocTemplate(
                ruta_salida,
                pagesize=letter,
                rightMargin=40,
                leftMargin=40,
                topMargin=115,
                bottomMargin=45,
            )

            elementos = []
            estilos = getSampleStyleSheet()

            estilo_tit = estilos["Heading2"]
            estilo_tit.alignment = 1
            elementos.append(
                Paragraph("<b>REPORTE DE ESTADÍSTICAS INSTITUCIONALES (ART. 109 RGLOE)</b>", estilo_tit)
            )
            elementos.append(Spacer(1, 10))

            # 1. Resumen de KPIs
            est_act = getattr(resumen, "total_estudiantes_activos", 0)
            doc_act = getattr(resumen, "total_docentes_activos", 0)
            clases_act = getattr(resumen, "total_clases_activas", 0)
            tasa_global = getattr(resumen, "tasa_asistencia_global", 100.0)
            total_riesgo = getattr(resumen, "total_en_riesgo", 0)

            datos_kpi = [
                ["Estudiantes Activos", "Docentes Activos", "Clases Activas", "% Asist. Global", "En Riesgo (<75%)"],
                [str(est_act), str(doc_act), str(clases_act), f"{tasa_global:.1f}%", str(total_riesgo)],
            ]
            tbl_kpi = Table(datos_kpi, colWidths=[106, 106, 106, 106, 106])
            tbl_kpi.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8f9f9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elementos.append(tbl_kpi)
            elementos.append(Spacer(1, 14))

            # 2. Desglose P / A / J y Género
            elementos.append(Paragraph("<b>DISTRIBUCIÓN DE ASISTENCIA (P / A / J) Y MATRÍCULA POR GÉNERO</b>", estilos["Heading3"]))
            elementos.append(Spacer(1, 4))

            dist = getattr(resumen, "distribucion_estados", None)
            gen = getattr(resumen, "distribucion_genero", None)
            p_cnt = getattr(dist, "presentes", 0) if dist else 0
            j_cnt = getattr(dist, "justificadas", 0) if dist else 0
            a_cnt = getattr(dist, "ausentes", 0) if dist else 0
            p_pct = getattr(dist, "porcentaje_presentes", 0.0) if dist else 0.0
            j_pct = getattr(dist, "porcentaje_justificadas", 0.0) if dist else 0.0
            a_pct = getattr(dist, "porcentaje_ausentes", 0.0) if dist else 0.0

            m_cnt = getattr(gen, "masculino", 0) if gen else 0
            f_cnt = getattr(gen, "femenino", 0) if gen else 0
            m_pct = getattr(gen, "porcentaje_masculino", 0.0) if gen else 0.0
            f_pct = getattr(gen, "porcentaje_femenino", 0.0) if gen else 0.0

            datos_dist = [
                ["Indicador de Asistencia", "Cantidad", "Porcentaje", "Matrícula por Género", "Cantidad", "Porcentaje"],
                ["Presentes (P)", str(p_cnt), f"{p_pct:.1f}%", "Masculino (M)", str(m_cnt), f"{m_pct:.1f}%"],
                ["Justificadas (J)", str(j_cnt), f"{j_pct:.1f}%", "Femenino (F)", str(f_cnt), f"{f_pct:.1f}%"],
                ["Ausentes (A)", str(a_cnt), f"{a_pct:.1f}%", "Total Activos", str(m_cnt + f_cnt), "100.0%" if (m_cnt + f_cnt) > 0 else "0.0%"],
            ]
            tbl_dist = Table(datos_dist, colWidths=[120, 65, 80, 120, 65, 80])
            tbl_dist.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d5d8dc")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ALIGN", (1, 0), (2, -1), "CENTER"),
                ("ALIGN", (4, 0), (5, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elementos.append(tbl_dist)
            elementos.append(Spacer(1, 14))

            # 3. Tabla de Asistencia por Sección
            elementos.append(Paragraph("<b>ASISTENCIA EFECTIVA POR GRADO Y SECCIÓN</b>", estilos["Heading3"]))
            elementos.append(Spacer(1, 4))

            metricas = getattr(resumen, "metricas_por_seccion", []) or []
            if metricas:
                filas_sec = [["Sección", "Presentes", "Justif.", "Ausentes", "Total Reg.", "% Asistencia", "Condición (>=75%)"]]
                for m in metricas:
                    estado_sec = "CUMPLE (>=75%)" if m.tasa_efectiva >= 75.0 else "ALERTA (<75%)"
                    filas_sec.append([
                        m.etiqueta, str(m.presentes), str(m.justificadas),
                        str(m.ausentes), str(m.total_registros),
                        f"{m.tasa_efectiva:.1f}%", estado_sec,
                    ])
                tbl_sec = Table(filas_sec, colWidths=[95, 65, 55, 65, 65, 75, 110], repeatRows=1)
                tbl_sec.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                elementos.append(tbl_sec)
            else:
                elementos.append(Paragraph("<i>Sin registros de asistencia agrupados por sección.</i>", estilos["Italic"]))
            elementos.append(Spacer(1, 14))

            # 4. Estudiantes en Alerta Crítica (< 75% Art. 109 RGLOE)
            elementos.append(Paragraph("<b>ESTUDIANTES EN ALERTA CRÍTICA (&lt; 75.0% ART. 109 RGLOE)</b>", estilos["Heading3"]))
            elementos.append(Spacer(1, 4))

            riesgos = getattr(resumen, "estudiantes_en_riesgo", []) or []
            if riesgos:
                filas_r = [["Cédula", "Estudiante", "Grado / Sección", "Efectivas (P+J)", "Clases", "% Asist."]]
                for est in riesgos:
                    filas_r.append([
                        est.id_estudiante,
                        est.nombre,
                        f"{est.grado} {est.seccion}",
                        str(est.asistencias_efectivas),
                        str(est.total_clases),
                        f"{est.porcentaje_asistencia:.1f}%",
                    ])
                tbl_r = Table(filas_r, colWidths=[85, 175, 100, 70, 45, 55], repeatRows=1)
                tbl_r.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c0392b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (1, 1), (1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                elementos.append(tbl_r)
            else:
                elementos.append(Paragraph("<i>No se registran estudiantes por debajo del 75.0% de asistencia.</i>", estilos["Italic"]))

            doc.build(elementos, onFirstPage=self._dibujar_membrete, onLaterPages=self._dibujar_membrete)
            return True
        except Exception as error:
            print(f"Error al generar PDF de estadísticas: {error}")
            return False
