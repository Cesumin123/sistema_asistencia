# dominio/usuario.py
import hashlib
import secrets
from typing import Optional

class Usuario:
    """
    Entidad pura del Dominio. Representa a una persona autenticable en el sistema.
    Gestiona la validación y el hashing criptográfico de contraseñas con PBKDF2-HMAC-SHA256 + salt.
    """
    def __init__(self, nombre_completo: Optional[str], username: str, password: str, rol: str, id_usuario: Optional[int] = None, estado_activo: int = 1):
        self.id_usuario = id_usuario
        self.nombre_completo = nombre_completo.strip().upper() if nombre_completo else ""
        self.rol = rol.strip().upper() if rol else "ADMIN"
        self.username = username.strip() if username else ""
        self.password = password
        self.estado_activo = estado_activo

    @staticmethod
    def generar_hash(password_plano: str, salt: Optional[str] = None) -> str:
        """
        Genera un hash criptográfico seguro en formato salt$hash usando PBKDF2-HMAC-SHA256 con 100,000 iteraciones.
        """
        if not password_plano:
            raise ValueError("La contraseña no puede estar vacía.")
        if not salt:
            salt = secrets.token_hex(16)
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password_plano.encode('utf-8'),
            salt.encode('utf-8'),
            100_000
        )
        return f"{salt}${hash_bytes.hex()}"

    def verificar_password(self, password_plano: str) -> bool:
        """
        Verifica si la contraseña en texto plano coincide con el hash almacenado en formato salt$hash.
        Utiliza secrets.compare_digest para prevenir ataques de tiempo (timing attacks).
        """
        if not self.password or not password_plano:
            return False
        try:
            salt, hash_guardado = self.password.split("$")
            hash_calculado = hashlib.pbkdf2_hmac(
                'sha256',
                password_plano.encode('utf-8'),
                salt.encode('utf-8'),
                100_000
            ).hex()
            return secrets.compare_digest(hash_guardado, hash_calculado)
        except Exception:
            # Compatibilidad defensiva en caso de contraseñas legadas sin migrar
            return secrets.compare_digest(self.password, password_plano)

    def validar(self):
        """Reglas de negocio estrictas para crear o actualizar un usuario."""
        if not self.nombre_completo:
            raise ValueError("El nombre completo es obligatorio.")
        if not self.username:
            raise ValueError("El nombre de usuario es obligatorio.")
        if not self.password:
            raise ValueError("La contraseña es obligatoria.")
        if not self.rol:
            raise ValueError("El rol es obligatorio.")
        if len(self.username) < 4:
            raise ValueError("El nombre de usuario debe tener al menos 4 caracteres.")
        
        # Si la contraseña no está hasheada aún (no contiene '$'), validamos longitud mínima
        if "$" not in self.password and len(self.password) < 4:
            raise ValueError("La contraseña debe tener al menos 4 caracteres por seguridad.")
