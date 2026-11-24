# puertos/repositorio_estadisticas.py
"""
Puerto / Contrato abstracto para el Módulo de Estadísticas Institucionales.
"""

from abc import ABC, abstractmethod
from dominio.estadisticas import ResumenEstadisticoGeneral


class PuertoRepositorioEstadisticas(ABC):
    """Contrato de solo lectura para obtener indicadores institucionales agregados."""

    @abstractmethod
    def obtener_resumen_institucional(self) -> ResumenEstadisticoGeneral:
        """Calcula y retorna el resumen estadístico institucional consolidado."""
        pass
