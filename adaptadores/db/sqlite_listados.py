# adaptadores/db/sqlite_listados.py
"""
Adaptador de Persistencia SQLite para Listados Centralizados (RF-13).
Consultas parametrizadas de solo lectura para obtener consolidados
de estudiantes activos, clases/materias y nómina de profesores.
"""

from typing import List, Dict, Any
import sqlite3

from puertos.repositorio_listados import PuertoRepositorioListados


class RepositorioListadosSQLite(PuertoRepositorioListados):
    """Implementación SQLite para consultas consolidadas de listados institucionales."""

    def __init__(self, db_conexion):
        self.db = db_conexion

    def obtener_estudiantes_activos(self) -> List[Dict[str, Any]]:
        """
        Retorna la lista de todos los estudiantes activos (ESTADO_ACTIVO = 1)
        ordenados por grado, sección y nombre.
        """
        conn = self.db.conectar()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            sql = """
                SELECT E.ID_ESTUDIANTE, E.NOMBRE, E.FECHA_NACIMIENTO, E.REPRESENTANTE,
                       COALESCE(E.TELEFONO, '-') AS TELEFONO, E.GENERO,
                       G.DESCRIPCION AS GRADO, S.DESCRIPCION AS SECCION,
                       E.CONDICION, E.TURNO, E.ESCOLARIDAD
                FROM TBL_ESTUDIANTES E
                JOIN TBL_GRADOS G ON E.ID_GRADO = G.ID_GRADO
                JOIN TBL_SECCIONES S ON E.ID_SECCION = S.ID_SECCION
                WHERE E.ESTADO_ACTIVO = 1
                ORDER BY G.ID_GRADO ASC, S.DESCRIPCION ASC, E.NOMBRE ASC
            """
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [
                {
                    "cedula": fila[0],
                    "nombre": fila[1],
                    "nacimiento": fila[2],
                    "representante": fila[3],
                    "telefono": fila[4],
                    "genero": fila[5],
                    "grado": fila[6],
                    "seccion": fila[7],
                    "condicion": fila[8],
                    "turno": fila[9],
                    "escolaridad": fila[10]
                }
                for fila in filas
            ]
        finally:
            self.db.cerrar()

    def obtener_materias_consolidadas(self) -> List[Dict[str, Any]]:
        """
        Retorna todas las clases/materias asignadas con profesor, grado y sección.
        """
        conn = self.db.conectar()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            sql = """
                SELECT C.ID_CLASE, C.NOMBRE_MATERIA,
                       COALESCE(P.NOMBRE_COMPLETO, 'Sin Asignar') AS PROFESOR,
                       G.DESCRIPCION AS GRADO, S.DESCRIPCION AS SECCION
                FROM TBL_CLASES C
                LEFT JOIN TBL_PROFESORES P ON C.ID_PROFESOR = P.ID_PROFESOR
                JOIN TBL_GRADOS G ON C.ID_GRADO = G.ID_GRADO
                JOIN TBL_SECCIONES S ON C.ID_SECCION = S.ID_SECCION
                ORDER BY G.ID_GRADO ASC, S.DESCRIPCION ASC, C.NOMBRE_MATERIA ASC
            """
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [
                {
                    "id_clase": fila[0],
                    "materia": fila[1],
                    "profesor": fila[2],
                    "grado": fila[3],
                    "seccion": fila[4]
                }
                for fila in filas
            ]
        finally:
            self.db.cerrar()

    def obtener_profesores_activos(self) -> List[Dict[str, Any]]:
        """
        Retorna la nómina de profesores activos (ESTADO_ACTIVO = 1).
        """
        conn = self.db.conectar()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            sql = """
                SELECT P.ID_PROFESOR, P.CEDULA, P.NOMBRE_COMPLETO, COALESCE(P.TELEFONO, '')
                FROM TBL_PROFESORES P
                WHERE P.ESTADO_ACTIVO = 1
                ORDER BY P.NOMBRE_COMPLETO ASC
            """
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [
                {
                    "id_profesor": fila[0],
                    "cedula": fila[1],
                    "nombre": fila[2],
                    "telefono": fila[3] if fila[3] else "-",
                }
                for fila in filas
            ]
        finally:
            self.db.cerrar()
