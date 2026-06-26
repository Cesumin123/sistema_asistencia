# puertos/repositorio_usuario.py
from abc import ABC, abstractmethod
from dominio.usuario import Usuario

class RepositorioUsuario(ABC):
    """
    Contrato para la base de datos de Usuarios.
    """
    @abstractmethod
    def obtener_activos(self) -> list[Usuario]: pass

    @abstractmethod
    def guardar(self, usuario: Usuario): pass

    @abstractmethod
    def actualizar(self, usuario: Usuario): pass

    @abstractmethod
    def desactivar(self, id_usuario: int): 
        """Borrado Lógico: No usa DELETE, usa UPDATE."""
        pass