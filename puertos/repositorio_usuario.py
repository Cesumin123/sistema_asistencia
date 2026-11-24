# puertos/repositorio_usuario.py
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
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

    @abstractmethod
    def obtener_usernames_activos(self) -> List[Tuple[str, str]]:
        """Retorna lista de tuplas (username, rol) solo para usuarios activos, sin exponer hashes."""
        pass

    @abstractmethod
    def restablecer_contrasena_con_auditoria(
        self,
        username: str,
        nueva_password_plana: str,
        clave_maestra: str,
        ejecutor: str = "RECUPERACION_LOGIN",
    ) -> bool:
        """Valida clave maestra, actualiza hash PBKDF2 y registra en TBL_AUDITORIA atómicamente."""
        pass
