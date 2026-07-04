import sqlite3
from typing import List, Optional
from dominio.estudiante import Estudiante
from puertos.repositorio_estudiante import PuertoRepositorioEstudiante
from db_conexion import ConexionBD

class RepositorioEstudianteSQLite(PuertoRepositorioEstudiante):
    """
    Adaptador concreto para manejar la tabla TBL_ESTUDIANTES en SQLite.
    Cumple estrictamente con el contrato definido en el Puerto.
    """
    
    def __init__(self, db: ConexionBD):
        # Inyección de dependencias: recibimos la clase manejadora de la BD
        self.db = db

    def guardar(self, estudiante: Estudiante) -> bool:
        """Inserta un nuevo estudiante en la base de datos."""
        conn = self.db.conectar()
        if not conn: return False
        
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO TBL_ESTUDIANTES 
                (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO, 
                 ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION, ESTADO_ACTIVO) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            valores = (
                estudiante.cedula, estudiante.nombre, estudiante.fecha_nacimiento, 
                estudiante.representante, estudiante.telefono, estudiante.genero,
                estudiante.escolaridad, estudiante.turno, estudiante.condicion,
                estudiante.id_grado, estudiante.id_seccion, estudiante.estado_activo
            )
            cursor.execute(sql, valores)
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error de integridad (Cédula duplicada): {e}")
            return False
        except Exception as e:
            print(f"Error al guardar estudiante: {e}")
            return False
        finally:
            self.db.cerrar()

    def actualizar(self, estudiante: Estudiante) -> bool:
        """Actualiza la información de un estudiante existente."""
        conn = self.db.conectar()
        if not conn: return False
        
        try:
            cursor = conn.cursor()
            sql = """
                UPDATE TBL_ESTUDIANTES SET 
                NOMBRE=?, FECHA_NACIMIENTO=?, REPRESENTANTE=?, TELEFONO=?, GENERO=?, 
                ESCOLARIDAD=?, TURNO=?, CONDICION=?, ID_GRADO=?, ID_SECCION=?, ESTADO_ACTIVO=?
                WHERE ID_ESTUDIANTE=?
            """
            valores = (
                estudiante.nombre, estudiante.fecha_nacimiento, estudiante.representante, 
                estudiante.telefono, estudiante.genero, estudiante.escolaridad, 
                estudiante.turno, estudiante.condicion, estudiante.id_grado, 
                estudiante.id_seccion, estudiante.estado_activo, estudiante.cedula
            )
            cursor.execute(sql, valores)
            conn.commit()
            return cursor.rowcount > 0 # Devuelve True si realmente se modificó alguna fila
        except Exception as e:
            print(f"Error al actualizar estudiante: {e}")
            return False
        finally:
            self.db.cerrar()

    def eliminar(self, cedula: str) -> bool:
        """
        Realiza un borrado lógico (Soft Delete).
        Cambia ESTADO_ACTIVO a 0 en lugar de eliminar el registro.
        """
        conn = self.db.conectar()
        if not conn: return False
        
        try:
            cursor = conn.cursor()
            sql = "UPDATE TBL_ESTUDIANTES SET ESTADO_ACTIVO = 0 WHERE ID_ESTUDIANTE = ?"
            cursor.execute(sql, (cedula,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al eliminar (lógico) estudiante: {e}")
            return False
        finally:
            self.db.cerrar()

    def obtener_por_cedula(self, cedula: str) -> Optional[Estudiante]:
        """Busca un estudiante específico si está activo."""
        conn = self.db.conectar()
        if not conn: return None
        
        try:
            cursor = conn.cursor()
            sql = "SELECT * FROM TBL_ESTUDIANTES WHERE ID_ESTUDIANTE = ? AND ESTADO_ACTIVO = 1"
            cursor.execute(sql, (cedula,))
            fila = cursor.fetchone()
            
            if fila:
                return Estudiante(
                    cedula=fila[0], nombre=fila[1], fecha_nacimiento=fila[2],
                    representante=fila[3], telefono=fila[4], genero=fila[5],
                    escolaridad=fila[6], turno=fila[7], condicion=fila[8],
                    id_grado=fila[9], id_seccion=fila[10], estado_activo=fila[11]
                )
            return None
        except Exception as e:
            print(f"Error al buscar estudiante: {e}")
            return None
        finally:
            self.db.cerrar()

    def obtener_todos_activos(self) -> List[Estudiante]:
        """Devuelve una lista de todos los estudiantes que no han sido eliminados."""
        conn = self.db.conectar()
        if not conn: return []
        
        estudiantes = []
        try:
            cursor = conn.cursor()
            sql = "SELECT * FROM TBL_ESTUDIANTES WHERE ESTADO_ACTIVO = 1 ORDER BY NOMBRE ASC"
            cursor.execute(sql)
            
            for fila in cursor.fetchall():
                estudiantes.append(Estudiante(
                    cedula=fila[0], nombre=fila[1], fecha_nacimiento=fila[2],
                    representante=fila[3], telefono=fila[4], genero=fila[5],
                    escolaridad=fila[6], turno=fila[7], condicion=fila[8],
                    id_grado=fila[9], id_seccion=fila[10], estado_activo=fila[11]
                ))
            return estudiantes
        except Exception as e:
            print(f"Error al obtener estudiantes: {e}")
            return []
        finally:
            self.db.cerrar()