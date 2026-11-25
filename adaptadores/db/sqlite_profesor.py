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
            sql = """
                INSERT INTO TBL_PROFESORES 
                (NOMBRE_COMPLETO, CEDULA, ESTADO_ACTIVO, PROFESION, FOTO_PATH, TELEFONO) 
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (
                profesor.nombre_completo, profesor.cedula, profesor.estado_activo,
                profesor.profesion, profesor.foto_path, profesor.telefono
            ))
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
                sql = """
                    UPDATE TBL_PROFESORES SET 
                    NOMBRE_COMPLETO = ?, CEDULA = ?, ESTADO_ACTIVO = ?, 
                    PROFESION = ?, FOTO_PATH = ?, TELEFONO = ? 
                    WHERE ID_PROFESOR = ?
                """
                cursor.execute(sql, (
                    profesor.nombre_completo, profesor.cedula, profesor.estado_activo,
                    profesor.profesion, profesor.foto_path, profesor.telefono, profesor.id_profesor
                ))
            else:
                sql = """
                    UPDATE TBL_PROFESORES SET 
                    NOMBRE_COMPLETO = ?, ESTADO_ACTIVO = ?, 
                    PROFESION = ?, FOTO_PATH = ?, TELEFONO = ? 
                    WHERE CEDULA = ?
                """
                cursor.execute(sql, (
                    profesor.nombre_completo, profesor.estado_activo,
                    profesor.profesion, profesor.foto_path, profesor.telefono, profesor.cedula
                ))
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

    def _mapear_fila(self, fila) -> Profesor:
        """Helper defensivo para reconstruir entidad Profesor tolerando columnas opcionales."""
        id_prof = fila[0]
        nombre = fila[1] or ""
        cedula = fila[2] or ""
        estado = fila[3] if fila[3] is not None else 1
        profesion = fila[4] if len(fila) > 4 and fila[4] is not None else ""
        foto_path = fila[5] if len(fila) > 5 and fila[5] is not None else ""
        telefono = fila[6] if len(fila) > 6 and fila[6] is not None else ""
        return Profesor(
            cedula=cedula, nombre_completo=nombre, id_profesor=id_prof,
            estado_activo=estado, profesion=profesion, foto_path=foto_path,
            telefono=telefono
        )

    def obtener_todos(self) -> List[Profesor]:
        conn = self.db.conectar()
        profesores = []
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ID_PROFESOR, NOMBRE_COMPLETO, CEDULA, ESTADO_ACTIVO, PROFESION, FOTO_PATH, TELEFONO 
                    FROM TBL_PROFESORES ORDER BY NOMBRE_COMPLETO
                """)
                rows = cursor.fetchall()
                for r in rows:
                    profesores.append(self._mapear_fila(r))
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
                cursor.execute("""
                    SELECT ID_PROFESOR, NOMBRE_COMPLETO, CEDULA, ESTADO_ACTIVO, PROFESION, FOTO_PATH, TELEFONO 
                    FROM TBL_PROFESORES WHERE ESTADO_ACTIVO = 1 ORDER BY NOMBRE_COMPLETO
                """)
                rows = cursor.fetchall()
                for r in rows:
                    profesores.append(self._mapear_fila(r))
                return profesores
            finally:
                self.db.cerrar()
        return profesores

    def obtener_por_id(self, id_profesor: int) -> Optional[Profesor]:
        conn = self.db.conectar()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ID_PROFESOR, NOMBRE_COMPLETO, CEDULA, ESTADO_ACTIVO, PROFESION, FOTO_PATH, TELEFONO "
                "FROM TBL_PROFESORES WHERE ID_PROFESOR = ?",
                (id_profesor,)
            )
            fila = cursor.fetchone()
            return self._mapear_fila(fila) if fila else None
        finally:
            self.db.cerrar()

    def obtener_por_cedula(self, cedula: str) -> Optional[Profesor]:
        conn = self.db.conectar()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ID_PROFESOR, NOMBRE_COMPLETO, CEDULA, ESTADO_ACTIVO, PROFESION, FOTO_PATH, TELEFONO "
                "FROM TBL_PROFESORES WHERE CEDULA = ?",
                (str(cedula).strip().upper(),)
            )
            fila = cursor.fetchone()
            return self._mapear_fila(fila) if fila else None
        finally:
            self.db.cerrar()
