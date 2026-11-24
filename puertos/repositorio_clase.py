# puertos/repositorio_clase.py
"""
Puerto (Contrato) para la gestión de Clases / Carga Académica.
Incluye operaciones de consulta necesarias para selección de clases
en módulos como Asistencia (desacoplando SQL de la capa UI).
"""
from abc import ABC, abstractmethod
from typing import List, Tuple


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

    @abstractmethod
    def obtener_clases_disponibles(self) -> List[Tuple[int, str]]:
        """
        Retorna lista de tuplas (id_clase, descripcion_completa) con todas las
        clases registradas, combinando materia, grado y sección.
        """
        pass

    @abstractmethod
    def obtener_estudiantes_por_clase(self, id_clase: int) -> List[Tuple[str, str]]:
        """
        Retorna lista de tuplas (id_estudiante, nombre) correspondientes a los
        estudiantes activos inscritos en el grado y sección de la clase indicada.
        """
        pass

    @abstractmethod
    def obtener_nombres_estudiantes(self, ids_estudiantes: List[str]) -> dict:
        """
        Dado un listado de IDs de estudiante, retorna un diccionario {id: nombre}.
        """
        pass