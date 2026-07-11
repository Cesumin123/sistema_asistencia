# puertos/repositorio_reportes.py

from abc import ABC, abstractmethod
from typing import List
from dominio.reportes import AsistenciaEnriquecida

class PuertoRepositorioReportes(ABC):
    """Contrato que el Adaptador SQLite deberá cumplir."""
    
    @abstractmethod
    def obtener_asistencia_por_fecha(self, fecha: str) -> List[AsistenciaEnriquecida]:
        pass

    @abstractmethod
    def obtener_asistencia_por_mes(self, mes: str, anio: str) -> List[AsistenciaEnriquecida]:
        pass

    @abstractmethod
    def obtener_historial_estudiante(self, id_estudiante: str) -> List[AsistenciaEnriquecida]:
        pass


class PuertoExportadorPDF(ABC):
    """
    Contrato para generar documentos.
    El Adaptador que implemente esto será el que importe ReportLab y use tu 'ImprentaPDF'.
    """
    
    @abstractmethod
    def exportar_tabla(self, titulo: str, encabezados: List[str], datos: List[List[str]], ruta_salida: str) -> bool:
        """Debe retornar True si se generó con éxito, False si hubo error."""
        pass