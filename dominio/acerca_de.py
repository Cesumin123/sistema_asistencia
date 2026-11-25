# dominio/acerca_de.py
"""
Metadatos oficiales, créditos de autoría y avisos legales del sistema.

Módulo de dominio puro (sin dependencias de UI, Pillow, ReportLab ni SQLite)
que centraliza la información institucional, equipo desarrollador, marco
normativo venezolano y resumen de licencias de terceros.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ComponenteTercero:
    """Describe una dependencia o componente de terceros empaquetado."""

    nombre: str
    version: str
    licencia: str
    proposito: str


NOMBRE_SISTEMA = "Sistema de Información para la Gestión de Asistencia Estudiantil"
NOMBRE_CORTO = "Sistema de Asistencia Estudiantil"
VERSION_SISTEMA = "1.0.0"
ANIO_PUBLICACION = "2026"
INSTITUCION_BENEFICIARIA = (
    'Complejo Educativo "Colinas del Llano" — Coordinación de 4to Año, Barinas, Venezuela'
)

EQUIPO_DESARROLLADOR: tuple[str, ...] = (
    "César Meléndez",
    "Michelle Diaz",
    "Renzo Melendez",
    "Cesar Gonzalez",
)

CONTACTO_TECNICO = "César Meléndez — melendezcesar122@gmail.com"
EMAIL_CONTACTO = "melendezcesar122@gmail.com"
TELEFONO_SOPORTE = "+58 414-5446824"
LICENCIA_NOMBRE = "GNU General Public License v3.0 (GPLv3)"

MARCO_NORMATIVO: tuple[str, ...] = (
    "Art. 109 del RGLOE: Mínimo del 75% de asistencia efectiva para aprobación escolar.",
    "LOPNNA (Arts. 53, 54 y 65): Derecho a la educación y resguardo de datos personales.",
    "Ley de Infogobierno: Promoción del Software Libre en la gestión pública educativa.",
)

AVISO_CONFIDENCIALIDAD_LOPNNA = (
    "Confidencialidad (LOPNNA Arts. 53, 54 y 65): Los datos personales, fotografías "
    "y registros académicos de estudiantes y representantes son de uso estrictamente "
    "institucional y académico, quedando prohibida su divulgación no autorizada."
)

EXENCION_RESPONSABILIDAD = (
    "Este programa es software libre bajo GNU GPLv3 y se distribuye SIN GARANTÍA "
    "ALGUNA, sin siquiera la garantía implícita de COMERCIALIZACIÓN o IDONEIDAD "
    "PARA UN PROPÓSITO PARTICULAR."
)

COMPONENTES_TERCEROS: tuple[ComponenteTercero, ...] = (
    ComponenteTercero("Python", "3.12", "PSF License v2", "Intérprete y biblioteca estándar"),
    ComponenteTercero("Tcl/Tk", "8.6", "Tcl/Tk License (BSD-style)", "Interfaz gráfica Tkinter/Ttk"),
    ComponenteTercero("SQLite", "3.x", "Dominio Público", "Base de datos embebida offline-first"),
    ComponenteTercero("tkcalendar", "1.6.1", "GNU GPLv3", "Selector de fechas calendario"),
    ComponenteTercero("ReportLab", "4.4.10", "BSD-3-Clause", "Generación de reportes PDF"),
    ComponenteTercero("Pillow", "12.1.1", "MIT-CMU", "Procesamiento de imágenes y fotos"),
    ComponenteTercero("Babel", "2.18.0", "BSD-3-Clause / Unicode v3", "Localización de fechas"),
    ComponenteTercero("charset-normalizer", "3.4.6", "MIT", "Normalización de codificación"),
)


def obtener_resumen_legal_y_terceros() -> str:
    """Retorna el texto formateado con marco normativo, terceros y exención legal."""
    lineas = [
        f"Licencia Principal: {LICENCIA_NOMBRE}",
        f"Soporte Técnico: {EMAIL_CONTACTO}  |  Tel: {TELEFONO_SOPORTE}",
        "",
        "MARCO NORMATIVO APLICABLE:",
    ]
    for norma in MARCO_NORMATIVO:
        lineas.append(f"  • {norma}")

    lineas.extend(["", "COMPONENTES DE TERCEROS EMPAQUETADOS:"])
    for comp in COMPONENTES_TERCEROS:
        lineas.append(
            f"  • {comp.nombre} ({comp.version}) — {comp.licencia}: {comp.proposito}"
        )

    lineas.extend([
        "",
        "EXENCIÓN DE RESPONSABILIDAD (GNU GPLv3):",
        EXENCION_RESPONSABILIDAD,
    ])
    return "\n".join(lineas)
