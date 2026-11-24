# dominio/profesor.py

class Profesor:
    """
    Entidad pura del dominio. Representa a un docente de la institución.
    """
    def __init__(self, cedula: str, nombre_completo: str, 
                 id_profesor: int = None, estado_activo: int = 1):
        self.id_profesor = id_profesor
        self.cedula = str(cedula).strip().upper() if cedula is not None else ""
        self.nombre_completo = str(nombre_completo).strip().upper() if nombre_completo is not None else ""
        self.estado_activo = int(estado_activo) if estado_activo is not None else 1

    def validar(self):
        """Reglas de negocio: Cédula y nombre obligatorios y con formato mínimo."""
        if not self.cedula or not self.cedula.strip():
            raise ValueError("La cédula del profesor es obligatoria.")
        if len(self.cedula.strip()) < 4:
            raise ValueError("La cédula del profesor debe tener al menos 4 caracteres.")
        if not self.nombre_completo or not self.nombre_completo.strip():
            raise ValueError("El nombre completo del profesor es obligatorio.")
        if len(self.nombre_completo.strip()) < 3:
            raise ValueError("El nombre completo del profesor debe tener al menos 3 caracteres.")