# scripts/generar_manual_usuario.py
"""
Generador del Manual de Usuario Institucional en formato PDF (ReportLab Platypus).

Sistema de Información para la Gestión de Asistencia Estudiantil
Complejo Educativo "Colinas del Llano" — Coordinación de 4to Año, Barinas, Venezuela.

Uso:
    .venv/bin/python scripts/generar_manual_usuario.py
"""

from __future__ import annotations

import os
import sys
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


# ═══════════════════════════════════════════════════════════════════════════
# RUTAS Y PALETA INSTITUCIONAL
# ═══════════════════════════════════════════════════════════════════════════
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_LOGO = os.path.join(RAIZ_PROYECTO, "LOGOLICEO.png")
RUTA_SALIDA_DEFAULT = os.path.join(
    RAIZ_PROYECTO, "Manual_Usuario_Sistema_Asistencia_v1.0.0.pdf"
)

COLOR_PRIMARIO = colors.HexColor("#2C3E50")
COLOR_PRIMARIO_OSCURO = colors.HexColor("#1A252F")
COLOR_SECUNDARIO = colors.HexColor("#2980B9")
COLOR_ACENTO = colors.HexColor("#27AE60")
COLOR_ADVERTENCIA = colors.HexColor("#D68910")
COLOR_PELIGRO = colors.HexColor("#C0392B")
COLOR_FONDO_NEUTRO = colors.HexColor("#F4F6F9")
COLOR_FILA_ZEBRA = colors.HexColor("#F2F4F7")
COLOR_BORDE = colors.HexColor("#D5DBDB")
COLOR_TEXTO = colors.HexColor("#2C3E50")
COLOR_TEXTO_SUAVE = colors.HexColor("#566573")

COLOR_CONSEJO_BG = colors.HexColor("#EAFAF1")
COLOR_NOTA_BG = colors.HexColor("#EBF5FB")
COLOR_ALERTA_BG = colors.HexColor("#FDEDEC")
COLOR_AVISO_AMBAR_BG = colors.HexColor("#FEF9E7")

AUTORES_COMPLETOS = (
    "César Manuel Meléndez Berríos",
    "Michelle Josefina Díaz Bastidas",
    "Renzo Gabriel Meléndez Berríos",
    "César Miguel González Terán",
)

CONTACTO_SOPORTE_NOMBRE = "César Meléndez"
CONTACTO_SOPORTE_EMAIL = "melendezcesar122@gmail.com"
CONTACTO_SOPORTE_TEL = "+58 414-5446824"


# ═══════════════════════════════════════════════════════════════════════════
# PLANTILLA DE DOCUMENTO CON TABLA DE CONTENIDOS AUTOMÁTICA
# ═══════════════════════════════════════════════════════════════════════════
class ManualDocTemplate(BaseDocTemplate):
    """Documento ReportLab con registro automático de capítulos y subsecciones en el índice."""

    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        ancho, alto = letter
        frame_portada = Frame(
            42, 42, ancho - 84, alto - 84, id="frame_portada", showBoundary=0
        )
        frame_contenido = Frame(
            48, 56, ancho - 96, alto - 120, id="frame_contenido", showBoundary=0
        )
        self.addPageTemplates(
            [
                PageTemplate(
                    id="Portada",
                    frames=[frame_portada],
                    onPage=_dibujar_fondo_portada,
                ),
                PageTemplate(
                    id="Contenido",
                    frames=[frame_contenido],
                    onPage=_dibujar_encabezado_y_pie,
                ),
            ]
        )

    def afterFlowable(self, flowable):
        """Notifica a la TableOfContents los títulos de nivel 0 (Capítulos) y nivel 1 (Secciones)."""
        if isinstance(flowable, Paragraph):
            estilo = flowable.style.name
            texto = flowable.getPlainText()
            if estilo == "TituloCapitulo":
                clave = f"cap_{len(texto)}_{abs(hash(texto))}"
                self.canv.bookmarkPage(clave)
                self.notify("TOCEntry", (0, texto, self.page, clave))
            elif estilo == "TituloSeccion":
                clave = f"sec_{len(texto)}_{abs(hash(texto))}"
                self.canv.bookmarkPage(clave)
                self.notify("TOCEntry", (1, texto, self.page, clave))


def _dibujar_fondo_portada(canvas, doc):
    """Dibuja el marco institucional superior e inferior de la portada."""
    canvas.saveState()
    ancho, alto = letter

    # Franja superior institucional
    canvas.setFillColor(COLOR_PRIMARIO)
    canvas.rect(0, alto - 108, ancho, 108, fill=1, stroke=0)

    # Línea dorada/verde acento bajo la franja
    canvas.setFillColor(COLOR_ACENTO)
    canvas.rect(0, alto - 113, ancho, 5, fill=1, stroke=0)

    # Membrete en franja superior
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(
        ancho / 2, alto - 34, "REPÚBLICA BOLIVARIANA DE VENEZUELA"
    )
    canvas.setFont("Helvetica", 9.5)
    canvas.drawCentredString(
        ancho / 2, alto - 50, "MINISTERIO DEL PODER POPULAR PARA LA EDUCACIÓN"
    )
    canvas.setFont("Helvetica-Bold", 11.5)
    canvas.drawCentredString(
        ancho / 2, alto - 70, 'COMPLEJO EDUCATIVO "COLINAS DEL LLANO"'
    )
    canvas.setFont("Helvetica", 9.5)
    canvas.drawCentredString(
        ancho / 2, alto - 86, "Coordinación de 4to Año  •  Estado Barinas, Venezuela"
    )

    # Franja inferior discreta
    canvas.setFillColor(COLOR_PRIMARIO_OSCURO)
    canvas.rect(0, 0, ancho, 28, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#D5D8DC"))
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(
        ancho / 2,
        10,
        'Documento Oficial de Operación y Soporte  •  Complejo Educativo "Colinas del Llano"  •  2026',
    )
    canvas.restoreState()


def _dibujar_encabezado_y_pie(canvas, doc):
    """Dibuja el encabezado corriente y el pie de página numerado en páginas interiores."""
    canvas.saveState()
    ancho, alto = letter

    # Encabezado corriente
    canvas.setFillColor(COLOR_PRIMARIO)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawString(48, alto - 38, 'Complejo Educativo "Colinas del Llano" — Barinas')
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(COLOR_TEXTO_SUAVE)
    canvas.drawRightString(
        ancho - 48, alto - 38, "Manual de Usuario  |  Versión 1.0.0"
    )
    canvas.setStrokeColor(COLOR_SECUNDARIO)
    canvas.setLineWidth(1.0)
    canvas.line(48, alto - 45, ancho - 48, alto - 45)

    # Pie de página
    canvas.setStrokeColor(COLOR_BORDE)
    canvas.setLineWidth(0.75)
    canvas.line(48, 42, ancho - 48, 42)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(COLOR_TEXTO_SUAVE)
    canvas.drawString(
        48, 28, "Sistema de Gestión de Asistencia Estudiantil  •  Licencia GNU GPLv3"
    )
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.setFillColor(COLOR_PRIMARIO)
    canvas.drawRightString(ancho - 48, 28, f"Página {doc.page}")

    canvas.restoreState()


# ═══════════════════════════════════════════════════════════════════════════
# ESTILOS TIPOGRÁFICOS Y COMPONENTES VISUALES REUTILIZABLES
# ═══════════════════════════════════════════════════════════════════════════
def crear_estilos() -> dict[str, ParagraphStyle]:
    """Define la hoja de estilos institucional del manual."""
    base = getSampleStyleSheet()
    estilos: dict[str, ParagraphStyle] = {}

    estilos["PortadaSuper"] = ParagraphStyle(
        "PortadaSuper",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=COLOR_SECUNDARIO,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    estilos["PortadaTitulo"] = ParagraphStyle(
        "PortadaTitulo",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=31,
        textColor=COLOR_PRIMARIO,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    estilos["PortadaSubtitulo"] = ParagraphStyle(
        "PortadaSubtitulo",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13.5,
        leading=18,
        textColor=COLOR_TEXTO,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    estilos["PortadaPlantel"] = ParagraphStyle(
        "PortadaPlantel",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=COLOR_TEXTO_SUAVE,
        alignment=TA_CENTER,
        spaceAfter=14,
    )
    estilos["TituloTOC"] = ParagraphStyle(
        "TituloTOC",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=COLOR_PRIMARIO,
        spaceBefore=0,
        spaceAfter=6,
    )
    estilos["TOCNivel0"] = ParagraphStyle(
        "TOCNivel0",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.8,
        leading=12.5,
        leftIndent=0,
        firstLineIndent=0,
        textColor=COLOR_PRIMARIO,
        spaceBefore=3,
        spaceAfter=1,
    )
    estilos["TOCNivel1"] = ParagraphStyle(
        "TOCNivel1",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=11.0,
        leftIndent=16,
        firstLineIndent=0,
        textColor=COLOR_TEXTO_SUAVE,
        spaceBefore=0,
        spaceAfter=0,
    )
    estilos["TituloCapitulo"] = ParagraphStyle(
        "TituloCapitulo",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.white,
        backColor=COLOR_PRIMARIO,
        borderPadding=(7, 10, 7, 10),
        spaceBefore=6,
        spaceAfter=10,
        keepWithNext=True,
    )
    estilos["TituloSeccion"] = ParagraphStyle(
        "TituloSeccion",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=COLOR_SECUNDARIO,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True,
    )
    estilos["SubtituloMenor"] = ParagraphStyle(
        "SubtituloMenor",
        parent=base["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=COLOR_PRIMARIO,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )
    estilos["Cuerpo"] = ParagraphStyle(
        "Cuerpo",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.8,
        leading=14,
        textColor=COLOR_TEXTO,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    estilos["Lista"] = ParagraphStyle(
        "Lista",
        parent=estilos["Cuerpo"],
        leftIndent=16,
        firstLineIndent=-10,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    estilos["TablaHeader"] = ParagraphStyle(
        "TablaHeader",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.8,
        leading=11.5,
        textColor=colors.white,
        alignment=TA_LEFT,
    )
    estilos["TablaCelda"] = ParagraphStyle(
        "TablaCelda",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.6,
        leading=11.5,
        textColor=COLOR_TEXTO,
        alignment=TA_LEFT,
    )
    estilos["TablaCeldaCentro"] = ParagraphStyle(
        "TablaCeldaCentro",
        parent=estilos["TablaCelda"],
        alignment=TA_CENTER,
    )
    estilos["CajaTitulo"] = ParagraphStyle(
        "CajaTitulo",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        spaceAfter=2,
    )
    estilos["CajaTexto"] = ParagraphStyle(
        "CajaTexto",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=13,
        textColor=COLOR_TEXTO,
        alignment=TA_LEFT,
    )
    estilos["Formula"] = ParagraphStyle(
        "Formula",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=COLOR_PRIMARIO,
        alignment=TA_CENTER,
    )
    return estilos


def caja_aviso(
    titulo: str,
    contenido_html: str,
    estilos: dict[str, ParagraphStyle],
    tipo: str = "nota",
) -> KeepTogether:
    """Construye un recuadro institucional de Consejo, Nota Importante o Advertencia."""
    config = {
        "consejo": (COLOR_ACENTO, COLOR_CONSEJO_BG, "CONSEJO PRÁCTICO"),
        "nota": (COLOR_SECUNDARIO, COLOR_NOTA_BG, "NOTA IMPORTANTE"),
        "advertencia": (COLOR_PELIGRO, COLOR_ALERTA_BG, "ADVERTENCIA DE SEGURIDAD"),
        "atencion": (COLOR_ADVERTENCIA, COLOR_AVISO_AMBAR_BG, "ATENCIÓN"),
    }
    borde, fondo, prefijo = config.get(tipo, config["nota"])
    titulo_completo = f"{prefijo}: {escape(titulo)}" if titulo else prefijo

    st_tit = ParagraphStyle(
        f"CajaTit_{tipo}",
        parent=estilos["CajaTitulo"],
        textColor=borde,
    )
    p_tit = Paragraph(titulo_completo, st_tit)
    p_txt = Paragraph(contenido_html, estilos["CajaTexto"])

    ancho_util = letter[0] - 96
    tabla = Table([[p_tit], [p_txt]], colWidths=[ancho_util])
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), fondo),
                ("LINEBEFORE", (0, 0), (0, -1), 4, borde),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, 0), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 1),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 7),
            ]
        )
    )
    return KeepTogether([tabla, Spacer(1, 7)])


