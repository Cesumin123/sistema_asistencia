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
        # Lo implementaremos luego para cuando refactoricemos la creación de materias
        pass