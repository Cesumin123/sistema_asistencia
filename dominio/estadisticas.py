# dominio/estadisticas.py
"""
Núcleo de Dominio: Módulo de Estadísticas Institucionales.
Entidades puras y cálculos agregados según el Art. 109 RGLOE (mínimo 75% de asistencia efectiva).
Python puro sin dependencias de SQLite, Tkinter ni librerías externas.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class DistribucionEstados:
    """Distribución global de marcajes de asistencia (P, A, J)."""
    presentes: int = 0
    ausentes: int = 0
    justificadas: int = 0

    @property
    def total(self) -> int:
        return self.presentes + self.ausentes + self.justificadas

    @property
    def efectivas(self) -> int:
        return self.presentes + self.justificadas

    @property
    def porcentaje_presentes(self) -> float:
        return CalculadoraEstadisticas.calcular_proporcion(self.presentes, self.total)

    @property
    def porcentaje_ausentes(self) -> float:
        return CalculadoraEstadisticas.calcular_proporcion(self.ausentes, self.total)

    @property
    def porcentaje_justificadas(self) -> float:
        return CalculadoraEstadisticas.calcular_proporcion(self.justificadas, self.total)

    @property
    def porcentaje_efectivo(self) -> float:
        return CalculadoraEstadisticas.calcular_tasa_efectiva(
            self.presentes, self.justificadas, self.total
        )


@dataclass
class DistribucionGenero:
    """Distribución demográfica de matrícula estudiantil activa por género."""
    masculino: int = 0
    femenino: int = 0

    @property
    def total(self) -> int:
        return self.masculino + self.femenino

    @property
    def porcentaje_masculino(self) -> float:
        return CalculadoraEstadisticas.calcular_proporcion(self.masculino, self.total)

    @property
    def porcentaje_femenino(self) -> float:
        return CalculadoraEstadisticas.calcular_proporcion(self.femenino, self.total)


@dataclass
class MetricaSeccion:
    """Métrica agregada de asistencia efectiva para una combinación Grado + Sección."""
    grado: str
    seccion: str
    etiqueta: str
    presentes: int = 0
    ausentes: int = 0
    justificadas: int = 0
    total_registros: int = 0
    tasa_efectiva: float = 100.0


@dataclass
class EstudianteEnRiesgo:
    """Estudiante activo por debajo del mínimo legal del 75.0% (Art. 109 RGLOE)."""
    id_estudiante: str
    nombre: str
    grado: str
    seccion: str
    total_clases: int
    asistencias_efectivas: int
    faltas_injustificadas: int
    porcentaje_asistencia: float


@dataclass
class ResumenEstadisticoGeneral:
    """Resumen institucional consolidado para el tablero de estadísticas."""
    total_estudiantes_activos: int = 0
    total_docentes_activos: int = 0
    total_clases_activas: int = 0
    total_registros_asistencia: int = 0
    tasa_asistencia_global: float = 100.0
    total_en_riesgo: int = 0
    distribucion_estados: DistribucionEstados = field(default_factory=DistribucionEstados)
    distribucion_genero: DistribucionGenero = field(default_factory=DistribucionGenero)
    metricas_por_seccion: List[MetricaSeccion] = field(default_factory=list)
    estudiantes_en_riesgo: List[EstudianteEnRiesgo] = field(default_factory=list)


class CalculadoraEstadisticas:
    """Reglas puras de cálculo estadístico y evaluación legal (Art. 109 RGLOE)."""

    UMBRAL_APROBACION_RGLOE = 75.0
    UMBRAL_ADVERTENCIA = 65.0

    @staticmethod
    def calcular_tasa_efectiva(presentes: int, justificadas: int, total: int) -> float:
        """
        Calcula ((presentes + justificadas) / total) * 100 redondeado a 2 decimales.
        Si total <= 0, retorna 100.0 sin lanzar ZeroDivisionError.
        """
        if total <= 0:
            return 100.0
        efectivas = max(0, int(presentes)) + max(0, int(justificadas))
        return round((efectivas / total) * 100.0, 2)

    @staticmethod
    def calcular_proporcion(parte: int, total: int) -> float:
        """Calcula porcentaje de una parte sobre el total, protegiendo división entre cero."""
        if total <= 0:
            return 0.0
        return round((max(0, int(parte)) / total) * 100.0, 2)

    @classmethod
    def es_en_riesgo(cls, porcentaje_asistencia: float, total_clases: int) -> bool:
        """
        Criterio legal Art. 109 RGLOE coherente con dominio/reportes.py:
        requiere al menos 1 clase registrada y asistencia efectiva < 75.0%.
        """
        return total_clases > 0 and porcentaje_asistencia < cls.UMBRAL_APROBACION_RGLOE

    @classmethod
    def clasificar_semaforo(cls, tasa_efectiva: float) -> str:
        """Clasifica la tasa en 'verde' (>= 75%), 'ambar' (65%-74.99%) o 'rojo' (< 65%)."""
        if tasa_efectiva >= cls.UMBRAL_APROBACION_RGLOE:
            return "verde"
        if tasa_efectiva >= cls.UMBRAL_ADVERTENCIA:
            return "ambar"
        return "rojo"