def tabla_estilizada(
    encabezados: list[str],
    filas: list[list[str]],
    anchos_pt: list[float],
    estilos: dict[str, ParagraphStyle],
    centrar_cols: set[int] | None = None,
) -> Table:
    """Construye una tabla con encabezado azul institucional y filas tipo zebra."""
    centrar_cols = centrar_cols or set()
    data: list[list[Paragraph]] = []

    fila_hdr = [
        Paragraph(f"<b>{escape(h)}</b>", estilos["TablaHeader"]) for h in encabezados
    ]
    data.append(fila_hdr)

    for fila in filas:
        celdas = []
        for idx, valor in enumerate(fila):
            estilo = (
                estilos["TablaCeldaCentro"]
                if idx in centrar_cols
                else estilos["TablaCelda"]
            )
            celdas.append(Paragraph(valor, estilo))
        data.append(celdas)

    t = Table(data, colWidths=anchos_pt, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_FILA_ZEBRA]),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return t


def bullet(texto_html: str, estilos: dict[str, ParagraphStyle]) -> Paragraph:
    """Elemento de lista con viñeta limpia."""
    return Paragraph(f"&bull;&nbsp; {texto_html}", estilos["Lista"])


def paso(num: int, texto_html: str, estilos: dict[str, ParagraphStyle]) -> Paragraph:
    """Elemento de lista numerada en negrita."""
    return Paragraph(f"<b>{num}.</b>&nbsp; {texto_html}", estilos["Lista"])


# ═══════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN DE PORTADA E ÍNDICE
# ═══════════════════════════════════════════════════════════════════════════
def agregar_portada(story: list, estilos: dict[str, ParagraphStyle]):
    """Construye la Portada Institucional con el escudo LOGOLICEO.png y créditos."""
    story.append(Spacer(1, 95))

    # Escudo institucional proporcional
    if os.path.exists(RUTA_LOGO):
        logo = Image(RUTA_LOGO, width=148, height=117, kind="proportional")
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 18))

    story.append(Paragraph("DOCUMENTACIÓN OFICIAL DE USUARIO", estilos["PortadaSuper"]))
    story.append(Paragraph("MANUAL DE USUARIO", estilos["PortadaTitulo"]))
    story.append(
        Paragraph(
            "Sistema de Información para la Gestión de Asistencia Estudiantil",
            estilos["PortadaSubtitulo"],
        )
    )
    story.append(
        Paragraph(
            'Complejo Educativo "Colinas del Llano" — Coordinación de 4to Año<br/>Barinas, Estado Barinas, Venezuela',
            estilos["PortadaPlantel"],
        )
    )

    # Insignia de versión y año
    ancho_util = letter[0] - 84
    badge_tbl = Table(
        [
            [
                Paragraph(
                    "<b>Versión:</b> 1.0.0 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Año de Publicación:</b> 2026 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Operación:</b> 100% Offline &nbsp;&nbsp;|&nbsp;&nbsp; <b>Licencia:</b> GNU GPLv3",
                    ParagraphStyle(
                        "BadgePortada",
                        fontName="Helvetica",
                        fontSize=9.2,
                        leading=13,
                        textColor=COLOR_PRIMARIO,
                        alignment=TA_CENTER,
                    ),
                )
            ]
        ],
        colWidths=[ancho_util],
    )
    badge_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_FONDO_NEUTRO),
                ("BOX", (0, 0), (-1, -1), 0.8, COLOR_SECUNDARIO),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(badge_tbl)
    story.append(Spacer(1, 26))

    # Cuadro de Equipo Desarrollador y Contacto Técnico
    autores_html = "<br/>".join(f"&bull;&nbsp; {escape(a)}" for a in AUTORES_COMPLETOS)
    cuadro_creditos = Table(
        [
            [
                Paragraph(
                    "<b>EQUIPO DESARROLLADOR Y CONTACTO TÉCNICO</b>",
                    ParagraphStyle(
                        "CredHdr",
                        fontName="Helvetica-Bold",
                        fontSize=9.5,
                        leading=12,
                        textColor=colors.white,
                        alignment=TA_CENTER,
                    ),
                )
            ],
            [
                Paragraph(
                    f"<b>Autores / Desarrolladores:</b><br/>{autores_html}<br/><br/>"
                    f"<b>Soporte Técnico Oficial:</b> {escape(CONTACTO_SOPORTE_NOMBRE)}<br/>"
                    f"<b>Correo Electrónico:</b> {escape(CONTACTO_SOPORTE_EMAIL)} &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"<b>Teléfono:</b> {escape(CONTACTO_SOPORTE_TEL)}",
                    ParagraphStyle(
                        "CredBody",
                        fontName="Helvetica",
                        fontSize=9.3,
                        leading=14,
                        textColor=COLOR_TEXTO,
                        alignment=TA_LEFT,
                    ),
                )
            ],
        ],
        colWidths=[ancho_util],
    )
    cuadro_creditos.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), COLOR_PRIMARIO),
                ("BACKGROUND", (0, 1), (0, 1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, COLOR_PRIMARIO),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, 0), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                ("TOPPADDING", (0, 1), (-1, 1), 10),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
            ]
        )
    )
    story.append(cuadro_creditos)

    # Cambio a plantilla de páginas interiores
    story.append(NextPageTemplate("Contenido"))
    story.append(PageBreak())


