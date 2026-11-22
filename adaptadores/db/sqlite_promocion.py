# adaptadores/db/sqlite_promocion.py
"""
Adaptador de Persistencia SQLite para Promoción Anual en Cascada (RF-16).
Implementa PuertoRepositorioPromocion con actualización en cascada descendente,
transacción atómica con ROLLBACK ante fallos y registro obligatorio en TBL_AUDITORIA.
"""

from typing import List, Dict, Any
import sqlite3

from puertos.repositorio_promocion import PuertoRepositorioPromocion
from dominio.promocion import (
    ResumenGradoPromocion,
    ResultadoPromocion,
    ServicioPromocionDominio,
)


class RepositorioPromocionSQLite(PuertoRepositorioPromocion):
    """Implementación SQLite del repositorio de promoción anual."""

    def __init__(self, db_conexion):
        self.db = db_conexion

    def obtener_resumen_grados(self) -> List[ResumenGradoPromocion]:
        """
        Retorna la cantidad de estudiantes activos por cada grado del sistema.
        """
        conn = self.db.conectar()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            sql = """
                SELECT G.ID_GRADO, G.DESCRIPCION, COUNT(E.ID_ESTUDIANTE)
                FROM TBL_GRADOS G
                LEFT JOIN TBL_ESTUDIANTES E 
                    ON G.ID_GRADO = E.ID_GRADO 
                    AND E.ESTADO_ACTIVO = 1
                GROUP BY G.ID_GRADO, G.DESCRIPCION
                ORDER BY G.ID_GRADO ASC
            """
            cursor.execute(sql)
            filas = cursor.fetchall()
            return [
                ResumenGradoPromocion(
                    id_grado=fila[0],
                    descripcion=fila[1],
                    total_estudiantes=fila[2]
                )
                for fila in filas
            ]
        finally:
            self.db.cerrar()

    def ejecutar_promocion_cascada(self, usuario_responsable: str = "ADMIN") -> ResultadoPromocion:
        """
        Ejecuta la actualización en cascada descendente dentro de una única transacción atómica:
        1. Asegura la existencia de Grado 6 (GRADUADO).
        2. Promueve en orden estrictamente descendente:
           - 5to -> 6to
           - 4to -> 5to
           - 3ro -> 4to
           - 2do -> 3ro
           - 1ro -> 2do
           Afectando exclusivamente estudiantes activos (ESTADO_ACTIVO = 1).
        3. Registra el evento en TBL_AUDITORIA.
        4. Aplica COMMIT atómico o ROLLBACK ante cualquier error.
        """
        conn = self.db.conectar()
        if not conn:
            raise ConnectionError("No se pudo conectar a la base de datos para la promoción.")

        detalles_por_grado: Dict[str, int] = {}
        total_promovidos = 0

        try:
            cursor = conn.cursor()

            # Asegurar grado 6
            cursor.execute(
                "INSERT OR IGNORE INTO TBL_GRADOS (ID_GRADO, DESCRIPCION) VALUES (6, 'GRADUADO')"
            )

            # Cascada Inversa / Descendente
            for origen, destino in ServicioPromocionDominio.SECUENCIA_CASCADA_DESCENDENTE:
                cursor.execute(
                    """
                    UPDATE TBL_ESTUDIANTES
                    SET ID_GRADO = ?
                    WHERE ID_GRADO = ? AND ESTADO_ACTIVO = 1
                    """,
                    (destino, origen)
                )
                afectados = cursor.rowcount
                detalles_por_grado[f"{origen}_a_{destino}"] = afectados
                total_promovidos += afectados

            # Registro en TBL_AUDITORIA
            detalle_texto = (
                f"Promoción anual ejecutada con éxito. Total promovidos: {total_promovidos}. "
                f"Detalle: 5to->Graduado: {detalles_por_grado.get('5_a_6', 0)}, "
                f"4to->5to: {detalles_por_grado.get('4_a_5', 0)}, "
                f"3ro->4to: {detalles_por_grado.get('3_a_4', 0)}, "
                f"2do->3ro: {detalles_por_grado.get('2_a_3', 0)}, "
                f"1ro->2do: {detalles_por_grado.get('1_a_2', 0)}."
            )

            cursor.execute(
                """
                INSERT INTO TBL_AUDITORIA (FECHA_HORA, USUARIO, MODULO, ACCION, DETALLES)
                VALUES (datetime('now', 'localtime'), ?, 'PROMOCION_ANUAL', 'EJECUTAR_CASCADA', ?)
                """,
                (usuario_responsable, detalle_texto)
            )

            conn.commit()

            return ResultadoPromocion(
                exito=True,
                total_promovidos=total_promovidos,
                detalles_por_grado=detalles_por_grado,
                mensaje=f"Promoción anual completada exitosamente. Total estudiantes promovidos: {total_promovidos}."
            )

        except Exception as error:
            conn.rollback()
            raise RuntimeError(f"Fallo crítico durante la promoción en cascada. Se ejecutó Rollback: {error}")
        finally:
            self.db.cerrar()
