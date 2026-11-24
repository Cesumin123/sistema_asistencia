# puertos/repositorio_usuario.py
from abc import ABC, abstractmethod
from typing import Optional, List
from dominio.usuario import Usuario

class RepositorioUsuario(ABC):
    """
    Contrato para la persistencia y autenticación de Usuarios.
    """
    @abstractmethod
    def obtener_activos(self) -> List[Usuario]:
        pass

    @abstractmethod
    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        pass

    @abstractmethod
    def guardar(self, usuario: Usuario):
        pass

    @abstractmethod
    def actualizar(self, usuario: Usuario):
        pass

    @abstractmethod
    def desactivar(self, id_usuario: int): 
        """Borrado Lógico: No usa DELETE, cambia ESTADO_ACTIVO a 0."""
        pass

    @abstractmethod
    def autenticar(self, username: str, password_plano: str) -> Optional[Usuario]:
        """Verifica credenciales contra el hash seguro almacenado."""
        pass
