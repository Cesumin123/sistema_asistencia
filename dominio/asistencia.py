from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import date

class EstadoAsistencia(Enum):
    PRESENTE = "P"
    AUSENTE = "A"
    JUSTIFICADO = "J"

@dataclass
class RegistroAsistencia:
    """Representa la asistencia individual de un estudiante."""
    id_estudiante: str
    estado: EstadoAsistencia = EstadoAsistencia.PRESENTE
    motivo_justificacion: Optional[str] = None

    def justificar(self, motivo: str):
        self.estado = EstadoAsistencia.JUSTIFICADO
        self.motivo_justificacion = motivo

    def marcar_presente(self):
        self.estado = EstadoAsistencia.PRESENTE
        self.motivo_justificacion = None

    def marcar_ausente(self):
        self.estado = EstadoAsistencia.AUSENTE
        self.motivo_justificacion = None

@dataclass
class PlanillaAsistencia:
    """Raíz del Agregado: Representa la lista de asistencia de una clase en un día."""
    id_clase: int
    fecha: str
    registros: List[RegistroAsistencia] = field(default_factory=list)

    def actualizar_registro(self, id_estudiante: str, nuevo_estado: EstadoAsistencia, motivo: str = None):
        """Lógica de negocio pura para modificar el estado de un alumno."""
        for registro in self.registros:
            if registro.id_estudiante == id_estudiante:
                if nuevo_estado == EstadoAsistencia.JUSTIFICADO and motivo:
                    registro.justificar(motivo)
                elif nuevo_estado == EstadoAsistencia.AUSENTE:
                    registro.marcar_ausente()
                else:
                    registro.marcar_presente()
                break