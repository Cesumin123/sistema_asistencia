# dominio/clase.py

class Clase:
    """
    Entidad que representa una Materia asignada a un Profesor, Grado y Sección.
    """
    def __init__(self, nombre_materia: str, id_profesor: int, id_grado: int, id_seccion: int):
        self.nombre_materia = str(nombre_materia).strip().upper() if nombre_materia is not None else ""
        self.id_profesor = id_profesor
        self.id_grado = id_grado
        self.id_seccion = id_seccion

    def validar(self):
        """Reglas de negocio fundamentales para una Clase."""
        if not self.nombre_materia or len(self.nombre_materia.strip()) < 3:
            raise ValueError("El nombre de la materia es obligatorio y debe tener al menos 3 caracteres.")
        if not self.id_profesor or not isinstance(self.id_profesor, int) or self.id_profesor <= 0:
            raise ValueError("Debe asignar un profesor válido.")
        if not self.id_grado or not isinstance(self.id_grado, int) or self.id_grado <= 0:
            raise ValueError("Debe asignar un grado válido.")
        if not self.id_seccion or not isinstance(self.id_seccion, int) or self.id_seccion <= 0:
            raise ValueError("Debe asignar una sección válida.")