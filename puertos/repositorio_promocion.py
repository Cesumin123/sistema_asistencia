# puertos/repositorio_promocion.py
"""
Puerto / Contrato abstracto para el Módulo de Promoción Anual en Cascada (RF-16).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dominio.promocion import ResumenGradoPromocion, ResultadoPromocion


class PuertoRepositorioPromocion(ABC):
    """Contrato que el Adaptador SQLite de Promoción debe satisfacer."""

    @abstractmethod
    def obtener_resumen_grados(self) -> List[ResumenGradoPromocion]:
        """
        Retorna la vista previa de estudiantes activos distribuidos por grado escolar.
        """
        pass

    @abstractmethod
    def ejecutar_promocion_cascada(self, usuario_responsable: str = "ADMIN") -> ResultadoPromocion:
        """
        Ejecuta la actualización en cascada descendente en una única transacción atómica
        (5to->6to, 4to->5to, 3ro->4to, 2do->3ro, 1ro->2do), afectando solo ESTADO_ACTIVO = 1
        y registrando la auditoría del sistema.
        """
        pass
