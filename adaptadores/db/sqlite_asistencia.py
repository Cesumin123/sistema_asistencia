import sqlite3
from typing import Optional

# Importamos las entidades del dominio y el puerto que vamos a implementar
from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia
from puertos.repositorio_asistencia import PuertoRepositorioAsistencia

class RepositorioAsistenciaSQLite(PuertoRepositorioAsistencia):
    def __init__(self, db_conexion):
        """
        Inyección de dependencias: Recibimos la clase ConexionBD instanciada
        desde el main.py.
        """
        self.db = db_conexion

    def guardar_planilla(self, planilla: PlanillaAsistencia) -> None:
        conn = self.db.conectar()
        if not conn:
            raise ConnectionError("No se pudo conectar a la base de datos para guardar la asistencia.")

        try:
            cursor = conn.cursor()
            
            # --- BLINDAJE 1: Limpieza preventiva ---
            # Evitamos duplicados borrando los registros de esa misma clase y fecha.
            # Como se configuro 'PRAGMA foreign_keys = ON' y 'ON DELETE CASCADE' 
            # en la db_conexion.py, esto también borrará las justificaciones atadas.
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

                # Si es justificado, capturamos el ID recién creado e insertamos el motivo
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
            # Solo si todo el bucle for termina sin explotar, consolidamos los cambios.
            conn.commit()
            
        except sqlite3.Error as error_bd:
            conn.rollback() # Si algo falla, revertimos absolutamente todo
            raise Exception(f"Fallo crítico al guardar la asistencia: {error_bd}")
        finally:
            self.db.cerrar()

    def obtener_planilla(self, id_clase: int, fecha: str) -> Optional[PlanillaAsistencia]:
        """
        Recupera una planilla previamente guardada en la BD.
        """
        conn = self.db.conectar()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            
            # Usamos LEFT JOIN porque no todas las asistencias (A, P) tienen una
            # entrada en la tabla TBL_JUSTIFICACIONES.
            query = """
                SELECT A.ID_ESTUDIANTE, A.ESTADO, J.MOTIVO
                FROM TBL_ASISTENCIA A
                LEFT JOIN TBL_JUSTIFICACIONES J ON A.ID_ASISTENCIA = J.ID_ASISTENCIA
                WHERE A.ID_CLASE = ? AND A.FECHA = ?
            """
            cursor.execute(query, (id_clase, fecha))
            filas = cursor.fetchall()

            if not filas:
                return None # No se encontró asistencia guardada para esa fecha

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