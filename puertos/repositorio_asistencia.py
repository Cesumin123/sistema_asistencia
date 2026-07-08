from abc import ABC, abstractmethod
from typing import Optional
from dominio.asistencia import PlanillaAsistencia

class PuertoRepositorioAsistencia(ABC):
    """Contrato para la persistencia definitiva de la asistencia."""
    
    @abstractmethod
    def guardar_planilla(self, planilla: PlanillaAsistencia) -> None:
        """Guarda la planilla final en la base de datos."""
        pass
        
    @abstractmethod
    def obtener_planilla(self, id_clase: int, fecha: date) -> Optional[PlanillaAsistencia]:
        """Recupera una asistencia previamente guardada."""
        pass

class PuertoRespaldoEmergencia(ABC):
    """Contrato para el sistema anti-apagones."""
    
    @abstractmethod
    def guardar_respaldo(self, planilla: PlanillaAsistencia) -> None:
        """Guarda el estado actual de la planilla de forma temporal."""
        pass
        
    @abstractmethod
    def recuperar_respaldo(self, id_clase: int, fecha: date) -> Optional[PlanillaAsistencia]:
        """Verifica si existe un borrador sin guardar para esa clase y fecha."""
        pass
        
    @abstractmethod
    def limpiar_respaldo(self) -> None:
        """Elimina el archivo de respaldo una vez guardado en la base de datos principal."""
        pass