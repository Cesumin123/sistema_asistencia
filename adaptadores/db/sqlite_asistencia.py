import sqlite3
import re
from typing import Optional

from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia
from puertos.repositorio_asistencia import PuertoRepositorioAsistencia

class RepositorioAsistenciaSQLite(PuertoRepositorioAsistencia):
    def __init__(self, db_conexion):
        self.db = db_conexion

    def guardar_planilla(self, planilla: PlanillaAsistencia) -> None:
        # --- BLINDAJE 0: Validación Defensiva de Fecha ISO ---
        # Verificamos que la fecha cumpla con el formato YYYY-MM-DD
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", planilla.fecha):
            raise ValueError(f"Error de Arquitectura: La fecha '{planilla.fecha}' no está en formato ISO 8601 (YYYY-MM-DD).")

        conn = self.db.conectar()
        if not conn:
            raise ConnectionError("No se pudo conectar a la base de datos para guardar la asistencia.")

        try:
            cursor = conn.cursor()
            
            # --- BLINDAJE 1: Limpieza preventiva ---
            # Como se configuro 'PRAGMA foreign_keys = ON' y 'ON DELETE CASCADE' 
            # en la bd, esto también borrará las justificaciones atadas.
            cursor.execute(
                "DELETE FROM TBL_ASISTENCIA WHERE ID_CLASE = ? AND FECHA = ?",
                (planilla.id_clase, planilla.fecha)
            )

            # --- BLINDAJE 2: Inserción en lote ---
            for registro in planilla.registros:
                cursor.execute(
                    """
                    INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO)
                    VALUES (?, ?, ?, ?)
                    """,
                    (planilla.id_clase, registro.id_estudiante, planilla.fecha, registro.estado.value)
                )

                if registro.estado == EstadoAsistencia.JUSTIFICADO and registro.motivo_justificacion:
                    id_asistencia = cursor.lastrowid
                    cursor.execute(
                        """
                        INSERT INTO TBL_JUSTIFICACIONES (ID_ASISTENCIA, MOTIVO)
                        VALUES (?, ?)
                        """,
                        (id_asistencia, registro.motivo_justificacion)
                    )
            
            # --- BLINDAJE 3: Transacción Atómica ---
            conn.commit()
            
        except sqlite3.Error as error_bd:
            conn.rollback() 
            raise Exception(f"Fallo crítico al guardar la asistencia: {error_bd}")
        finally:
            self.db.cerrar()

    def obtener_planilla(self, id_clase: int, fecha: str) -> Optional[PlanillaAsistencia]:
        # --- BLINDAJE 0: Validación Defensiva ---
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha):
            print(f"Advertencia: Se intentó buscar con formato incorrecto ({fecha}).")
            return None

        conn = self.db.conectar()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            
            query = """
                SELECT A.ID_ESTUDIANTE, A.ESTADO, J.MOTIVO
                FROM TBL_ASISTENCIA A
                LEFT JOIN TBL_JUSTIFICACIONES J ON A.ID_ASISTENCIA = J.ID_ASISTENCIA
                WHERE A.ID_CLASE = ? AND A.FECHA = ?
            """
            cursor.execute(query, (id_clase, fecha))
            filas = cursor.fetchall()

            if not filas:
                return None 

            # Reconstruimos nuestro objeto de Dominio
            planilla = PlanillaAsistencia(id_clase=id_clase, fecha=fecha)
            
            for fila in filas:
                id_estudiante, estado_str, motivo = fila
                estado_enum = EstadoAsistencia(estado_str)
                
                registro = RegistroAsistencia(
                    id_estudiante=id_estudiante,
                    estado=estado_enum,
                    motivo_justificacion=motivo
                )
                planilla.registros.append(registro)

            return planilla
            
        except sqlite3.Error as error_bd:
            print(f"Error al obtener la planilla: {error_bd}")
            return None
        finally:
            self.db.cerrar()