def agregar_tabla_contenidos(story: list, estilos: dict[str, ParagraphStyle]):
    """Inserta la Tabla de Contenidos autogenerada con números de página exactos."""
    story.append(Paragraph("TABLA DE CONTENIDOS", estilos["TituloTOC"]))
    story.append(
        Paragraph(
            "Índice general de capítulos y secciones operativas del sistema.",
            estilos["Cuerpo"],
        )
    )
    story.append(Spacer(1, 6))

    toc = TableOfContents()
    toc.levelStyles = [estilos["TOCNivel0"], estilos["TOCNivel1"]]
    toc.dotsMinLevel = 0
    toc.tableStyle = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ]
    )
    story.append(toc)
    story.append(PageBreak())


# ═══════════════════════════════════════════════════════════════════════════
# REDACCIÓN DE LOS 10 CAPÍTULOS (100% FIEL AL CÓDIGO FUENTE REAL)
# ═══════════════════════════════════════════════════════════════════════════
def agregar_capitulos(story: list, estilos: dict[str, ParagraphStyle]):
    """Agrega los 10 capítulos técnicos y didácticos verificados en el código real."""
    ancho_util = letter[0] - 96

    # ── CAPÍTULO 1 ────────────────────────────────────────────────────────
    story.append(
        Paragraph(
            "Capítulo 1 — Introducción y Requisitos del Equipo",
            estilos["TituloCapitulo"],
        )
    )
    story.append(
        Paragraph("1.1 Propósito del Sistema y Operación 100% Offline", estilos["TituloSeccion"])
    )
    story.append(
        Paragraph(
            'El <b>Sistema de Información para la Gestión de Asistencia Estudiantil</b> ha sido diseñado '
            'específicamente para la Coordinación de 4to Año y el personal directivo, administrativo y docente del '
            '<b>Complejo Educativo "Colinas del Llano"</b> (Barinas, Venezuela). Su objetivo principal es digitalizar, '
            'agilizar y resguardar el control diario de asistencia por materia y sección, emitir fichas técnicas oficiales '
            'y alertar oportunamente sobre estudiantes en riesgo de reprobación conforme al <b>Artículo 109 del Reglamento '
            'General de la Ley Orgánica de Educación (RGLOE)</b>, el cual exige un mínimo del <b>75% de asistencia efectiva</b>.',
            estilos["Cuerpo"],
        )
    )
    story.append(
        Paragraph(
            'La aplicación opera de manera <b>100% offline (sin conexión a Internet)</b> y es completamente portable. '
            'Toda la información escolar se almacena de forma local en una base de datos embebida (<b>sistema_escolar.db</b>), '
            'junto con fotografías optimizadas en la carpeta <b>fotos/</b> y un respaldo automático ante apagones en '
            '<b>memoria_emergencia.json</b>.',
            estilos["Cuerpo"],
        )
    )

    story.append(Paragraph("1.2 Requisitos Mínimos de Hardware y Software", estilos["TituloSeccion"]))
    story.append(
        tabla_estilizada(
            ["Componente", "Requisito Mínimo / Recomendado"],
            [
                ["Sistema Operativo", "Windows 10 / Windows 11 (64 bits) o Linux Mint 21.x / 22.x."],
                ["Procesador y Memoria RAM", "Procesador de doble núcleo (o superior) y mínimo <b>2 GB de RAM</b>."],
                ["Espacio en Disco", "Al menos <b>150 MB</b> libres en la carpeta Documentos para el programa, base de datos, fotos y reportes PDF."],
                ["Resolución de Pantalla", "Mínimo <b>1024 × 768 píxeles</b> (ventanas principales optimizadas en modo maximizado)."],
                ["Software Adicional", "Lector de archivos PDF (navegador web moderno, Adobe Reader o lector del sistema) para visualizar reportes y fichas exportadas. No requiere instalar Python ni conexión a Internet."],
            ],
            [ancho_util * 0.32, ancho_util * 0.68],
            estilos,
        )
    )
    story.append(Spacer(1, 8))

    story.append(Paragraph("1.3 Convenciones Visuales del Manual", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "A lo largo de este manual encontrará recuadros destacados y el nombre exacto en <b>negrita</b> de los botones, pestañas y campos tal como aparecen en las ventanas del programa (en la interfaz gráfica, estos controles muestran además pequeños iconos ilustrativos junto al texto):",
            estilos["Cuerpo"],
        )
    )
    story.append(
        caja_aviso(
            "Uso de consejos en este manual",
            "Los recuadros verdes de <b>Consejo Práctico</b> ofrecen atajos de teclado o recomendaciones para agilizar el trabajo diario de coordinación y docencia.",
            estilos,
            tipo="consejo",
        )
    )
    story.append(
        caja_aviso(
            "Reglas operativas importantes",
            "Los recuadros azules de <b>Nota Importante</b> detallan reglas automáticas del sistema, fórmulas legales o ubicación de archivos.",
            estilos,
            tipo="nota",
        )
    )
    story.append(
        caja_aviso(
            "Acciones críticas o de seguridad",
            "Los recuadros rojos de <b>Advertencia de Seguridad</b> señalan operaciones delicadas, como el borrado lógico, el cambio de credenciales o la promoción anual irreversible.",
            estilos,
            tipo="advertencia",
        )
    )

    # ── CAPÍTULO 2 ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(
        Paragraph(
            "Capítulo 2 — Instalación y Primer Arranque",
            estilos["TituloCapitulo"],
        )
    )
    story.append(Paragraph("2.1 Instalación en Windows 10 / 11 (Instalador Oficial)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "El paquete oficial de distribución para Windows se entrega mediante el instalador <b>Instalar_ColinasDelLlano_Windows.exe</b> "
            "(desde CD, pendrive o carpeta compartida). No requiere permisos de administrador para instalarse en el equipo de usuario:",
            estilos["Cuerpo"],
        )
    )
    story.append(paso(1, "Inserte el CD o conecte el pendrive de instalación y haga doble clic en <b>Instalar_ColinasDelLlano_Windows.exe</b>.", estilos))
    story.append(
        paso(
            2,
            'Si aparece la ventana azul de seguridad <b>Windows Defender SmartScreen ("Windows protegió su PC")</b>, es un comportamiento normal porque el ejecutable institucional no posee firma comercial de pago. Haga clic en <b>"Más información"</b> y luego en el botón <b>"Ejecutar de todas formas"</b>.',
            estilos,
        )
    )
    story.append(paso(3, "En el asistente de instalación en español, lea y acepte los términos de la licencia libre <b>GNU GPLv3</b>.", estilos))
    story.append(
        paso(
            4,
            "Confirme la carpeta de destino predeterminada: <b>Documentos\\Sistema_Asistencia_Colinas</b> (no requiere privilegios de administrador). Marque la casilla para crear un acceso directo en el <b>Escritorio</b> si lo desea y presione <b>Instalar</b>.",
            estilos,
        )
    )
    story.append(paso(5, "Al finalizar, haga clic en <b>Finalizar</b> para abrir el programa o utilice el acceso directo <b>Sistema de Asistencia Colinas del Llano</b> en su Escritorio.", estilos))

    story.append(
        caja_aviso(
            "Actualizaciones seguras sin pérdida de datos",
            "Tanto el instalador de Windows como el de Linux Mint están configurados para actualizar únicamente el programa conservando intactos la base de datos <b>sistema_escolar.db</b>, la carpeta <b>fotos/</b> y el respaldo <b>memoria_emergencia.json</b>.",
            estilos,
            tipo="nota",
        )
    )

    story.append(Paragraph("2.2 Despliegue en Linux Mint (21.x / 22.x)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "En equipos institucionales con Linux Mint, la instalación se realiza sin usuario administrador (sin <i>root</i>) mediante el script oficial <b>Instalar_en_Mint.sh</b>:",
            estilos["Cuerpo"],
        )
    )
    story.append(paso(1, "Ubique la carpeta de distribución que contiene <b>sistema_escolar</b>, la carpeta <b>_internal/</b> y el script <b>Instalar_en_Mint.sh</b>.", estilos))
    story.append(paso(2, "Haga doble clic sobre <b>Instalar_en_Mint.sh</b> (o ejecútelo desde terminal con <b>./Instalar_en_Mint.sh</b>).", estilos))
    story.append(paso(3, "El instalador copiará los archivos a <b>~/Documentos/Sistema_Asistencia_Colinas</b> y creará automáticamente el lanzador en el <b>Escritorio</b> y en el <b>Menú de Aplicaciones</b> (categoría Educación / Oficina).", estilos))

    story.append(Paragraph("2.3 Primer Inicio de Sesión y Credenciales Iniciales", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "La primera vez que se ejecuta el sistema, se crea automáticamente la base de datos local con una cuenta de administrador inicial:",
            estilos["Cuerpo"],
        )
    )
    story.append(bullet("<b>Usuario inicial:</b> <font name='Courier'>admin</font>", estilos))
    story.append(bullet("<b>Contraseña inicial:</b> <font name='Courier'>1234</font> (Rol: <b>ADMIN</b>)", estilos))
    story.append(Spacer(1, 3))
    story.append(
        caja_aviso(
            "Cambio obligatorio de la contraseña inicial",
            "Por seguridad institucional, inmediatamente después de iniciar sesión por primera vez, ingrese al módulo <b>Seguridad (Gestión de Usuarios)</b> o utilice la opción de recuperación en el Login para cambiar la contraseña por defecto <font name='Courier'>1234</font> por una clave personal segura.",
            estilos,
            tipo="advertencia",
        )
    )

    # ── CAPÍTULO 3 ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(
        Paragraph(
            "Capítulo 3 — Acceso al Sistema y Seguridad (Login)",
            estilos["TituloCapitulo"],
        )
    )
    story.append(Paragraph("3.1 Inicio de Sesión y Atajos de Teclado", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            'Al abrir el programa se presenta la ventana compacta <b>"Acceso al Sistema — Colinas del Llano"</b>. Para ingresar:',
            estilos["Cuerpo"],
        )
    )
    story.append(paso(1, "Escriba su identificador en el campo <b>Nombre de Usuario:</b> y presione la tecla <b>Enter</b> (o haga clic en el siguiente campo).", estilos))
    story.append(paso(2, "Escriba su clave en el campo <b>Contraseña:</b>. Si desea verificar lo escrito antes de entrar, active la casilla <b>Mostrar contraseña</b>.", estilos))
    story.append(paso(3, "Haga clic en el botón <b>INICIAR SESIÓN</b> o presione <b>Enter</b> directamente desde el campo de contraseña.", estilos))
    story.append(
        Paragraph(
            "Todas las contraseñas se protegen localmente con cifrado criptográfico seguro (<b>PBKDF2-HMAC-SHA256</b>). Si la cuenta está inactiva o las credenciales no coinciden, el sistema mostrará el aviso <i>\"Usuario o contraseña incorrectos, o cuenta de usuario inactiva.\"</i>. Las ventanas emergentes de registro o recuperación se cierran rápidamente con la tecla <b>Escape</b>.",
            estilos["Cuerpo"],
        )
    )

    story.append(Paragraph("3.2 Registro Rápido de Nueva Cuenta", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "En la parte inferior de la tarjeta de acceso existe el enlace <b>Registrar Nuevo Usuario</b> (bajo la pregunta <i>\"¿Requiere una nueva cuenta de acceso?\"</i>). Esta vía rápida permite habilitar una cuenta nueva sin entrar al panel principal:",
            estilos["Cuerpo"],
        )
    )
    story.append(paso(1, "Haga clic en <b>Registrar Nuevo Usuario</b>.", estilos))
    story.append(paso(2, "Ingrese la <b>Clave Maestra Institucional (resguardada exclusivamente por la Dirección/Coordinación)</b> en el diálogo de autorización.", estilos))
    story.append(paso(3, "En la ventana <b>Alta de Nuevo Usuario</b> complete: <b>Nombre Completo:</b>, <b>Nombre de Usuario (Login):</b> (mínimo 4 caracteres), <b>Contraseña:</b> (mínimo 4 caracteres; puede activar <b>Mostrar contraseña</b>) y seleccione el <b>Rol de Acceso (RBAC):</b> (<b>DOCENTE</b>, <b>ASISTENTE</b> o <b>ADMIN</b>).", estilos))
    story.append(paso(4, "Pulse <b>GUARDAR USUARIO</b> (o navegue entre cajas con <b>Enter</b>).", estilos))

    story.append(Paragraph("3.3 Recuperación Offline de Usuario o Contraseña (en 2 Pasos)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "Si un integrante del plantel olvida su nombre de usuario o su contraseña, puede restablecer su acceso sin conexión a Internet desde el enlace <b>¿Olvidó su usuario o contraseña?</b>:",
            estilos["Cuerpo"],
        )
    )
    story.append(paso(1, "<b>Paso 1 — Autorización:</b> En la ventana <b>Recuperación Offline de Credenciales</b>, escriba la <b>Clave Maestra Institucional (resguardada exclusivamente por la Dirección/Coordinación)</b> y haga clic en <b>Validar Clave Maestra</b> (o presione <b>Enter</b>).", estilos))
    story.append(paso(2, "<b>Paso 2 — Consulta y Restablecimiento:</b> Una vez validada, se habilitará el desplegable <b>Usuario Activo (consulta y restablecimiento):</b> mostrando cada usuario junto a su rol (<font name='Courier'>usuario - ROL</font>). Seleccione la cuenta, escriba la <b>Nueva Contraseña:</b> y repítala en <b>Confirmar Contraseña:</b> (puede marcar <b>Mostrar contraseñas</b>) y pulse <b>Restablecer Contraseña</b>.", estilos))
    story.append(
        Paragraph(
            "Cada restablecimiento queda registrado automáticamente en la tabla interna de auditoría del sistema y coloca al usuario listo en la pantalla de Login para iniciar sesión de inmediato.",
            estilos["Cuerpo"],
        )
    )

    # ── CAPÍTULO 4 ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(
        Paragraph(
            "Capítulo 4 — Panel de Control y Matriz de Roles (RBAC)",
            estilos["TituloCapitulo"],
        )
    )
    story.append(Paragraph("4.1 Navegación en el Panel de Control (Dashboard)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            'Tras autenticarse correctamente, se abre maximizada la ventana <b>"Panel de Control — Complejo Educativo Colinas del Llano"</b>. Consta de dos áreas principales:',
            estilos["Cuerpo"],
        )
    )
    story.append(
        bullet(
            "<b>Panel Lateral Izquierdo:</b> Muestra el escudo del plantel, el nombre del Complejo Educativo, el nombre completo del usuario activo, su insignia de rol en color distintivo (<b>ADMIN</b> verde, <b>ASISTENTE</b> azul, <b>DOCENTE</b> naranja), el botón <b>Acerca de</b> (icono informativo; habilitado para todos los roles para consultar equipo desarrollador, contacto de soporte, marco normativo y licencias) y el botón <b>Cerrar Sesión</b> en la parte inferior para regresar de forma segura al Login.",
            estilos,
        )
    )
    story.append(
        bullet(
            "<b>Área Central de Módulos:</b> Presenta 8 tarjetas de acceso organizadas en cuadrícula. Los módulos autorizados para su rol se muestran activos con banda de color lateral; los módulos restringidos aparecen atenuados con la etiqueta <b>Sin acceso</b>.",
            estilos,
        )
    )
    story.append(
        bullet(
            "<b>Botón Volver al Panel (barra superior):</b> Todas las ventanas de los módulos se abren maximizadas e incluyen en su barra superior el botón <b>Volver al Panel</b> (acompañado de flecha de retorno) para cerrar el módulo actual y devolver el foco al Panel de Control.",
            estilos,
        )
    )

    story.append(Paragraph("4.2 Matriz Oficial de Permisos por Rol (RBAC)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "El control de acceso por roles garantiza la seguridad de los datos académicos y administrativos de acuerdo con el perfil asignado a cada usuario:",
            estilos["Cuerpo"],
        )
    )
    story.append(
        tabla_estilizada(
            ["Módulo en Panel de Control", "Descripción Funcional", "ADMIN", "ASISTENTE", "DOCENTE"],
            [
                ["Gestión Académica", "Registro de profesores y asignación de materias/secciones", "<b>Permitido</b>", "Sin acceso", "Sin acceso"],
                ["Inscripciones", "Expedientes de estudiantes, núcleo familiar, foto y ficha PDF", "<b>Permitido</b>", "<b>Permitido</b>", "Sin acceso"],
                ["Pasar Lista", "Toma diaria de asistencia (P / A / J) y respaldo anti-apagones", "<b>Permitido</b>", "<b>Permitido</b>", "<b>Permitido</b>"],
                ["Listados", "Consulta en vivo y PDF de alumnos, materias y profesores", "<b>Permitido</b>", "<b>Permitido</b>", "<b>Permitido</b>"],
                ["Reportes", "Reportes diario/mensual/historial, Art. 109 RGLOE y alertas", "<b>Permitido</b>", "<b>Permitido</b>", "Sin acceso"],
                ["Estadísticas", "Tarjetas KPI, gráficos por sección/género y tabla de riesgo", "<b>Permitido</b>", "<b>Permitido</b>", "Sin acceso"],
                ["Promoción Anual", "Cierre de año escolar y promoción en cascada 5to a 1ro", "<b>Permitido</b>", "Sin acceso", "Sin acceso"],
                ["Seguridad", "Administración de cuentas de usuario y asignación de roles", "<b>Permitido</b>", "Sin acceso", "Sin acceso"],
            ],
            [ancho_util * 0.25, ancho_util * 0.39, ancho_util * 0.12, ancho_util * 0.12, ancho_util * 0.12],
            estilos,
            centrar_cols={2, 3, 4},
        )
    )
    story.append(Spacer(1, 8))

    # ── CAPÍTULO 5 ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(
        Paragraph(
            "Capítulo 5 — Gestión Académica (Docentes y Materias)",
            estilos["TituloCapitulo"],
        )
    )
    story.append(
        Paragraph(
            'El módulo <b>Gestión Académica</b> (exclusivo para rol <b>ADMIN</b>) abre la ventana <b>"Gestión Académica - Profesores y Clases"</b> dividida en dos pestañas superiores.',
            estilos["Cuerpo"],
        )
    )

    story.append(Paragraph("5.1 Pestaña: GESTIÓN DE PROFESORES", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "La pantalla se organiza en dos columnas: a la izquierda la tarjeta <b>EXPEDIENTE DOCENTE</b> y a la derecha la tabla <b>DOCENTES REGISTRADOS</b>.",
            estilos["Cuerpo"],
        )
    )
    story.append(bullet("<b>Cédula de Identidad:</b> Seleccione el prefijo (<b>V</b>, <b>E</b> o <b>P</b>) y escriba solo los números sin puntos (ej. <font name='Courier'>12345678</font>).", estilos))
    story.append(bullet("<b>Nombre Completo del Profesor:</b> Se convierte automáticamente a mayúsculas al escribir.", estilos))
    story.append(bullet("<b>Profesión / Título Académico:</b> Campo de texto libre en mayúsculas para registrar el título o especialidad del docente (ej. <i>LICENCIADO EN EDUCACIÓN MENCIÓN MATEMÁTICA</i>).", estilos))
    story.append(bullet("<b>Teléfono de Contacto:</b> Campo opcional para el número telefónico del docente.", estilos))
    story.append(
        bullet(
            "<b>Fotografía (110 × 110 px en vista previa):</b> Ingrese primero la cédula y presione <b>Cargar</b> para seleccionar una imagen (<font name='Courier'>.jpg</font>, <font name='Courier'>.jpeg</font>, <font name='Courier'>.png</font>, <font name='Courier'>.webp</font> o <font name='Courier'>.bmp</font>). El sistema la optimiza automáticamente a <b>240 × 240 px JPEG</b> y la guarda de forma portable en <b>fotos/profesores/</b>. Use <b>Quitar</b> para removerla.",
            estilos,
        )
    )
    story.append(Spacer(1, 3))
    story.append(Paragraph("<b>Botonera de Acciones (cuadrícula 2 × 2):</b>", estilos["Cuerpo"]))
    story.append(bullet("<b>GUARDAR:</b> Registra un nuevo profesor en la base de datos.", estilos))
    story.append(bullet("<b>ACTUALIZAR:</b> Guarda cambios tras hacer clic en un profesor de la tabla <b>DOCENTES REGISTRADOS</b> (columnas: <i>ID</i>, <i>Cédula</i>, <i>Nombre del Profesor</i>, <i>Profesión</i>, <i>Teléfono</i>).", estilos))
    story.append(bullet("<b>FICHA PDF:</b> Genera la Ficha Técnica Oficial del Docente en PDF incluyendo su fotografía y las materias que dicta.", estilos))
    story.append(bullet("<b>LIMPIAR:</b> Vacía el formulario y deselecciona la tabla para un nuevo registro.", estilos))
    story.append(
        caja_aviso(
            "Navegación rápida en el expediente docente",
            "Puede presionar la tecla <b>Enter</b> después de llenar cada campo del formulario para avanzar directamente al siguiente cuadro de texto.",
            estilos,
            tipo="consejo",
        )
    )

    story.append(Paragraph("5.2 Pestaña: ASIGNAR MATERIAS", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "Permite vincular asignaturas con un profesor titular, un año escolar y una o varias secciones simultáneamente desde la tarjeta <b>ASIGNACIÓN ACADÉMICA DE MATERIAS</b>:",
            estilos["Cuerpo"],
        )
    )
    story.append(paso(1, "Escriba el <b>Nombre de la Materia:</b> (ej. <i>MATEMÁTICAS</i>, <i>CASTELLANO</i>, <i>QUÍMICA</i>; se formatea en mayúsculas).", estilos))
    story.append(paso(2, "Seleccione el <b>Profesor Encargado:</b> en la lista desplegable de docentes activos.", estilos))
    story.append(paso(3, "Seleccione el <b>Año Escolar / Grado:</b> (desde <b>1 - 1er AÑO</b> hasta <b>5 - 5to AÑO</b>).", estilos))
    story.append(paso(4, "En <b>Secciones Destino: (Puede elegir varias)</b> haga clic sobre una o múltiples secciones del catálogo completo (<b>Sección A</b> hasta <b>Sección Z</b>).", estilos))
    story.append(paso(5, "Pulse <b>INSCRIBIR MATERIA</b>. El sistema registrará en lote la materia para todas las secciones marcadas y confirmará el número de secciones creadas.", estilos))

    # ── CAPÍTULO 6 ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(
        Paragraph(
            "Capítulo 6 — Gestión de Estudiantes (Inscripciones y Expedientes)",
            estilos["TituloCapitulo"],
        )
    )
    story.append(
        Paragraph(
            'El módulo <b>Inscripciones</b> (accesible para <b>ADMIN</b> y <b>ASISTENTE</b>) abre la ventana <b>"Gestión de Estudiantes — Inscripciones y Expedientes"</b> con el encabezado <b>EXPEDIENTES Y FICHAS TÉCNICAS DE ESTUDIANTES</b>.',
            estilos["Cuerpo"],
        )
    )

    story.append(Paragraph("6.1 Registro Completo y Núcleo Familiar", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "La tarjeta superior organiza la ficha estudiantil en tres bloques claramente definidos:",
            estilos["Cuerpo"],
        )
    )
    story.append(
        bullet(
            "<b>DATOS PERSONALES Y ACADÉMICOS:</b> <b>Cédula:</b> (prefijo <b>V/E/P</b> y número sin puntos), <b>Nombre Completo:</b> (mayúsculas automáticas), <b>Género:</b> (<b>M</b> o <b>F</b>), <b>F. Nac:</b> (selector calendario <font name='Courier'>dd/mm/yyyy</font>), <b>Año:</b> (número entero, ej. <font name='Courier'>1</font> a <font name='Courier'>5</font>), <b>Sec:</b> (<b>A–Z</b>), <b>Escol.:</b> (<i>Regular</i>, <i>Materia Pendiente</i> o <i>Repite</i>), <b>Turno:</b> (<i>Mañana</i> o <i>Tarde</i>) y <b>Cond:</b> (<i>Activo</i> o <i>Preinscrito</i>). Los campos obligatorios para guardar son Cédula, Nombre, Año Escolar y Sección.",
            estilos,
        )
    )
    story.append(
        bullet(
            "<b>NÚCLEO FAMILIAR Y REPRESENTACIÓN LEGAL:</b> Permite registrar al <b>Representante Legal:</b> y su <b>Teléfono Repr.:</b>, además del bloque familiar dedicado para <b>Madre:</b>, <b>Telf. Madre:</b>, <b>Padre:</b> y <b>Telf. Padre:</b>.",
            estilos,
        )
    )
    story.append(
        bullet(
            "<b>Fotografía:</b> Tras ingresar la cédula del estudiante, pulse <b>Cargar</b> para adjuntar su foto (se optimiza a <b>240 × 240 px JPEG</b> dentro de <b>fotos/estudiantes/</b>) o <b>Quitar</b> para retirarla.",
            estilos,
        )
    )

    story.append(Paragraph("6.2 Edición, Borrado Lógico y Ficha Estudiantil en PDF", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "Debajo del formulario se encuentra la botonera principal y la tabla de estudiantes activos (columnas: <i>Cédula</i>, <i>Nombre</i>, <i>F. Nac</i>, <i>Representante</i>, <i>Telf</i>, <i>Sexo</i>, <i>Escolaridad</i>, <i>Turno</i>, <i>Cond</i>, <i>Año</i>, <i>Sec</i>). Al hacer clic en cualquier fila, todos sus datos se cargan en el formulario:",
            estilos["Cuerpo"],
        )
    )
    story.append(bullet("<b>GUARDAR:</b> Inscribe un estudiante nuevo (impide cédulas duplicadas).", estilos))
    story.append(bullet("<b>MODIFICAR:</b> Actualiza los datos del estudiante seleccionado previamente en la tabla.", estilos))
    story.append(bullet("<b>ELIMINAR:</b> Solicita confirmación y ejecuta una desactivación por <b>borrado lógico</b> (<font name='Courier'>ESTADO_ACTIVO = 0</font>). El alumno deja de aparecer en nóminas activas y pases de lista, pero su historial previo de asistencias permanece intacto para auditorías.", estilos))
    story.append(bullet("<b>FICHA PDF:</b> Solicita dónde guardar el archivo (<font name='Courier'>Ficha_Estudiante_...</font>) y genera la Ficha Técnica Oficial del Estudiante en PDF, incluyendo fotografía, núcleo familiar y resumen estadístico de asistencia si posee registros. Al finalizar ofrece abrir el PDF de inmediato.", estilos))
    story.append(bullet("<b>LIMPIAR:</b> Restablece todos los campos a sus valores iniciales.", estilos))

    story.append(
        caja_aviso(
            "Confidencialidad de expedientes (LOPNNA Arts. 53, 54 y 65)",
            "Las fotografías, teléfonos y datos familiares de estudiantes y representantes son de uso estrictamente académico e institucional. Queda prohibida su reproducción o divulgación fuera del plantel.",
            estilos,
            tipo="atencion",
        )
    )

    # ── CAPÍTULO 7 ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(
        Paragraph(
            "Capítulo 7 — Control de Asistencia y Respaldo Anti-Apagones",
            estilos["TituloCapitulo"],
        )
    )
    story.append(Paragraph("7.1 Selección de Clase y Toma Diaria de Asistencia (P / A / J)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            'El módulo <b>Pasar Lista</b> (disponible para <b>ADMIN</b>, <b>ASISTENTE</b> y <b>DOCENTE</b>) se desarrolla en dos pantallas consecutivas:',
            estilos["Cuerpo"],
        )
    )
    story.append(paso(1, "<b>Selección de Clase:</b> En la ventana compacta <b>\"Seleccionar Clase — Pase de Lista\"</b>, elija la asignatura/sección en <b>Clase / Materia:</b>, seleccione la fecha en el calendario <b>Fecha de Asistencia:</b> (formato <font name='Courier'>yyyy-mm-dd</font>) y pulse <b>COMENZAR TOMA DE ASISTENCIA</b>.", estilos))
    story.append(
        paso(
            2,
            '<b>Planilla de Asistencia:</b> Se abre maximizada la ventana <b>"Planilla de Asistencia — Pase de Lista"</b> mostrando en la cabecera el nombre de la clase, la fecha, el conteo vivo (<i>Total | Presentes | Ausentes | Justificados</i>) y el indicador verde <b>Respaldo automático activo</b>. En la tabla (<i>Cédula</i>, <i>Estudiante</i>, <i>Estado</i>) todos los alumnos inician en <b>P</b> (Presente).',
            estilos,
        )
    )
    story.append(
        paso(
            3,
            "<b>Marcaje de Estados:</b> Seleccione uno o varios estudiantes de la tabla y pulse el botón correspondiente: <b>PRESENTE</b> (<b>P</b>), <b>AUSENTE</b> (<b>A</b>) o <b>JUSTIFICADA</b> (<b>J</b>). Al marcar <b>JUSTIFICADA</b>, el sistema abrirá un cuadro emergente preguntando <i>\"¿Por qué faltó &lt;Nombre&gt;?\"</i> para registrar obligatoriamente el motivo (si se cancela o queda vacío, el estado no cambia a <b>J</b>).",
            estilos,
        )
    )
    story.append(
        paso(
            4,
            "<b>Guardado Definitivo:</b> Al terminar, haga clic en <b>GUARDAR EN BASE DE DATOS</b>. El sistema ejecuta una transacción atómica que sustituye cualquier toma previa de esa misma clase y fecha (evitando registros duplicados), limpia el respaldo temporal de emergencia y muestra el mensaje de confirmación. Si desea salir descartando cambios, use <b>CERRAR SIN GUARDAR</b>.",
            estilos,
        )
    )

    story.append(
        caja_aviso(
            "Atajo rápido con doble clic",
            "Durante el pase de lista, al hacer <b>doble clic</b> sobre la fila de un estudiante en la tabla se alterna instantáneamente su estado entre <b>P</b> (Presente) y <b>A</b> (Ausente).",
            estilos,
            tipo="consejo",
        )
    )

    story.append(Paragraph("7.2 Protocolo ante Cortes Eléctricos (memoria_emergencia.json)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "Dado que pueden ocurrir interrupciones repentinas del servicio eléctrico antes de pulsar el botón de guardado definitivo, el sistema cuenta con un mecanismo automático anti-apagones:",
            estilos["Cuerpo"],
        )
    )
    story.append(bullet("<b>Guardado instantáneo en disco:</b> Cada vez que usted marca <b>P</b>, <b>A</b> o <b>J</b> en un estudiante (incluyendo el motivo de justificación), la planilla completa se escribe inmediatamente en el archivo local <b>memoria_emergencia.json</b>.", estilos))
    story.append(bullet("<b>Procedimiento al regresar la electricidad:</b>", estilos))
    story.append(paso(1, "Encienda nuevamente el equipo, abra el sistema e inicie sesión.", estilos))
    story.append(paso(2, "Entre en <b>Pasar Lista</b> y seleccione <b>exactamente la misma Clase y la misma Fecha</b> en que estaba trabajando cuando ocurrió el corte de luz.", estilos))
    story.append(paso(3, 'Al pulsar <b>COMENZAR TOMA DE ASISTENCIA</b>, el sistema detectará el archivo de respaldo concordante y mostrará la alerta: <i>"¡ATENCIÓN! Se encontró una lista sin guardar del apagón. ¿Deseas recuperar lo que llevabas?"</i>.', estilos))
    story.append(paso(4, "Responda <b>Sí</b> para recuperar todos sus marcajes intactos, complete los alumnos restantes si faltaba alguno y pulse finalmente <b>GUARDAR EN BASE DE DATOS</b>.", estilos))

    # ── CAPÍTULO 8 ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(
        Paragraph(
            "Capítulo 8 — Listados, Reportes (Art. 109 RGLOE) y Estadísticas",
            estilos["TituloCapitulo"],
        )
    )

    story.append(Paragraph("8.1 Listados Consolidados (Listados)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            'Accesible para <b>ADMIN</b>, <b>ASISTENTE</b> y <b>DOCENTE</b>. La ventana <b>"Listados Institucionales del Liceo"</b> centraliza la consulta de nóminas activas en tres pestañas:',
            estilos["Cuerpo"],
        )
    )
    story.append(bullet("<b>Alumnos Activos:</b> Columnas <i>Cédula, Estudiante, F. Nac, Representante, Teléfono, Gen, Año, Sec, Condición, Turno</i>. Filtra por cédula, nombre, representante o grado.", estilos))
    story.append(bullet("<b>Materias y Clases:</b> Columnas <i>ID, Materia, Profesor Encargado, Año, Sección</i>. Filtra por materia, profesor o grado.", estilos))
    story.append(bullet("<b>Nómina de Profesores:</b> Columnas <i>ID, Cédula, Nombre Completo, Teléfono</i>. Filtra por cédula, nombre o teléfono.", estilos))
    story.append(
        Paragraph(
            "En cualquiera de las tres pestañas puede escribir en la caja <b>Filtrar:</b> para buscar en tiempo real mientras teclea, pulsar <b>Refrescar</b> para recargar desde la base de datos o exportar la vista actual con el botón rojo <b>PDF</b>.",
            estilos["Cuerpo"],
        )
    )

    story.append(Paragraph("8.2 Reportes de Asistencia y Cálculo Legal Art. 109 RGLOE (Reportes)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            'Accesible para <b>ADMIN</b> y <b>ASISTENTE</b>. La ventana <b>"Reportes y Estadísticas — Art. 109 RGLOE"</b> ofrece tres modos de búsqueda por pestañas:',
            estilos["Cuerpo"],
        )
    )
    story.append(bullet("<b>Reporte Diario:</b> Seleccione una <b>Fecha:</b> y presione <b>Buscar por Día</b>.", estilos))
    story.append(bullet("<b>Reporte Mensual:</b> Elija el <b>Mes:</b> y el <b>Año:</b> y presione <b>Buscar por Mes</b>.", estilos))
    story.append(bullet("<b>Historial Estudiante:</b> Escriba la <b>Cédula:</b> y pulse <b>Buscar Historial</b> (o presione <b>Enter</b>).", estilos))
    story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            "Los resultados muestran <i>Fecha, Cédula, Estudiante, Gen, Materia, ST, Justificación, % Asist.</i> y actualizan la barra inferior con el total de registros, asistencias efectivas (P+J), faltas (A) y cantidad de alumnos en riesgo. El porcentaje legal se calcula estrictamente según el <b>Artículo 109 del RGLOE</b>:",
            estilos["Cuerpo"],
        )
    )
    story.append(
        Table(
            [
                [
                    Paragraph(
                        "Asistencia Efectiva (%) = ((Presentes [P] + Justificadas [J]) &divide; Total de Clases) &times; 100",
                        estilos["Formula"],
                    )
                ]
            ],
            colWidths=[ancho_util],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_FONDO_NEUTRO),
                    ("BOX", (0, 0), (-1, -1), 0.7, COLOR_SECUNDARIO),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        )
    )
    story.append(Spacer(1, 5))
    story.append(
        Paragraph(
            "Las faltas justificadas (<b>J</b>) suman como asistencia efectiva junto a los presentes (<b>P</b>). Si un estudiante tiene al menos una clase registrada y su porcentaje resulta estrictamente menor al <b>75.0%</b>, sus filas se resaltan en rojo suave y puede inspeccionarse en detalle con el botón <b>VER ALERTAS DE RIESGO (&lt; 75%)</b>, que abre un listado ordenado de mayor a menor criticidad. El botón <b>EXPORTAR A PDF</b> guarda la consulta actual en PDF oficial.",
            estilos["Cuerpo"],
        )
    )

    story.append(Paragraph("8.3 Tablero de Estadísticas Institucionales (Estadísticas)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            'Accesible para <b>ADMIN</b> y <b>ASISTENTE</b>. La ventana <b>"Estadísticas Institucionales — Colinas del Llano"</b> consolida indicadores gráficos en tiempo real sin librerías pesadas externas:',
            estilos["Cuerpo"],
        )
    )
    story.append(bullet("<b>4 Tarjetas KPI Superiores:</b> <i>Estudiantes Activos</i>, <i>Docentes Activos</i>, <i>% Asistencia Global</i> (con semáforo: verde desde 75%, ámbar 65% a 74.99%, rojo menor a 65%) y <i>Alumnos en Riesgo (&lt; 75%)</i>.", estilos))
    story.append(bullet("<b>Gráfico Izquierdo:</b> <i>% Asistencia Efectiva por Sección (Meta Legal 75%)</i> con barras horizontales por año/sección y una línea vertical punteada marcando el umbral obligatorio del 75%.", estilos))
    story.append(bullet("<b>Gráfico Derecho:</b> <i>Asistencia (P / A / J) y Matrícula por Género</i> (barra segmentada con leyenda de Presentes, Justificadas, Ausentes y desglose Masculino/Femenino).", estilos))
    story.append(bullet("<b>Tabla Inferior:</b> <i>Estudiantes en Alerta Crítica (&lt; 75.0% Art. 109 RGLOE)</i> con cédula, estudiante, grado/sección, asistencias efectivas, clases y porcentaje.", estilos))
    story.append(bullet("<b>Botones Superiores:</b> <b>Exportar PDF</b> (genera el reporte estadístico institucional completo y pregunta si desea abrirlo) y <b>Actualizar Métricas</b>.", estilos))

    # ── CAPÍTULO 9 ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(
        Paragraph(
            "Capítulo 9 — Administración Avanzada (Usuarios y Promoción Anual)",
            estilos["TituloCapitulo"],
        )
    )

    story.append(Paragraph("9.1 Gestión de Usuarios y Buenas Prácticas de Seguridad (Seguridad)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            'El módulo <b>Seguridad</b> (solo <b>ADMIN</b>) solicita primero la <b>Clave Maestra Institucional (resguardada exclusivamente por la Dirección/Coordinación)</b> antes de abrir el <b>"Panel de Seguridad y Usuarios"</b>.',
            estilos["Cuerpo"],
        )
    )
    story.append(bullet("<b>Alta y Edición:</b> Complete <i>Nombre Completo:</i>, <i>Username (Login):</i> (mínimo 4 caracteres), <i>Contraseña:</i> (mínimo 4 caracteres; se recomiendan 8 o más combinando letras y números) y <i>Rol en el sistema:</i> (<b>ADMIN</b>, <b>ASISTENTE</b> o <b>DOCENTE</b>). Use <b>Guardar Nuevo</b> para crear, o haga <b>doble clic</b> sobre un usuario en la tabla inferior para cargarlo (la casilla de clave mostrará <font name='Courier'>********</font>, por lo que debe escribir una nueva contraseña antes de pulsar <b>Actualizar</b>).", estilos))
    story.append(bullet("<b>Revocación Segura:</b> El botón <b>Desactivar</b> aplica borrado lógico para retirar el acceso a personal que ya no labora en el plantel sin perder la trazabilidad histórica de sus registros.", estilos))
    story.append(bullet("<b>Principio de Mínimo Privilegio:</b> Asigne el rol <b>DOCENTE</b> a profesores de aula, <b>ASISTENTE</b> al personal de secretaría o apoyo en coordinación y reserve <b>ADMIN</b> únicamente para Dirección y Coordinación General.", estilos))

    story.append(Paragraph("9.2 Cierre de Año Escolar y Promoción Anual en Cascada (Promoción Anual)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            'Al concluir el año escolar, el módulo <b>Promoción Anual</b> (exclusivo para <b>ADMIN</b>) abre la ventana <b>"Cierre y Promoción de Año Escolar"</b> para avanzar masivamente a todos los estudiantes activos al grado superior:',
            estilos["Cuerpo"],
        )
    )
    story.append(paso(1, "<b>Revisar el Censo Previo:</b> Verifique en la tabla <i>Vista Previa de Alumnos Activos por Grado</i> (columnas: <i>ID</i>, <i>Grado / Año Actual</i>, <i>Alumnos Activos</i>, <i>Destino tras Promoción</i>) cuántos estudiantes serán promovidos en cada año. Si realizó cambios recientes en inscripciones, pulse <b>Refrescar Censo</b>.", estilos))
    story.append(paso(2, "<b>Secuencia en Cascada Inversa:</b> El sistema promueve atómicamente en orden descendente para evitar colisiones: <b>5to AÑO a GRADUADO / EGRESADO</b>, <b>4to AÑO a 5to AÑO</b>, <b>3er AÑO a 4to AÑO</b>, <b>2do AÑO a 3er AÑO</b> y <b>1er AÑO a 2do AÑO</b>. Los estudiantes inactivos o ya graduados no sufren cambios.", estilos))
    story.append(paso(3, "<b>Ejecución con Doble Autorización:</b> Pulse <b>EJECUTAR PROMOCIÓN EN CASCADA</b>, confirme la advertencia crítica (<b>Sí</b>) y escriba la <b>Clave Maestra Institucional (resguardada exclusivamente por la Dirección/Coordinación)</b>.", estilos))
    story.append(
        caja_aviso(
            "Operación masiva irreversible de fin de año",
            "La Promoción Anual <b>NO se puede deshacer</b> automáticamente. Ejecútela únicamente al cerrar el año escolar y solo <b>después</b> de haber emitido los reportes PDF finales y realizado una copia de respaldo completa de <b>sistema_escolar.db</b>.",
            estilos,
            tipo="advertencia",
        )
    )

    # ── CAPÍTULO 10 ───────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(
        Paragraph(
            "Capítulo 10 — Respaldo Semanal, Solución de Problemas y Marco Legal",
            estilos["TituloCapitulo"],
        )
    )

    story.append(Paragraph("10.1 Procedimiento de Respaldo Semanal (Backup)", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "Debido a que el sistema funciona de manera local sin servidores en la nube, la Coordinación debe realizar un respaldo semanal (por ejemplo, todos los viernes al finalizar la jornada) hacia un pendrive institucional o disco externo dedicado:",
            estilos["Cuerpo"],
        )
    )
    story.append(paso(1, "<b>Cierre completamente el sistema</b> antes de copiar archivos (esto garantiza que la base de datos SQLite en modo WAL consolide todas las escrituras pendientes dentro del archivo principal).", estilos))
    story.append(paso(2, "Abra la carpeta donde está instalado el sistema: <b>Documentos\\Sistema_Asistencia_Colinas</b> (en Windows) o <b>~/Documentos/Sistema_Asistencia_Colinas</b> (en Linux Mint).", estilos))
    story.append(paso(3, "Copie hacia su pendrive o carpeta de respaldo semanal (ej. nombrada <font name='Courier'>Respaldo_Colinas_AAAA-MM-DD</font>) estos dos elementos indispensables:<br/>&nbsp;&nbsp;&bull;&nbsp; El archivo <b>sistema_escolar.db</b> (base de datos completa de usuarios, docentes, estudiantes, materias, asistencia y auditoría).<br/>&nbsp;&nbsp;&bull;&nbsp; La carpeta completa <b>fotos/</b> (contiene las fotografías optimizadas de estudiantes y profesores).", estilos))
    story.append(
        Paragraph(
            "Para restaurar en caso de daño del computador, instale nuevamente el programa en el equipo nuevo, asegúrese de que esté cerrado y pegue su archivo <b>sistema_escolar.db</b> y la carpeta <b>fotos/</b> dentro de <b>Sistema_Asistencia_Colinas</b> reemplazando los vacíos.",
            estilos["Cuerpo"],
        )
    )

    story.append(Paragraph("10.2 Solución de Problemas Frecuentes (FAQ)", estilos["TituloSeccion"]))
    story.append(
        tabla_estilizada(
            ["Situación / Problema", "Causa Probable y Solución Paso a Paso"],
            [
                [
                    "<b>Windows Defender SmartScreen bloquea el instalador o el programa</b>",
                    "Windows muestra una alerta preventiva porque el software institucional no posee certificado comercial de pago. Haga clic en <b>Más información</b> y luego en <b>Ejecutar de todas formas</b>.",
                ],
                [
                    "<b>Olvidé mi usuario o contraseña</b>",
                    "En la pantalla de Login haga clic en <b>¿Olvidó su usuario o contraseña?</b>. Con la <b>Clave Maestra Institucional</b> (resguardada por Dirección/Coordinación) podrá consultar los usuarios activos y asignar una nueva contraseña.",
                ],
                [
                    "<b>Hubo un apagón mientras pasaba lista</b>",
                    "Sus marcajes se guardaron automáticamente en <b>memoria_emergencia.json</b>. Al volver la luz, abra <b>Pasar Lista</b>, seleccione <b>la misma clase y fecha</b>, y acepte el mensaje de recuperación.",
                ],
                [
                    "<b>No me permite cargar la fotografía de un alumno o profesor</b>",
                    "Debe escribir primero la <b>Cédula</b> en el formulario antes de pulsar <b>Cargar</b>, y seleccionar un formato válido (<font name='Courier'>.jpg, .jpeg, .png, .webp, .bmp</font>).",
                ],
                [
                    "<b>No aparecen materias en Pasar Lista</b>",
                    "Aún no se han asignado materias. Un usuario <b>ADMIN</b> debe entrar en <b>Gestión Académica</b>, registrar al docente y luego vincular la materia y secciones en la pestaña <b>ASIGNAR MATERIAS</b>.",
                ],
                [
                    "<b>Un alumno aparece en alerta roja (&lt; 75%)</b>",
                    "Su asistencia efectiva (<b>P + J</b>) está por debajo del 75.0% exigido por el Art. 109 RGLOE. Verifique en <b>Reportes &gt; Historial Estudiante</b> si posee inasistencias justificables o notifique al representante.",
                ],
            ],
            [ancho_util * 0.34, ancho_util * 0.66],
            estilos,
        )
    )
    story.append(Spacer(1, 8))

    story.append(CondPageBreak(150))
    story.append(Paragraph("10.3 Marco Legal, Licenciamiento y Soporte Técnico", estilos["TituloSeccion"]))
    story.append(
        Paragraph(
            "El sistema y su documentación se rigen por la normativa venezolana vigente y el licenciamiento de Software Libre:",
            estilos["Cuerpo"],
        )
    )
    story.append(bullet("<b>Licencia Principal:</b> <b>GNU General Public License v3.0 (GPLv3)</b>, en concordancia con la <b>Ley de Infogobierno</b> que promueve el uso de Software Libre en la gestión pública educativa venezolana. Este programa se distribuye sin garantía alguna (conforme a la exención estándar de la licencia GPLv3).", estilos))
    story.append(bullet("<b>Art. 109 del Reglamento General de la Ley Orgánica de Educación (RGLOE):</b> Establece el mínimo legal del <b>75% de asistencia efectiva</b> para la aprobación del año escolar.", estilos))
    story.append(bullet("<b>LOPNNA (Arts. 53, 54 y 65):</b> Resguarda el derecho a la educación y exige confidencialidad estricta sobre los datos personales, familiares y fotografías de estudiantes y representantes.", estilos))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph("<b>Componentes de Terceros Empaquetados (compatibles con GNU GPLv3):</b>", estilos["Cuerpo"])
    )
    story.append(
        tabla_estilizada(
            ["Componente", "Versión", "Licencia", "Función en el Sistema"],
            [
                ["Python", "3.12", "PSF License v2", "Intérprete y biblioteca estándar"],
                ["Tcl/Tk (Tkinter / Ttk)", "8.6", "Tcl/Tk License (BSD-style)", "Interfaz gráfica y gráficos en Canvas"],
                ["SQLite", "3.x", "Dominio Público", "Base de datos relacional local offline-first"],
                ["tkcalendar", "1.6.1", "GNU GPLv3", "Selectores de fecha en formularios y reportes"],
                ["ReportLab", "4.4.10", "BSD-3-Clause", "Generación de fichas y reportes oficiales PDF"],
                ["Pillow", "12.1.1", "MIT-CMU", "Optimización y vistas previas de fotografías"],
                ["Babel", "2.18.0", "BSD-3-Clause / Unicode v3", "Localización de calendarios en español"],
                ["charset-normalizer", "3.4.6", "MIT", "Normalización de codificación de texto"],
            ],
            [ancho_util * 0.24, ancho_util * 0.12, ancho_util * 0.28, ancho_util * 0.36],
            estilos,
            centrar_cols={1},
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        caja_aviso(
            "Equipo Desarrollador y Canal Oficial de Soporte Técnico",
            f"<b>Equipo Desarrollador:</b> {', '.join(escape(a) for a in AUTORES_COMPLETOS)}.<br/>"
            f"<b>Contacto de Soporte Técnico:</b> {escape(CONTACTO_SOPORTE_NOMBRE)}<br/>"
            f"<b>Correo Electrónico:</b> {escape(CONTACTO_SOPORTE_EMAIL)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Teléfono:</b> {escape(CONTACTO_SOPORTE_TEL)}",
            estilos,
            tipo="nota",
        )
    )


# ═══════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════
def generar_manual_pdf(ruta_salida: str = RUTA_SALIDA_DEFAULT) -> str:
    """Construye el Manual de Usuario institucional en PDF usando multiBuild para TOC exacto."""
    dir_destino = os.path.dirname(os.path.abspath(ruta_salida))
    if dir_destino:
        os.makedirs(dir_destino, exist_ok=True)

    estilos = crear_estilos()
    story: list = []

    agregar_portada(story, estilos)
    agregar_tabla_contenidos(story, estilos)
    agregar_capitulos(story, estilos)

    doc = ManualDocTemplate(
        ruta_salida,
        pagesize=letter,
        title="Manual de Usuario — Sistema de Gestión de Asistencia Estudiantil",
        author="César Manuel Meléndez Berríos, Michelle Josefina Díaz Bastidas, Renzo Gabriel Meléndez Berríos, César Miguel González Terán",
        subject='Complejo Educativo "Colinas del Llano" — Barinas, Venezuela',
    )
    doc.multiBuild(story)
    return ruta_salida


if __name__ == "__main__":
    destino = sys.argv[1] if len(sys.argv) > 1 else RUTA_SALIDA_DEFAULT
    ruta_generada = generar_manual_pdf(destino)
    print(f"Manual generado exitosamente en: {ruta_generada}")
