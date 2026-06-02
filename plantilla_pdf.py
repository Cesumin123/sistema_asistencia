from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime

class ImprentaPDF:
    """
    La Imprenta Central del Sistema.
    Se encarga de poner el membrete oficial y dibujar las tablas con bordes.
    """
    @staticmethod
    def dibujar_membrete(canvas, doc):
        """Este es el 'Sello Fijo' que se estampará en todas las páginas."""
        canvas.saveState()
        ancho, alto = letter
        
        # 1. ENCABEZADO A TRES COLUMNAS
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
        
        # 2. FECHA DE EMISIÓN
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        hoy = datetime.now()
        fecha_texto = f"CIUDAD VARYNA, {hoy.day:02d} de {meses[hoy.month-1]} del {hoy.year}"
        
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(ancho - 40, alto - 90, fecha_texto)
        
        # 3. LÍNEA SEPARADORA ELEGANTE
        canvas.setLineWidth(1)
        canvas.line(40, alto - 100, ancho - 40, alto - 100)
        
        # 4. PIE DE PÁGINA (Número de página abajo al centro)
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(ancho / 2, 30, f"Página {doc.page}")
        
        canvas.restoreState()

    @staticmethod
    def generar_reporte_tabla(ruta_archivo, titulo_reporte, encabezados, datos_filas):
        """
        El Maquetador. Toma los datos y construye el PDF completo.
        """
        # Configuramos la hoja de papel con márgenes grandes arriba para no chocar con el membrete
        doc = SimpleDocTemplate(ruta_archivo, pagesize=letter,
                                rightMargin=40, leftMargin=40,
                                topMargin=120, bottomMargin=50)
        
        elementos = [] # Aquí iremos metiendo los bloques de contenido
        estilos = getSampleStyleSheet()
        
        # --- TÍTULO DEL REPORTE ---
        estilo_titulo = estilos['Heading2']
        estilo_titulo.alignment = 1 # 1 = Centrado
        titulo = Paragraph(f"<b>{titulo_reporte}</b>", estilo_titulo)
        elementos.append(titulo)
        elementos.append(Spacer(1, 15)) # Espacio en blanco debajo del título
        
        # --- LA TABLA DE DATOS ---
        # Unimos los títulos de las columnas con los datos reales
        tabla_completa = [encabezados] + datos_filas
        
        # repeatRows=1 hace que si la tabla es muy larga, los títulos se repitan en la página 2
        tabla_pdf = Table(tabla_completa, repeatRows=1) 
        
        # AQUI OCURRE LA MAGIA DE LOS BORDES
        estilo_tabla = TableStyle([
            # Fila de Títulos (Fondo gris claro, texto centrado)
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#d5d8dc")),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            
            # Formato general
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            
            # ¡TODOS LOS BORDES! (Líneas negras sólidas)
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        tabla_pdf.setStyle(estilo_tabla)
        
        elementos.append(tabla_pdf)
        
        # Construimos el PDF ordenándole que use nuestro membrete en todas las páginas
        doc.build(elementos, onFirstPage=ImprentaPDF.dibujar_membrete, onLaterPages=ImprentaPDF.dibujar_membrete)