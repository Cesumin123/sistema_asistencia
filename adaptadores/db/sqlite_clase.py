# adaptadores/db/sqlite_clase.py
from puertos.repositorio_clase import RepositorioClase

class SQLiteRepositorioClase(RepositorioClase):
    def __init__(self, conexion_bd):
        self.db = conexion_bd

    def obtener_profesores_activos(self):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # Solo traemos a los que NO están borrados (Borrado Lógico)
                cursor.execute("SELECT ID_PROFESOR, NOMBRE_COMPLETO FROM TBL_PROFESORES WHERE ESTADO_ACTIVO = 1 ORDER BY NOMBRE_COMPLETO")
                return cursor.fetchall()
            finally:
                self.db.cerrar()
        return []

    def obtener_grados(self):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # El grado 6 es GRADUADO, a ellos no se les asignan materias
                cursor.execute("SELECT ID_GRADO, DESCRIPCION FROM TBL_GRADOS WHERE ID_GRADO < 6")
                return cursor.fetchall()
            finally:
                self.db.cerrar()
        return []

    def obtener_secciones(self):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT ID_SECCION, DESCRIPCION FROM TBL_SECCIONES")
                return cursor.fetchall()
            finally:
                self.db.cerrar()
        return []

    def guardar_lote(self, lista_clases):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                for c in lista_clases:
                    sql = "INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES (?, ?, ?, ?)"
                    cursor.execute(sql, (c.nombre_materia, c.id_profesor, c.id_grado, c.id_seccion))
                conn.commit()
            except Exception as e:
                conn.rollback() # Si algo falla, deshacemos todo para no dejar la base de datos a medias
                raise ValueError(f"Error de base de datos: {str(e)}")
            finally:
                self.db.cerrar()