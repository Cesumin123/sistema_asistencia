# adaptadores/db/sqlite_usuario.py
import sqlite3
from typing import Optional, List, Tuple
from puertos.repositorio_usuario import RepositorioUsuario
from dominio.usuario import Usuario, ServicioRecuperacionUsuario

class SQLiteRepositorioUsuario(RepositorioUsuario):
    """
    Adaptador de Persistencia SQLite para Usuarios.
    Garantiza el almacenamiento seguro con hashing PBKDF2 y borrado lógico con ESTADO_ACTIVO.
    """
    def __init__(self, conexion_bd):
        self.db = conexion_bd

    def obtener_activos(self) -> List[Usuario]:
        conn = self.db.conectar()
        usuarios = []
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ID_USUARIO, NOMBRE_COMPLETO, USERNAME, PASSWORD, ROL, ESTADO_ACTIVO "
                    "FROM TBL_USUARIOS WHERE ESTADO_ACTIVO = 1"
                )
                for fila in cursor.fetchall():
                    nombre = fila[1] if fila[1] else "ADMINISTRADOR GENERAL"
                    usuarios.append(Usuario(
                        id_usuario=fila[0],
                        nombre_completo=nombre,
                        username=fila[2],
                        password=fila[3],
                        rol=fila[4],
                        estado_activo=fila[5]
                    ))
            finally:
                self.db.cerrar()
        return usuarios

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ID_USUARIO, NOMBRE_COMPLETO, USERNAME, PASSWORD, ROL, ESTADO_ACTIVO "
                    "FROM TBL_USUARIOS WHERE USERNAME = ? AND ESTADO_ACTIVO = 1",
                    (username,)
                )
                fila = cursor.fetchone()
                if fila:
                    nombre = fila[1] if fila[1] else "ADMINISTRADOR GENERAL"
                    return Usuario(
                        id_usuario=fila[0],
                        nombre_completo=nombre,
                        username=fila[2],
                        password=fila[3],
                        rol=fila[4],
                        estado_activo=fila[5]
                    )
            finally:
                self.db.cerrar()
        return None

    def guardar(self, usuario: Usuario):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # Cifrado seguro PBKDF2 si la contraseña viene en texto plano
                password_almacenar = usuario.password
                if "$" not in password_almacenar:
                    password_almacenar = Usuario.generar_hash(password_almacenar)
                    usuario.password = password_almacenar

                sql = "INSERT INTO TBL_USUARIOS (NOMBRE_COMPLETO, USERNAME, PASSWORD, ROL, ESTADO_ACTIVO) VALUES (?, ?, ?, ?, 1)"
                cursor.execute(sql, (usuario.nombre_completo, usuario.username, password_almacenar, usuario.rol))
                conn.commit()
                usuario.id_usuario = cursor.lastrowid
            except sqlite3.IntegrityError:
                raise ValueError("Ese Username ya está en uso. Por favor elija otro.")
            finally:
                self.db.cerrar()

    def actualizar(self, usuario: Usuario):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                password_almacenar = usuario.password
                # Si se cambió la contraseña y no está hasheada ni es la máscara "********"
                if "$" not in password_almacenar and password_almacenar != "********":
                    password_almacenar = Usuario.generar_hash(password_almacenar)
                    usuario.password = password_almacenar

                sql = "UPDATE TBL_USUARIOS SET NOMBRE_COMPLETO=?, USERNAME=?, PASSWORD=?, ROL=? WHERE ID_USUARIO=?"
                cursor.execute(sql, (usuario.nombre_completo, usuario.username, password_almacenar, usuario.rol, usuario.id_usuario))
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError("Ese Username ya está en uso por otra persona.")
            finally:
                self.db.cerrar()

    def desactivar(self, id_usuario: int):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE TBL_USUARIOS SET ESTADO_ACTIVO = 0 WHERE ID_USUARIO=?", (id_usuario,))
                conn.commit()
            finally:
                self.db.cerrar()

    def autenticar(self, username: str, password_plano: str) -> Optional[Usuario]:
        """Autentica a un usuario verificando su contraseña plana contra el hash PBKDF2."""
        usuario = self.obtener_por_username(username)
        if usuario and usuario.verificar_password(password_plano):
            return usuario
        return None

    def obtener_usernames_activos(self) -> List[Tuple[str, str]]:
        """Retorna lista de tuplas (username, rol) solo para usuarios activos, sin exponer hashes."""
        conn = self.db.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT USERNAME, ROL FROM TBL_USUARIOS "
                "WHERE ESTADO_ACTIVO = 1 ORDER BY USERNAME ASC"
            )
            return [(str(fila[0]), str(fila[1])) for fila in cursor.fetchall()]
        finally:
            self.db.cerrar()

    def restablecer_contrasena_con_auditoria(
        self,
        username: str,
        nueva_password_plana: str,
        clave_maestra: str,
        ejecutor: str = "RECUPERACION_LOGIN",
    ) -> bool:
        """
        Valida la clave maestra institucional, verifica usuario activo y regla de contraseña,
        re-hashea con PBKDF2-HMAC-SHA256 (salt nuevo) y registra en TBL_AUDITORIA atómicamente.
        """
        ServicioRecuperacionUsuario.validar_clave_maestra(clave_maestra)
        password_validada = ServicioRecuperacionUsuario.validar_nueva_password(nueva_password_plana)

        username_limpio = str(username).strip() if username is not None else ""
        if not username_limpio:
            raise ValueError("Debe seleccionar un nombre de usuario válido.")

        ejecutor_limpio = str(ejecutor or "RECUPERACION_LOGIN").strip().upper() or "RECUPERACION_LOGIN"

        conn = self.db.conectar()
        if not conn:
            raise ConnectionError("No se pudo conectar a la base de datos.")

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ID_USUARIO FROM TBL_USUARIOS WHERE USERNAME = ? AND ESTADO_ACTIVO = 1",
                (username_limpio,),
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValueError(f"El usuario '{username_limpio}' no existe o está inactivo.")

            id_usuario = int(fila[0])
            nuevo_hash = Usuario.generar_hash(password_validada)

            cursor.execute(
                "UPDATE TBL_USUARIOS SET PASSWORD = ? WHERE ID_USUARIO = ? AND ESTADO_ACTIVO = 1",
                (nuevo_hash, id_usuario),
            )

            detalle_auditoria = (
                f"Restablecimiento offline de credenciales para usuario '{username_limpio}'."
            )
            cursor.execute(
                """
                INSERT INTO TBL_AUDITORIA (FECHA_HORA, USUARIO, MODULO, ACCION, DETALLES)
                VALUES (datetime('now', 'localtime'), ?, 'SEGURIDAD', 'RESTABLECER_CREDENCIALES', ?)
                """,
                (ejecutor_limpio, detalle_auditoria),
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            self.db.cerrar()
