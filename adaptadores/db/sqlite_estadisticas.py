# adaptadores/db/sqlite_estadisticas.py
"""
Adaptador de Persistencia SQLite para el Módulo de Estadísticas Institucionales.
Consultas parametrizadas de solo lectura coherentes con los filtros de activos
del repositorio (ESTADO_ACTIVO = 1).
"""

from typing import List
import sqlite3

from puertos.repositorio_estadisticas import PuertoRepositorioEstadisticas
from dominio.estadisticas import (
    ResumenEstadisticoGeneral,
    DistribucionEstados,
    DistribucionGenero,
    MetricaSeccion,
    EstudianteEnRiesgo,
    CalculadoraEstadisticas,
)


class RepositorioEstadisticasSQLite(PuertoRepositorioEstadisticas):
    """Implementación SQLite de solo lectura para estadísticas institucionales."""

    def __init__(self, db_conexion):
        self.db = db_conexion

    @staticmethod
    def _acortar_grado(descripcion_grado: str) -> str:
        """Convierte '4to AÑO' en '4to' para etiquetas legibles en canvas."""
        texto = str(descripcion_grado or "").strip()
        return texto.replace(" AÑO", "").replace(" Año", "").strip()

    def obtener_resumen_institucional(self) -> ResumenEstadisticoGeneral:
        """Consulta métricas agregadas globales, por sección, género y alertas < 75%."""
        conn = self.db.conectar()
        if not conn:
            return ResumenEstadisticoGeneral()

        try:
            cursor = conn.cursor()

            # 1. Totales globales activos
            cursor.execute("SELECT COUNT(*) FROM TBL_ESTUDIANTES WHERE ESTADO_ACTIVO = 1")
            total_estudiantes = int(cursor.fetchone()[0] or 0)

            cursor.execute("SELECT COUNT(*) FROM TBL_PROFESORES WHERE ESTADO_ACTIVO = 1")
            total_docentes = int(cursor.fetchone()[0] or 0)

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM TBL_CLASES C
                LEFT JOIN TBL_PROFESORES P ON C.ID_PROFESOR = P.ID_PROFESOR
                WHERE COALESCE(P.ESTADO_ACTIVO, 1) = 1
                """
            )
            total_clases = int(cursor.fetchone()[0] or 0)

            # 2. Distribución global P / A / J (sobre registros de asistencia)
            cursor.execute(
                """
                SELECT UPPER(COALESCE(A.ESTADO, '')), COUNT(*)
                FROM TBL_ASISTENCIA A
                JOIN TBL_ESTUDIANTES E ON A.ID_ESTUDIANTE = E.ID_ESTUDIANTE
                WHERE E.ESTADO_ACTIVO = 1
                GROUP BY UPPER(COALESCE(A.ESTADO, ''))
                """
            )
            conteos_estado = {"P": 0, "A": 0, "J": 0}
            for estado, cant in cursor.fetchall():
                if estado in conteos_estado:
                    conteos_estado[estado] = int(cant or 0)

            dist_estados = DistribucionEstados(
                presentes=conteos_estado["P"],
                ausentes=conteos_estado["A"],
                justificadas=conteos_estado["J"],
            )
            total_registros = dist_estados.total
            tasa_global = dist_estados.porcentaje_efectivo

            # 3. Tasa de asistencia efectiva (%) agrupada por Grado y Sección
            cursor.execute(
                """
                SELECT G.DESCRIPCION,
                       S.DESCRIPCION,
                       SUM(CASE WHEN UPPER(A.ESTADO) = 'P' THEN 1 ELSE 0 END) AS P,
                       SUM(CASE WHEN UPPER(A.ESTADO) = 'A' THEN 1 ELSE 0 END) AS A,
                       SUM(CASE WHEN UPPER(A.ESTADO) = 'J' THEN 1 ELSE 0 END) AS J,
                       COUNT(A.ID_ASISTENCIA) AS TOTAL
                FROM TBL_ASISTENCIA A
                JOIN TBL_ESTUDIANTES E ON A.ID_ESTUDIANTE = E.ID_ESTUDIANTE
                JOIN TBL_GRADOS G ON E.ID_GRADO = G.ID_GRADO
                JOIN TBL_SECCIONES S ON E.ID_SECCION = S.ID_SECCION
                WHERE E.ESTADO_ACTIVO = 1
                GROUP BY G.ID_GRADO, G.DESCRIPCION, S.ID_SECCION, S.DESCRIPCION
                ORDER BY G.ID_GRADO ASC, S.DESCRIPCION ASC
                """
            )
            metricas_seccion: List[MetricaSeccion] = []
            for grado_desc, sec_desc, p, a, j, tot in cursor.fetchall():
                p_i, a_i, j_i, tot_i = int(p or 0), int(a or 0), int(j or 0), int(tot or 0)
                tasa_sec = CalculadoraEstadisticas.calcular_tasa_efectiva(p_i, j_i, tot_i)
                etiqueta = f"{self._acortar_grado(grado_desc)} {sec_desc}".strip()
                metricas_seccion.append(
                    MetricaSeccion(
                        grado=str(grado_desc),
                        seccion=str(sec_desc),
                        etiqueta=etiqueta,
                        presentes=p_i,
                        ausentes=a_i,
                        justificadas=j_i,
                        total_registros=tot_i,
                        tasa_efectiva=tasa_sec,
                    )
                )

            # 4. Distribución demográfica por género (M / F) de estudiantes activos
            cursor.execute(
                """
                SELECT UPPER(COALESCE(GENERO, '')), COUNT(*)
                FROM TBL_ESTUDIANTES
                WHERE ESTADO_ACTIVO = 1
                GROUP BY UPPER(COALESCE(GENERO, ''))
                """
            )
            masc = 0
            fem = 0
            for gen, cant in cursor.fetchall():
                if gen == "M":
                    masc = int(cant or 0)
                elif gen == "F":
                    fem = int(cant or 0)
            dist_genero = DistribucionGenero(masculino=masc, femenino=fem)

            # 5. Estudiantes activos en alerta crítica (< 75.0% Art. 109 RGLOE)
            cursor.execute(
                """
                SELECT E.ID_ESTUDIANTE,
                       E.NOMBRE,
                       G.DESCRIPCION,
                       S.DESCRIPCION,
                       SUM(CASE WHEN UPPER(A.ESTADO) = 'P' THEN 1 ELSE 0 END) AS P,
                       SUM(CASE WHEN UPPER(A.ESTADO) = 'J' THEN 1 ELSE 0 END) AS J,
                       SUM(CASE WHEN UPPER(A.ESTADO) = 'A' THEN 1 ELSE 0 END) AS A,
                       COUNT(A.ID_ASISTENCIA) AS TOTAL
                FROM TBL_ESTUDIANTES E
                JOIN TBL_ASISTENCIA A ON E.ID_ESTUDIANTE = A.ID_ESTUDIANTE
                JOIN TBL_GRADOS G ON E.ID_GRADO = G.ID_GRADO
                JOIN TBL_SECCIONES S ON E.ID_SECCION = S.ID_SECCION
                WHERE E.ESTADO_ACTIVO = 1
                GROUP BY E.ID_ESTUDIANTE, E.NOMBRE, G.DESCRIPCION, S.DESCRIPCION
                """
            )
            en_riesgo: List[EstudianteEnRiesgo] = []
            for id_est, nombre, grado_desc, sec_desc, p, j, a, tot in cursor.fetchall():
                p_i, j_i, a_i, tot_i = int(p or 0), int(j or 0), int(a or 0), int(tot or 0)
                tasa = CalculadoraEstadisticas.calcular_tasa_efectiva(p_i, j_i, tot_i)
                if CalculadoraEstadisticas.es_en_riesgo(tasa, tot_i):
                    en_riesgo.append(
                        EstudianteEnRiesgo(
                            id_estudiante=str(id_est),
                            nombre=str(nombre),
                            grado=str(grado_desc),
                            seccion=str(sec_desc),
                            total_clases=tot_i,
                            asistencias_efectivas=p_i + j_i,
                            faltas_injustificadas=a_i,
                            porcentaje_asistencia=tasa,
                        )
                    )

            en_riesgo.sort(key=lambda x: (x.porcentaje_asistencia, -x.faltas_injustificadas, x.nombre))

            return ResumenEstadisticoGeneral(
                total_estudiantes_activos=total_estudiantes,
                total_docentes_activos=total_docentes,
                total_clases_activas=total_clases,
                total_registros_asistencia=total_registros,
                tasa_asistencia_global=tasa_global,
                total_en_riesgo=len(en_riesgo),
                distribucion_estados=dist_estados,
                distribucion_genero=dist_genero,
                metricas_por_seccion=metricas_seccion,
                estudiantes_en_riesgo=en_riesgo,
            )
        finally:
            self.db.cerrar()
