# adaptadores/db/sqlite_usuario.py
import sqlite3
from puertos.repositorio_usuario import RepositorioUsuario
from dominio.usuario import Usuario

class SQLiteRepositorioUsuario(RepositorioUsuario):
    def __init__(self, conexion_bd):
        self.db = conexion_bd

    def obtener_activos(self) -> list[Usuario]:
        conn = self.db.conectar()
        usuarios = []
        if conn:
            try:
                cursor = conn.cursor()
                # MAGIA DEL BORRADO LÓGICO: Solo traemos a los que tienen ESTADO_ACTIVO = 1
                cursor.execute("SELECT ID_USUARIO, NOMBRE_COMPLETO, USERNAME, PASSWORD, ROL FROM TBL_USUARIOS WHERE ESTADO_ACTIVO = 1")
                for fila in cursor.fetchall():
                    usuarios.append(Usuario(id_usuario=fila[0], nombre_completo=fila[1], username=fila[2], password=fila[3], rol=fila[4]))
            finally:
                self.db.cerrar()
        return usuarios

    def guardar(self, usuario: Usuario):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                sql = "INSERT INTO TBL_USUARIOS (NOMBRE_COMPLETO, USERNAME, PASSWORD, ROL, ESTADO_ACTIVO) VALUES (?, ?, ?, ?, 1)"
                cursor.execute(sql, (usuario.nombre_completo, usuario.username, usuario.password, usuario.rol))
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError("Ese Username ya está en uso. Por favor elija otro.")
            finally:
                self.db.cerrar()

    def actualizar(self, usuario: Usuario):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                sql = "UPDATE TBL_USUARIOS SET NOMBRE_COMPLETO=?, USERNAME=?, PASSWORD=?, ROL=? WHERE ID_USUARIO=?"
                cursor.execute(sql, (usuario.nombre_completo, usuario.username, usuario.password, usuario.rol, usuario.id_usuario))
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
                # MAGIA DEL BORRADO LÓGICO: Apagamos el interruptor en lugar de borrar la fila
                cursor.execute("UPDATE TBL_USUARIOS SET ESTADO_ACTIVO = 0 WHERE ID_USUARIO=?", (id_usuario,))
                conn.commit()
            finally:
                self.db.cerrar()