# adaptadores/documentos/pdf_reportes.py
"""
Adaptador de Exportación PDF con ReportLab Platypus.
Implementa el puerto PuertoExportadorPDF reutilizando el formato institucional
del Complejo Educativo 'Colinas del Llano' (Barinas, Venezuela).
Totalmente desacoplado de bases de datos y de la interfaz gráfica.
"""

from typing import List
from datetime import datetime
import os

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from puertos.repositorio_reportes import PuertoExportadorPDF


class ExportadorPDFReportLab(PuertoExportadorPDF):
    """
    Imprenta PDF institucional para reportes escolares.
    Genera documentos en formato PDF con membrete oficial y tablas maquetadas.
    """

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
