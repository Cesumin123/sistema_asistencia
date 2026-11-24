# puertos/repositorio_reportes.py

from abc import ABC, abstractmethod
from typing import List, Optional, Any
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
    Contrato para generar documentos y reportes oficiales en PDF.
    Desacoplado de bases de datos y de la interfaz gráfica.
    """
    
    @abstractmethod
    def exportar_tabla(self, titulo: str, encabezados: List[str], datos: List[List[str]], ruta_salida: str) -> bool:
        """Debe retornar True si se generó con éxito, False si hubo error."""
        pass

    @abstractmethod
    def generar_ficha_docente(self, profesor: Any, materias_asignadas: Optional[List[Any]] = None, ruta_salida: Optional[str] = None) -> str:
        """Construye la ficha oficial imprimible del profesor y retorna la ruta del PDF generado."""
        pass

    @abstractmethod
    def generar_ficha_estudiante(self, estudiante: Any, resumen_asistencia: Optional[dict] = None, ruta_salida: Optional[str] = None) -> str:
        """Construye la ficha oficial de inscripción/expediente del estudiante y retorna la ruta del PDF."""
        pass

    @abstractmethod
    def generar_reporte_estadisticas(self, resumen: Any, ruta_salida: str) -> bool:
        """Genera el reporte PDF consolidado de estadísticas institucionales."""
        pass