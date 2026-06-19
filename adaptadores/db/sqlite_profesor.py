# adaptadores/db/sqlite_profesor.py
import sqlite3
from puertos.repositorio_profesor import RepositorioProfesor
from dominio.profesor import Profesor

class SQLiteRepositorioProfesor(RepositorioProfesor):
    """
    Adaptador que sabe cómo hablar con SQLite.
    """
    def __init__(self, conexion_bd):
        self.db = conexion_bd

    def guardar(self, profesor: Profesor):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                sql = "INSERT INTO TBL_PROFESORES (NOMBRE_COMPLETO, CEDULA) VALUES (?, ?)"
                cursor.execute(sql, (profesor.nombre_completo, profesor.cedula))
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError("Esa cédula ya se encuentra registrada en el sistema.")
            finally:
                self.db.cerrar()

    def obtener_todos(self) -> list[Profesor]:
        conn = self.db.conectar()
        profesores = []
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT ID_PROFESOR, NOMBRE_COMPLETO, CEDULA, ESTADO_ACTIVO FROM TBL_PROFESORES ORDER BY NOMBRE_COMPLETO")
                rows = cursor.fetchall()
                for r in rows:
                    id_prof, nombre, cedula, estado = r
                    p = Profesor(cedula=cedula, nombre_completo=nombre, id_profesor=id_prof, estado_activo=estado)
                    profesores.append(p)
                return profesores
            finally:
                self.db.cerrar()
        return profesores