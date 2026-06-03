# puertos/repositorio_profesor.py
from abc import ABC, abstractmethod
from dominio.profesor import Profesor

class RepositorioProfesor(ABC):
    """
    Puerto de salida. Define las operaciones que la base de datos DEBE cumplir.
    """
    @abstractmethod
    def guardar(self, profesor: Profesor):
        pass

    @abstractmethod
    def obtener_todos(self) -> list[Profesor]:
        pass