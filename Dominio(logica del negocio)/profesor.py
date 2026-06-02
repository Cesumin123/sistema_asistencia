# dominio/profesor.py

class Profesor:
    """
    Entidad pura del dominio. Solo representa lo que es un Profesor.
    """
    def __init__(self, cedula: str, nombre_completo: str, id_profesor: int = None,
                  estado_activo: int = 1
                 ):
        self.id_profesor = id_profesor
        self.cedula = cedula
        self.nombre_completo = nombre_completo
        self.estado_activo = estado_activo

    def validar(self):
        """Regla de negocio: Un profesor debe tener nombre y cédula."""
        if not self.cedula or not self.nombre_completo:
            raise ValueError("La cédula y el nombre son obligatorios.")