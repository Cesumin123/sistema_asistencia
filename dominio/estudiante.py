from dataclasses import dataclass
from typing import Optional

@dataclass
class Estudiante:
    """
    Entidad principal de la capa de dominio que representa a un estudiante.
    No tiene dependencias externas.
    """
    cedula: str  # Equivale a ID_ESTUDIANTE (Ej: V-12345678)
    nombre: str
    fecha_nacimiento: str
    representante: str
    telefono: str
    genero: str
    escolaridad: str
    turno: str
    condicion: str
    id_grado: int
    id_seccion: int
    estado_activo: int = 1  # 1 = Activo, 0 = Eliminado (Borrado Lógico)

    def validar(self):
        """
        Lógica de negocio simple: Validar que los datos obligatorios existan.
        """
        if not self.cedula or not self.cedula.strip():
            raise ValueError("La cédula del estudiante es obligatoria.")
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del estudiante es obligatorio.")
        if not self.id_grado or not self.id_seccion:
            raise ValueError("El estudiante debe estar asignado a un grado y sección.")