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
        """Inserta un nuevo estudiante en la base de datos con los campos de FASE A."""
        conn = self.db.conectar()
        if not conn: return False
        
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO TBL_ESTUDIANTES 
                (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO, 
                 ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION, ESTADO_ACTIVO,
                 NOMBRE_MADRE, TELEFONO_MADRE, NOMBRE_PADRE, TELEFONO_PADRE, FOTO_PATH) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            valores = (
                estudiante.cedula, estudiante.nombre, estudiante.fecha_nacimiento, 
                estudiante.representante, estudiante.telefono, estudiante.genero,
                estudiante.escolaridad, estudiante.turno, estudiante.condicion,
                estudiante.id_grado, estudiante.id_seccion, estudiante.estado_activo,
                estudiante.nombre_madre, estudiante.telefono_madre,
                estudiante.nombre_padre, estudiante.telefono_padre,
                estudiante.foto_path
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
                ESCOLARIDAD=?, TURNO=?, CONDICION=?, ID_GRADO=?, ID_SECCION=?, ESTADO_ACTIVO=?,
                NOMBRE_MADRE=?, TELEFONO_MADRE=?, NOMBRE_PADRE=?, TELEFONO_PADRE=?, FOTO_PATH=?
                WHERE ID_ESTUDIANTE=?
            """
            valores = (
                estudiante.nombre, estudiante.fecha_nacimiento, estudiante.representante, 
                estudiante.telefono, estudiante.genero, estudiante.escolaridad, 
                estudiante.turno, estudiante.condicion, estudiante.id_grado, 
                estudiante.id_seccion, estudiante.estado_activo,
                estudiante.nombre_madre, estudiante.telefono_madre,
                estudiante.nombre_padre, estudiante.telefono_padre,
                estudiante.foto_path,
                estudiante.cedula
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

    def _mapear_fila(self, fila) -> Estudiante:
        """Mapeo defensivo para reconstruir Estudiante tolerando esquemas previos o NULLs."""
        return Estudiante(
            cedula=fila[0] or "",
            nombre=fila[1] or "",
            fecha_nacimiento=fila[2] or "",
            representante=fila[3] or "",
            telefono=fila[4] or "",
            genero=fila[5] or "M",
            escolaridad=fila[6] or "Regular",
            turno=fila[7] or "Mañana",
            condicion=fila[8] or "Activo",
            id_grado=fila[9] if fila[9] is not None else 1,
            id_seccion=fila[10] if fila[10] is not None else 1,
            estado_activo=fila[11] if fila[11] is not None else 1,
            nombre_madre=fila[12] if len(fila) > 12 and fila[12] is not None else "",
            telefono_madre=fila[13] if len(fila) > 13 and fila[13] is not None else "",
            nombre_padre=fila[14] if len(fila) > 14 and fila[14] is not None else "",
            telefono_padre=fila[15] if len(fila) > 15 and fila[15] is not None else "",
            foto_path=fila[16] if len(fila) > 16 and fila[16] is not None else ""
        )

    def obtener_por_cedula(self, cedula: str) -> Optional[Estudiante]:
        """Busca un estudiante específico si está activo."""
        conn = self.db.conectar()
        if not conn: return None
        
        try:
            cursor = conn.cursor()
            sql = """
                SELECT ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO,
                       ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION, ESTADO_ACTIVO,
                       NOMBRE_MADRE, TELEFONO_MADRE, NOMBRE_PADRE, TELEFONO_PADRE, FOTO_PATH 
                FROM TBL_ESTUDIANTES 
                WHERE ID_ESTUDIANTE = ? AND ESTADO_ACTIVO = 1
            """
            cursor.execute(sql, (cedula,))
            fila = cursor.fetchone()
            
            if fila:
                return self._mapear_fila(fila)
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
            sql = """
                SELECT ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO,
                       ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION, ESTADO_ACTIVO,
                       NOMBRE_MADRE, TELEFONO_MADRE, NOMBRE_PADRE, TELEFONO_PADRE, FOTO_PATH 
                FROM TBL_ESTUDIANTES 
                WHERE ESTADO_ACTIVO = 1 
                ORDER BY NOMBRE ASC
            """
            cursor.execute(sql)
            
            for fila in cursor.fetchall():
                estudiantes.append(self._mapear_fila(fila))
            return estudiantes
        except Exception as e:
            print(f"Error al obtener estudiantes: {e}")
            return []
        finally:
            self.db.cerrar()

    def obtener_secciones(self) -> list:
        """Devuelve la lista de secciones registradas en TBL_SECCIONES."""
        conn = self.db.conectar()
        if not conn:
            return [(i, chr(64 + i)) for i in range(1, 27)]
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ID_SECCION, DESCRIPCION FROM TBL_SECCIONES ORDER BY ID_SECCION")
            return cursor.fetchall()
        except Exception:
            return [(i, chr(64 + i)) for i in range(1, 27)]
        finally:
            self.db.cerrar()