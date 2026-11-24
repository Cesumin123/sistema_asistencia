# adaptadores/db/sqlite_clase.py
"""
Adaptador de Persistencia SQLite para la entidad Clase / Carga Académica.
Implementa el contrato RepositorioClase incluyendo las consultas de selección
necesarias para el módulo de Asistencia (desacoplando SQL de la capa UI).
"""
from typing import List, Tuple
from puertos.repositorio_clase import RepositorioClase


class SQLiteRepositorioClase(RepositorioClase):
    def __init__(self, conexion_bd):
        self.db = conexion_bd

    def obtener_profesores_activos(self):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ID_PROFESOR, NOMBRE_COMPLETO FROM TBL_PROFESORES "
                    "WHERE ESTADO_ACTIVO = 1 ORDER BY NOMBRE_COMPLETO"
                )
                return cursor.fetchall()
            finally:
                self.db.cerrar()
        return []

    def obtener_grados(self):
        conn = self.db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
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
                    sql = (
                        "INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) "
                        "VALUES (?, ?, ?, ?)"
                    )
                    cursor.execute(sql, (c.nombre_materia, c.id_profesor, c.id_grado, c.id_seccion))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise ValueError(f"Error de base de datos: {str(e)}")
            finally:
                self.db.cerrar()

    # ------------------------------------------------------------------
    # Nuevas operaciones requeridas para el módulo de Asistencia (FASE 1)
    # ------------------------------------------------------------------
    def obtener_clases_disponibles(self) -> List[Tuple[int, str]]:
        """Retorna (id_clase, 'MATERIA - GRADO SECCIÓN') ordenado."""
        conn = self.db.conectar()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT C.ID_CLASE, "
                "       C.NOMBRE_MATERIA || ' - ' || G.DESCRIPCION || ' ' || S.DESCRIPCION "
                "FROM TBL_CLASES C "
                "JOIN TBL_GRADOS G ON C.ID_GRADO = G.ID_GRADO "
                "JOIN TBL_SECCIONES S ON C.ID_SECCION = S.ID_SECCION "
                "ORDER BY G.ID_GRADO, S.DESCRIPCION, C.NOMBRE_MATERIA"
            )
            return cursor.fetchall()
        finally:
            self.db.cerrar()

    def obtener_estudiantes_por_clase(self, id_clase: int) -> List[Tuple[str, str]]:
        """Retorna (id_estudiante, nombre) del grado/sección de la clase."""
        conn = self.db.conectar()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT ID_GRADO, ID_SECCION FROM TBL_CLASES WHERE ID_CLASE = ?",
                (id_clase,)
            )
            datos = cur.fetchone()
            if not datos:
                return []
            cur.execute(
                "SELECT ID_ESTUDIANTE, NOMBRE FROM TBL_ESTUDIANTES "
                "WHERE ID_GRADO = ? AND ID_SECCION = ? AND ESTADO_ACTIVO = 1 "
                "ORDER BY NOMBRE",
                (datos[0], datos[1])
            )
            return cur.fetchall()
        finally:
            self.db.cerrar()

    def obtener_nombres_estudiantes(self, ids_estudiantes: List[str]) -> dict:
        """Dado un listado de IDs, retorna {id: nombre}."""
        if not ids_estudiantes:
            return {}
        conn = self.db.conectar()
        if not conn:
            return {}
        try:
            cur = conn.cursor()
            placeholders = ','.join(['?'] * len(ids_estudiantes))
            cur.execute(
                f"SELECT ID_ESTUDIANTE, NOMBRE FROM TBL_ESTUDIANTES "
                f"WHERE ID_ESTUDIANTE IN ({placeholders})",
                ids_estudiantes
            )
            return {row[0]: row[1] for row in cur.fetchall()}
        finally:
            self.db.cerrar()