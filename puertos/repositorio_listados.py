# puertos/repositorio_listados.py
"""
Puerto / Contrato abstracto para el Módulo de Listados Centralizados (RF-13).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class PuertoRepositorioListados(ABC):
    """Contrato abstracto para la consulta y consolidación de listados institucionales."""

    @abstractmethod
    def obtener_estudiantes_activos(self) -> List[Dict[str, Any]]:
        """
        Recupera el consolidado de estudiantes activos con su información académica
        (cédula, nombre, nacimiento, representante, teléfono, género, grado, sección, etc.).
        """
        pass

    @abstractmethod
    def obtener_materias_consolidadas(self) -> List[Dict[str, Any]]:
        """
        Recupera el consolidado de clases/materias junto con su docente responsable,
        grado y sección.
        """
        pass

    @abstractmethod
    def obtener_profesores_activos(self) -> List[Dict[str, Any]]:
        """
        Recupera la nómina de profesores activos (ID, cédula, nombre completo).
        """
        pass
