# dominio/clase.py

class Clase:
    """
    Entidad que representa una Materia asignada a un Profesor y a un Salón.
    """
    def __init__(self, nombre_materia: str, id_profesor: int, id_grado: int, id_seccion: int):
        self.nombre_materia = nombre_materia.upper()
        self.id_profesor = id_profesor
        self.id_grado = id_grado
        self.id_seccion = id_seccion

    def validar(self):
        """Reglas de negocio fundamentales."""
        if len(self.nombre_materia) < 3:
            raise ValueError("El nombre de la materia es muy corto o está vacío.")
        if not self.id_profesor or not self.id_grado or not self.id_seccion:
            raise ValueError("Faltan datos: Asegúrese de elegir Profesor, Grado y Sección.")