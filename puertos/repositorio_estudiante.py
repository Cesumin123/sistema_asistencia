from abc import ABC, abstractmethod
from typing import List, Optional
from dominio.estudiante import Estudiante

class PuertoRepositorioEstudiante(ABC):
    """
    Contrato que cualquier adaptador de base de datos debe cumplir
    para gestionar estudiantes.
    """

    @abstractmethod
    def guardar(self, estudiante: Estudiante) -> bool:
        """Guarda un nuevo estudiante en el sistema."""
        pass

    @abstractmethod
    def actualizar(self, estudiante: Estudiante) -> bool:
        """Actualiza los datos de un estudiante existente."""
        pass

    @abstractmethod
    def eliminar(self, cedula: str) -> bool:
        """Realiza un borrado lógico del estudiante (estado_activo = 0)."""
        pass

    @abstractmethod
    def obtener_por_cedula(self, cedula: str) -> Optional[Estudiante]:
        """Busca un estudiante específico por su número de cédula."""
        pass

    @abstractmethod
    def obtener_todos_activos(self) -> List[Estudiante]:
        """Devuelve una lista con todos los estudiantes cuyo estado_activo sea 1."""
        pass