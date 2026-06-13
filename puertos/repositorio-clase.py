# puertos/repositorio_clase.py
from abc import ABC, abstractmethod

class RepositorioClase(ABC):
    """
    Contrato que la base de datos debe cumplir para gestionar las clases.
    """
    @abstractmethod
    def obtener_profesores_activos(self) -> list:
        pass

    @abstractmethod
    def obtener_grados(self) -> list:
        pass

    @abstractmethod
    def obtener_secciones(self) -> list:
        pass

    @abstractmethod
    def guardar_lote(self, lista_clases: list):
        """Permite guardar varias clases al mismo tiempo (ej. 'Matemáticas' para sección A, B y C)"""
        pass