# adaptadores/db/sqlite_reportes.py
"""
Adaptador de Persistencia SQLite para el Módulo de Reportes.
Implementa el puerto PuertoRepositorioReportes utilizando consultas SQL parametrizadas
estrictamente con marcadores '?' sobre TBL_ASISTENCIA, TBL_ESTUDIANTES, TBL_CLASES y TBL_JUSTIFICACIONES.
"""

from typing import List, Dict, Optional
import sqlite3

from puertos.repositorio_reportes import PuertoRepositorioReportes
from dominio.reportes import AsistenciaEnriquecida


class RepositorioReportesSQLite(PuertoRepositorioReportes):
    """Implementación SQLite del repositorio de reportes."""

    MESES_MAPA = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }

    def __init__(self, db_conexion):
        self.db = db_conexion

    def _normalizar_mes(self, mes: str) -> str:
        """Convierte nombres o dígitos de mes a formato de dos dígitos '01'-'12'."""
        if not mes:
            return ""
        mes_limpio = str(mes).strip().lower()
        if mes_limpio in self.MESES_MAPA:
            return self.MESES_MAPA[mes_limpio]
        if mes_limpio.isdigit():
            return f"{int(mes_limpio):02d}"
        return mes_limpio

    def obtener_asistencia_por_fecha(self, fecha: str) -> List[AsistenciaEnriquecida]:
        """
        Recupera los registros de asistencia para una fecha exacta (formato YYYY-MM-DD).
        """
        conn = self.db.conectar()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            sql = """
                SELECT A.ID_ESTUDIANTE, E.NOMBRE, E.GENERO, A.FECHA, A.ESTADO,
                       C.NOMBRE_MATERIA, COALESCE(J.MOTIVO, '-')
                FROM TBL_ASISTENCIA A
                JOIN TBL_CLASES C ON A.ID_CLASE = C.ID_CLASE
                JOIN TBL_ESTUDIANTES E ON A.ID_ESTUDIANTE = E.ID_ESTUDIANTE
                LEFT JOIN TBL_JUSTIFICACIONES J ON A.ID_ASISTENCIA = J.ID_ASISTENCIA
                WHERE A.FECHA = ?
                ORDER BY C.NOMBRE_MATERIA, E.NOMBRE
            """
            cursor.execute(sql, (fecha.strip(),))
            filas = cursor.fetchall()

            return [
                AsistenciaEnriquecida(
                    id_estudiante=fila[0],
                    nombre=fila[1],
                    genero=fila[2],
                    fecha=fila[3],
                    estado=fila[4],
                    materia=fila[5],
                    observacion=fila[6]
                )
                for fila in filas
            ]
        finally:
            self.db.cerrar()

    def obtener_asistencia_por_mes(self, mes: str, anio: str = "") -> List[AsistenciaEnriquecida]:
        """
        Recupera los registros de asistencia para un mes específico utilizando strftime('%m', FECHA).
        Opcionalmente filtra por año si se especifica.
        """
        conn = self.db.conectar()
        if not conn:
            return []

        mes_norm = self._normalizar_mes(mes)
        anio_limpio = str(anio).strip() if anio else ""

        try:
            cursor = conn.cursor()
            if anio_limpio:
                sql = """
                    SELECT A.ID_ESTUDIANTE, E.NOMBRE, E.GENERO, A.FECHA, A.ESTADO,
                           C.NOMBRE_MATERIA, COALESCE(J.MOTIVO, '-')
                    FROM TBL_ASISTENCIA A
                    JOIN TBL_CLASES C ON A.ID_CLASE = C.ID_CLASE
                    JOIN TBL_ESTUDIANTES E ON A.ID_ESTUDIANTE = E.ID_ESTUDIANTE
                    LEFT JOIN TBL_JUSTIFICACIONES J ON A.ID_ASISTENCIA = J.ID_ASISTENCIA
                    WHERE strftime('%m', A.FECHA) = ? AND strftime('%Y', A.FECHA) = ?
                    ORDER BY A.FECHA DESC, C.NOMBRE_MATERIA, E.NOMBRE
                """
                cursor.execute(sql, (mes_norm, anio_limpio))
            else:
                sql = """
                    SELECT A.ID_ESTUDIANTE, E.NOMBRE, E.GENERO, A.FECHA, A.ESTADO,
                           C.NOMBRE_MATERIA, COALESCE(J.MOTIVO, '-')
                    FROM TBL_ASISTENCIA A
                    JOIN TBL_CLASES C ON A.ID_CLASE = C.ID_CLASE
                    JOIN TBL_ESTUDIANTES E ON A.ID_ESTUDIANTE = E.ID_ESTUDIANTE
                    LEFT JOIN TBL_JUSTIFICACIONES J ON A.ID_ASISTENCIA = J.ID_ASISTENCIA
                    WHERE strftime('%m', A.FECHA) = ?
                    ORDER BY A.FECHA DESC, C.NOMBRE_MATERIA, E.NOMBRE
                """
                cursor.execute(sql, (mes_norm,))

            filas = cursor.fetchall()
            return [
                AsistenciaEnriquecida(
                    id_estudiante=fila[0],
                    nombre=fila[1],
                    genero=fila[2],
                    fecha=fila[3],
                    estado=fila[4],
                    materia=fila[5],
                    observacion=fila[6]
                )
                for fila in filas
            ]
        finally:
            self.db.cerrar()

    def obtener_historial_estudiante(self, id_estudiante: str) -> List[AsistenciaEnriquecida]:
        """
        Recupera el historial completo de asistencia de un estudiante por su cédula o identificador.
        Soporta coincidencia exacta o parcial segura.
        """
        conn = self.db.conectar()
        if not conn:
            return []

        ced = id_estudiante.strip()
        try:
            cursor = conn.cursor()
            sql = """
                SELECT A.ID_ESTUDIANTE, E.NOMBRE, E.GENERO, A.FECHA, A.ESTADO,
                       C.NOMBRE_MATERIA, COALESCE(J.MOTIVO, '-')
                FROM TBL_ASISTENCIA A
                JOIN TBL_CLASES C ON A.ID_CLASE = C.ID_CLASE
                JOIN TBL_ESTUDIANTES E ON A.ID_ESTUDIANTE = E.ID_ESTUDIANTE
                LEFT JOIN TBL_JUSTIFICACIONES J ON A.ID_ASISTENCIA = J.ID_ASISTENCIA
                WHERE A.ID_ESTUDIANTE = ? OR A.ID_ESTUDIANTE LIKE ?
                ORDER BY A.FECHA DESC, C.NOMBRE_MATERIA
            """
            cursor.execute(sql, (ced, f"%{ced}%"))
            filas = cursor.fetchall()

            return [
                AsistenciaEnriquecida(
                    id_estudiante=fila[0],
                    nombre=fila[1],
                    genero=fila[2],
                    fecha=fila[3],
                    estado=fila[4],
                    materia=fila[5],
                    observacion=fila[6]
                )
                for fila in filas
            ]
        finally:
            self.db.cerrar()

    def obtener_resumen_genero(
        self,
        fecha: Optional[str] = None,
        mes: Optional[str] = None,
        anio: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Ejecuta una agregación SQL para calcular demografía (género y estado de asistencia)
        con filtros opcionales por fecha exacta o por mes/año.
        """
        conn = self.db.conectar()
        if not conn:
            return {}

        filtros = []
        params = []

        if fecha:
            filtros.append("A.FECHA = ?")
            params.append(fecha.strip())
        elif mes:
            mes_norm = self._normalizar_mes(mes)
            filtros.append("strftime('%m', A.FECHA) = ?")
            params.append(mes_norm)
            if anio:
                filtros.append("strftime('%Y', A.FECHA) = ?")
                params.append(str(anio).strip())

        where_clause = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        try:
            cursor = conn.cursor()
            sql = f"""
                SELECT E.GENERO, A.ESTADO, COUNT(*)
                FROM TBL_ASISTENCIA A
                JOIN TBL_ESTUDIANTES E ON A.ID_ESTUDIANTE = E.ID_ESTUDIANTE
                {where_clause}
                GROUP BY E.GENERO, A.ESTADO
            """
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()

            stats: Dict[str, int] = {}
            for gen, est, cantidad in filas:
                clave = f"{gen.upper()}_{est.upper()}"
                stats[clave] = cantidad

            return stats
        finally:
            self.db.cerrar()
