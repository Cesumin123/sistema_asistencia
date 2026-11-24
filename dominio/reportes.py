# dominio/reportes.py
"""
Núcleo de Dominio: Módulo de Reportes y Análisis de Asistencia Escolar.
Regulado por el Artículo 109 del Reglamento General de la Ley Orgánica de Educación (RGLOE).
Contiene entidades puras y reglas de negocio sin acoplamiento a bases de datos ni UI.
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class AsistenciaEnriquecida:
    """Data Transfer Object que combina la asistencia con datos del estudiante y materia."""
    id_estudiante: str
    nombre: str
    genero: str
    fecha: str
    estado: str  # 'P', 'A', 'J'
    materia: str = ""
    observacion: str = ""


@dataclass
class AlertaRiesgo:
    """
    Entidad que representa la evaluación de riesgo de reprobación por inasistencia (Art. 109 RGLOE).
    Exige un mínimo del 75% de asistencia efectiva ('P' + 'J') para la aprobación del año escolar.
    """
    id_estudiante: str
    nombre: str
    faltas_injustificadas: int = 0
    total_clases: int = 0
    presentes: int = 0
    justificadas: int = 0
    porcentaje_asistencia: float = 100.0

    @property
    def asistencias_efectivas(self) -> int:
        """Asistencias efectivas según Art. 109 RGLOE: 'P' y 'J'."""
        return self.presentes + self.justificadas

    @property
    def es_critico(self) -> bool:
        """
        Regla de negocio estricta (Art. 109 RGLOE - CP-04):
        Si el porcentaje de asistencia efectiva es estrictamente menor al 75.0%,
        el estudiante se encuentra en ALERTA DE RIESGO DE REPROBACIÓN.
        Un porcentaje >= 75.0% cumple el mínimo legal (NO riesgo).
        """
        return self.porcentaje_asistencia < 75.0


class AnalizadorEstadistico:
    """
    Servicio de Dominio para el análisis estadístico y cálculo de alertas de inasistencia.
    Python puro, desacoplado de SQLite y Tkinter.
    """

    @staticmethod
    def calcular_porcentaje(asistencias_efectivas: int, total_clases: int) -> float:
        """
        Fórmula oficial según Art. 109 RGLOE:
        porcentaje = (asistencias_efectivas / total_clases_dictadas) * 100

        Prevención de división entre cero:
        Si total_clases == 0, retorna 100.0% (sin alerta).
        """
        if total_clases <= 0:
            return 100.0
        return round((asistencias_efectivas / total_clases) * 100.0, 2)

    @staticmethod
    def es_alerta_riesgo(porcentaje: float) -> bool:
        """Evalúa si un porcentaje de asistencia efectiva incumple el mínimo legal del 75.0%."""
        return porcentaje < 75.0

    @staticmethod
    def generar_resumen_estudiantes(registros: List[AsistenciaEnriquecida]) -> List[AlertaRiesgo]:
        """
        Agrupa los registros por estudiante, desglosando 'P', 'J' y 'A',
        y calcula el porcentaje oficial de asistencia efectiva según Art. 109 RGLOE.
        """
        conteo_p: Dict[str, int] = {}
        conteo_j: Dict[str, int] = {}
        conteo_a: Dict[str, int] = {}
        nombres: Dict[str, str] = {}

        for reg in registros:
            id_est = reg.id_estudiante
            nombres[id_est] = reg.nombre
            estado = reg.estado.upper()
            if estado == 'P':
                conteo_p[id_est] = conteo_p.get(id_est, 0) + 1
            elif estado == 'J':
                conteo_j[id_est] = conteo_j.get(id_est, 0) + 1
            elif estado == 'A':
                conteo_a[id_est] = conteo_a.get(id_est, 0) + 1

        todos_los_ids = set(nombres.keys())
        resumenes: List[AlertaRiesgo] = []
        for id_est in todos_los_ids:
            p = conteo_p.get(id_est, 0)
            j = conteo_j.get(id_est, 0)
            a = conteo_a.get(id_est, 0)
            total = p + j + a
            efectivas = p + j
            pct = AnalizadorEstadistico.calcular_porcentaje(efectivas, total)

            resumenes.append(AlertaRiesgo(
                id_estudiante=id_est,
                nombre=nombres[id_est],
                faltas_injustificadas=a,
                total_clases=total,
                presentes=p,
                justificadas=j,
                porcentaje_asistencia=pct
            ))

        return resumenes

    @staticmethod
    def detectar_riesgo(registros: List[AsistenciaEnriquecida]) -> List[AlertaRiesgo]:
        """
        Identifica y filtra únicamente a los estudiantes en riesgo legal (< 75.0% de asistencia efectiva).
        Ordenados de menor porcentaje a mayor (más críticos primero).
        """
        resumenes = AnalizadorEstadistico.generar_resumen_estudiantes(registros)
        alertas = [r for r in resumenes if r.es_critico]
        return sorted(alertas, key=lambda x: (x.porcentaje_asistencia, -x.faltas_injustificadas))

    @staticmethod
    def calcular_demografia(registros: List[AsistenciaEnriquecida]) -> Dict[str, int]:
        """
        Calcula estadísticas descriptivas demográficas (Varones vs Hembras presentes/ausentes/justificados).
        Mantiene el desglose individual de P, A y J.
        """
        stats = {
            "masculino_presente": 0,
            "masculino_ausente": 0,
            "masculino_justificado": 0,
            "femenino_presente": 0,
            "femenino_ausente": 0,
            "femenino_justificado": 0,
            "total_masculino": 0,
            "total_femenino": 0,
            "total_general": 0
        }

        for reg in registros:
            genero = "masculino" if reg.genero.upper() == "M" else "femenino"
            stats["total_general"] += 1
            stats[f"total_{genero}"] += 1

            estado = reg.estado.upper()
            if estado == 'P':
                stats[f"{genero}_presente"] += 1
            elif estado == 'J':
                stats[f"{genero}_justificado"] += 1
            elif estado == 'A':
                stats[f"{genero}_ausente"] += 1

        return stats
