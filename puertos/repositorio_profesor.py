# puertos/repositorio_profesor.py
from abc import ABC, abstractmethod
from typing import List, Optional
from dominio.profesor import Profesor

class RepositorioProfesor(ABC):
    """
    Puerto de salida para la persistencia y gestión de Profesores.
    """
    @abstractmethod
    def guardar(self, profesor: Profesor) -> bool:
        pass

    @abstractmethod
    def actualizar(self, profesor: Profesor) -> bool:
        """Actualiza los datos de un profesor existente."""
        pass

    @abstractmethod
    def eliminar(self, identificador) -> bool:
        """Realiza un borrado lógico del profesor (ESTADO_ACTIVO = 0)."""
        pass

    @abstractmethod
    def obtener_todos(self) -> List[Profesor]:
        pass

    @abstractmethod
    def obtener_activos(self) -> List[Profesor]:
        """Devuelve los profesores con ESTADO_ACTIVO = 1."""
        pass

    @abstractmethod
    def obtener_por_id(self, id_profesor: int) -> Optional[Profesor]:
        """Obtiene un profesor por su identificador único."""
        pass

    @abstractmethod
    def obtener_por_cedula(self, cedula: str) -> Optional[Profesor]:
        """Obtiene un profesor por su cédula de identidad."""
        pass