# dominio/usuario.py

class Usuario:
    """
    Entidad pura. Representa a una persona que puede iniciar sesión en el sistema.
    """
    def __init__(self, nombre_completo: str, username: str, password: str, rol: str, id_usuario: int = None, estado_activo: int = 1):
        self.id_usuario = id_usuario
        self.nombre_completo = nombre_completo.upper()
        self.username = username.upper()
        self.password = password
        self.rol = rol.upper()
        self.estado_activo = estado_activo

    def validar(self):
        """Reglas de negocio estrictas para crear un usuario."""
        if not self.nombre_completo or not self.username or not self.password or not self.rol:
            raise ValueError("Todos los campos son obligatorios.")
        if len(self.username) < 4:
            raise ValueError("El nombre de usuario debe tener al menos 4 caracteres.")
        if len(self.password) < 4:
            raise ValueError("La contraseña debe tener al menos 4 caracteres por seguridad.") 
