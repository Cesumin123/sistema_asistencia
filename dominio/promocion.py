# dominio/promocion.py
"""
Núcleo de Dominio: Reglas de Promoción Anual en Cascada Inversa (RF-16).
Reglas de negocio puras, desacopladas de SQLite y Tkinter.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict


@dataclass
class ResumenGradoPromocion:
    """Entidad que describe la cantidad de estudiantes activos en un grado."""
    id_grado: int
    descripcion: str
    total_estudiantes: int


@dataclass
class ResultadoPromocion:
    """Resultado de la ejecución de promoción en cascada."""
    exito: bool
    total_promovidos: int
    detalles_por_grado: Dict[str, int]
    mensaje: str


class ServicioPromocionDominio:
    """
    Servicio de Dominio que encapsula la lógica y seguridad de la Promoción Anual.
    """
    CLAVE_MAESTRA_DEFAULT = "DIRECTOR2025"

    # Transiciones en orden estrictamente descendente para evitar efecto avalancha:
    # 5to -> 6to (GRADUADO)
    # 4to -> 5to
    # 3ro -> 4to
    # 2do -> 3ro
    # 1ro -> 2do
    SECUENCIA_CASCADA_DESCENDENTE: List[Tuple[int, int]] = [
        (5, 6),
        (4, 5),
        (3, 4),
        (2, 3),
        (1, 2),
    ]

    @classmethod
    def validar_autorizacion(cls, clave_ingresada: str, clave_esperada: str = CLAVE_MAESTRA_DEFAULT) -> bool:
        """
        Valida la clave maestra de seguridad administrativa antes de autorizar la promoción.
        Lanza PermissionError si no coincide.
        """
        if not clave_ingresada or str(clave_ingresada).strip() != str(clave_esperada).strip():
            raise PermissionError("Clave maestra administrativa inválida. Operación de promoción cancelada por seguridad.")
        return True
