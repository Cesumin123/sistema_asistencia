import sqlite3 
import os      
import sys

class ConexionBD:
    """
    Esta clase Maneja la conexión a la base de datos (Capa de Infraestructura).
    """
    
    def __init__(self):
        # Detectar si es .exe o .py para buscar la ruta correcta
        if getattr(sys, 'frozen', False):
            carpeta_actual = os.path.dirname(sys.executable)
        else:
            carpeta_actual = os.path.dirname(os.path.abspath(__file__))
        
        self.ruta_db = os.path.join(carpeta_actual, "sistema_escolar.db")

    def conectar(self):
        """Intenta abrir la conexión con la base de datos."""
        es_nueva = not os.path.exists(self.ruta_db)
        
        try:
            self.conexion = sqlite3.connect(self.ruta_db)
            self.conexion.execute("PRAGMA foreign_keys = ON")
            
            if es_nueva:
                self.crear_tablas_iniciales()
                
            return self.conexion
            
        except Exception as error:
            print(f"hubo un problema al conectar: {error}")
            return None

    def cerrar(self):
        """Cierra la conexión con la base de datos."""
        if hasattr(self, 'conexion'):
            self.conexion.close()

    def crear_tablas_iniciales(self):
        """Construye las tablas la primera vez que se ejecuta el programa."""
        cursor = self.conexion.cursor()
        
        # --- NUEVO: TABLA DE AUDITORÍA (El Gran Hermano) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_AUDITORIA (
                ID_AUDITORIA INTEGER PRIMARY KEY AUTOINCREMENT,
                FECHA_HORA TEXT,
                USUARIO TEXT,
                MODULO TEXT,
                ACCION TEXT,
                DETALLES TEXT
            )""")
        
        # --- ESTANTE 1: USUARIOS ---
        # Se agregó ESTADO_ACTIVO (1 = Activo, 0 = Eliminado)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_USUARIOS (
                ID_USUARIO INTEGER PRIMARY KEY AUTOINCREMENT,
                NOMBRE_COMPLETO TEXT,
                USERNAME TEXT UNIQUE,
                PASSWORD TEXT,
                ROL TEXT,
                ESTADO_ACTIVO INTEGER DEFAULT 1
            )""")
        cursor.execute("INSERT OR IGNORE INTO TBL_USUARIOS (USERNAME, PASSWORD, ROL) VALUES ('admin', '1234', 'ADMIN')")

        # --- ESTANTE 2: GRADOS Y SECCIONES ---
        cursor.execute("CREATE TABLE IF NOT EXISTS TBL_GRADOS (ID_GRADO INTEGER PRIMARY KEY, DESCRIPCION TEXT)")
        cursor.execute("INSERT OR IGNORE INTO TBL_GRADOS VALUES (1,'1er AÑO'),(2,'2do AÑO'),(3,'3er AÑO'),(4,'4to AÑO'),(5,'5to AÑO'),(6,'GRADUADO')")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS TBL_SECCIONES (ID_SECCION INTEGER PRIMARY KEY AUTOINCREMENT, DESCRIPCION TEXT UNIQUE)")
        cursor.execute("INSERT OR IGNORE INTO TBL_SECCIONES (DESCRIPCION) VALUES ('A'),('B'),('C'),('D'),('E')")

        # --- ESTANTE 3: PROFESORES ---
        # Se agregó ESTADO_ACTIVO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_PROFESORES (
                ID_PROFESOR INTEGER PRIMARY KEY AUTOINCREMENT,
                CEDULA TEXT UNIQUE,
                NOMBRE_COMPLETO TEXT,
                ESTADO_ACTIVO INTEGER DEFAULT 1
            )""")

        # --- ESTANTE 4: ESTUDIANTES ---
        # Se agregó ESTADO_ACTIVO
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_ESTUDIANTES (
                ID_ESTUDIANTE TEXT PRIMARY KEY,
                NOMBRE TEXT NOT NULL,
                FECHA_NACIMIENTO TEXT,
                REPRESENTANTE TEXT,
                TELEFONO TEXT,
                GENERO TEXT,
                ESCOLARIDAD TEXT,
                TURNO TEXT,
                CONDICION TEXT,
                ID_GRADO INTEGER,
                ID_SECCION INTEGER,
                ESTADO_ACTIVO INTEGER DEFAULT 1, 
                FOREIGN KEY(ID_GRADO) REFERENCES TBL_GRADOS(ID_GRADO),
                FOREIGN KEY(ID_SECCION) REFERENCES TBL_SECCIONES(ID_SECCION)
            )""")

        # --- ESTANTE 5: CLASES ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_CLASES (
                ID_CLASE INTEGER PRIMARY KEY AUTOINCREMENT,
                NOMBRE_MATERIA TEXT, ID_PROFESOR INTEGER, ID_GRADO INTEGER, ID_SECCION INTEGER,
                FOREIGN KEY(ID_PROFESOR) REFERENCES TBL_PROFESORES(ID_PROFESOR),
                FOREIGN KEY(ID_GRADO) REFERENCES TBL_GRADOS(ID_GRADO),
                FOREIGN KEY(ID_SECCION) REFERENCES TBL_SECCIONES(ID_SECCION)
            )""")

        # --- ESTANTE 6: ASISTENCIA ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_ASISTENCIA (
                ID_ASISTENCIA INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_CLASE INTEGER, ID_ESTUDIANTE TEXT, FECHA TEXT, ESTADO TEXT,
                FOREIGN KEY(ID_CLASE) REFERENCES TBL_CLASES(ID_CLASE) ON DELETE CASCADE,
                FOREIGN KEY(ID_ESTUDIANTE) REFERENCES TBL_ESTUDIANTES(ID_ESTUDIANTE) ON DELETE CASCADE ON UPDATE CASCADE
            )""")

        # --- ESTANTE 7: JUSTIFICACIONES ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_JUSTIFICACIONES (
                ID_JUSTIFICACION INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_ASISTENCIA INTEGER, MOTIVO TEXT,
                FOREIGN KEY(ID_ASISTENCIA) REFERENCES TBL_ASISTENCIA(ID_ASISTENCIA) ON DELETE CASCADE
            )""")
        
        self.conexion.commit()

if __name__ == "__main__":
    mi_base_de_datos = ConexionBD()
    conn = mi_base_de_datos.conectar()
    if conn:
        print("¡Excelente! La base de datos se creó y conectó correctamente con soporte para Auditoría.")
        mi_base_de_datos.cerrar()