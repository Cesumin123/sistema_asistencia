# adaptadores/db/sqlite_profesor.py
import sqlite3
from typing import List, Optional
from puertos.repositorio_profesor import RepositorioProfesor
from dominio.profesor import Profesor

class SQLiteRepositorioProfesor(RepositorioProfesor):
    """
    Adaptador de Persistencia SQLite para Profesores.
    """
    def __init__(self, conexion_bd):
        self.db = conexion_bd

    def guardar(self, profesor: Profesor) -> bool:
        conn = self.db.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO TBL_PROFESORES (NOMBRE_COMPLETO, CEDULA, ESTADO_ACTIVO) VALUES (?, ?, ?)"
            cursor.execute(sql, (profesor.nombre_completo, profesor.cedula, profesor.estado_activo))
            conn.commit()
            profesor.id_profesor = cursor.lastrowid
            return True
        except sqlite3.IntegrityError:
            raise ValueError("Esa cédula ya se encuentra registrada en el sistema.")
        finally:
            self.db.cerrar()

    def actualizar(self, profesor: Profesor) -> bool:
        conn = self.db.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            if profesor.id_profesor:
                sql = "UPDATE TBL_PROFESORES SET NOMBRE_COMPLETO = ?, CEDULA = ?, ESTADO_ACTIVO = ? WHERE ID_PROFESOR = ?"
                cursor.execute(sql, (profesor.nombre_completo, profesor.cedula, profesor.estado_activo, profesor.id_profesor))
            else:
                sql = "UPDATE TBL_PROFESORES SET NOMBRE_COMPLETO = ?, ESTADO_ACTIVO = ? WHERE CEDULA = ?"
                cursor.execute(sql, (profesor.nombre_completo, profesor.estado_activo, profesor.cedula))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            self.db.cerrar()

    def eliminar(self, identificador) -> bool:
        """Borrado lógico (ESTADO_ACTIVO = 0). Acepta ID_PROFESOR (int) o CEDULA (str)."""
        conn = self.db.conectar()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            if isinstance(identificador, int) or (isinstance(identificador, str) and identificador.isdigit()):
                sql = "UPDATE TBL_PROFESORES SET ESTADO_ACTIVO = 0 WHERE ID_PROFESOR = ?"
            else:
                sql = "UPDATE TBL_PROFESORES SET ESTADO_ACTIVO = 0 WHERE CEDULA = ?"
            cursor.execute(sql, (identificador,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            self.db.cerrar()

    def obtener_todos(self) -> List[Profesor]:
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

    def obtener_activos(self) -> List[Profesor]:
        conn = self.db.conectar()
        profesores = []
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT ID_PROFESOR, NOMBRE_COMPLETO, CEDULA, ESTADO_ACTIVO FROM TBL_PROFESORES WHERE ESTADO_ACTIVO = 1 ORDER BY NOMBRE_COMPLETO")
                rows = cursor.fetchall()
                for r in rows:
                    id_prof, nombre, cedula, estado = r
                    p = Profesor(cedula=cedula, nombre_completo=nombre, id_profesor=id_prof, estado_activo=estado)
                    profesores.append(p)
                return profesores
            finally:
                self.db.cerrar()
        return profesores