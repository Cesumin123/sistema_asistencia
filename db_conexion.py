import sqlite3 # Importamos la herramienta para manejar bases de datos (el archivador)
import os      # Importamos una herramienta para encontrar rutas en la computadora (el mapa)
import sys

class ConexionBD:
    """
    Esta clase es como el CONSERJE de la escuela.
    Su trabajo es abrir la puerta del cuarto de archivos (Base de Datos)
    y cerrarla cuando terminamos para que todo esté seguro.
    """
    
    def __init__(self):
    
        # DETECTAR SI ESTAMOS EN MODO EJECUTABLE (.EXE) O MODO CÓDIGO (.PY)
        if getattr(sys, 'frozen', False):
            # Si es un .exe, la carpeta es donde está el archivo ejecutable
            carpeta_actual = os.path.dirname(sys.executable)
        else:
            # Si es código normal, la carpeta es donde está este archivo
            carpeta_actual = os.path.dirname(os.path.abspath(__file__))
        
        # Unimos la ruta con el nombre del archivo
        self.ruta_db = os.path.join(carpeta_actual, "sistema_escolar.db")

    def conectar(self):
        """
        Esta función es la LLAVE. 
        Intenta abrir la conexión con la base de datos.
        """
        # Preguntamos: ¿El archivo ya existe o es nuevo?
        es_nueva = not os.path.exists(self.ruta_db)
        
        try:
            # ¡Clic! Giramos la llave y abrimos la conexión
            self.conexion = sqlite3.connect(self.ruta_db)
            
            # Le decimos a la base de datos que respete las reglas de familia
            # (Por ejemplo: No puedes tener un hijo (Nota) sin un padre (Alumno))
            self.conexion.execute("PRAGMA foreign_keys = ON")
            
            # Si la base de datos es nueva, llamamos a los constructores para armar los estantes (tablas)
            if es_nueva:
                self.crear_tablas_iniciales()
                
            return self.conexion
            
        except Exception as error:
            # Si algo sale mal (se rompió la llave), avisamos aquí
            print(f"Uy, hubo un problema al conectar: {error}")
            return None

    def cerrar(self):
        """
        Esta función cierra la puerta. 
        Siempre hay que cerrar al salir para no dejar datos volando.
        """
        if hasattr(self, 'conexion'):
            self.conexion.close()

    def crear_tablas_iniciales(self):
        """
        Esta función es el CARPINTERO.
        Si la base de datos está vacía, construye las tablas (los estantes)
        para que podamos guardar la información ordenada.
        """
        cursor = self.conexion.cursor()
        
        # --- ESTANTE 1: USUARIOS (Para los que pueden entrar al sistema) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_USUARIOS (
                ID_USUARIO INTEGER PRIMARY KEY AUTOINCREMENT,
                NOMBRE_COMPLETO TEXT,
                USERNAME TEXT UNIQUE, -- El usuario no se puede repetir
                PASSWORD TEXT,
                ROL TEXT
            )""")
        # Creamos al primer usuario "admin" para no quedarnos fuera
        cursor.execute("INSERT OR IGNORE INTO TBL_USUARIOS (USERNAME, PASSWORD, ROL) VALUES ('admin', '1234', 'ADMIN')")

        # --- ESTANTE 2: GRADOS Y SECCIONES (Los salones) ---
        cursor.execute("CREATE TABLE IF NOT EXISTS TBL_GRADOS (ID_GRADO INTEGER PRIMARY KEY, DESCRIPCION TEXT)")
        cursor.execute("INSERT OR IGNORE INTO TBL_GRADOS VALUES (1,'1er AÑO'),(2,'2do AÑO'),(3,'3er AÑO'),(4,'4to AÑO'),(5,'5to AÑO'),(6,'GRADUADO')")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS TBL_SECCIONES (ID_SECCION INTEGER PRIMARY KEY AUTOINCREMENT, DESCRIPCION TEXT UNIQUE)")
        cursor.execute("INSERT OR IGNORE INTO TBL_SECCIONES (DESCRIPCION) VALUES ('A'),('B'),('C'),('D'),('E')")

        # --- ESTANTE 3: PROFESORES (Los maestros) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_PROFESORES (
                ID_PROFESOR INTEGER PRIMARY KEY AUTOINCREMENT,
                CEDULA TEXT UNIQUE,
                NOMBRE_COMPLETO TEXT
            )""")

        # --- ESTANTE 4: ESTUDIANTES (La tabla más importante) ---
        # Aquí guardamos toda la info de los alumnos, incluyendo los nuevos campos:
        # Escolaridad (si repite), Turno (mañana/tarde) y Condición (activo).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_ESTUDIANTES (
                ID_ESTUDIANTE TEXT PRIMARY KEY, -- La Cédula es única
                NOMBRE TEXT NOT NULL,
                FECHA_NACIMIENTO TEXT,
                REPRESENTANTE TEXT,
                TELEFONO TEXT,
                GENERO TEXT,
                ESCOLARIDAD TEXT, -- Nuevo: ¿Regular o Repitiente?
                TURNO TEXT,       -- Nuevo: ¿Mañana o Tarde?
                CONDICION TEXT,   -- Nuevo: ¿Activo o Preinscrito?
                ID_GRADO INTEGER,
                ID_SECCION INTEGER,
                -- Estas líneas conectan al alumno con su salón y grado
                FOREIGN KEY(ID_GRADO) REFERENCES TBL_GRADOS(ID_GRADO),
                FOREIGN KEY(ID_SECCION) REFERENCES TBL_SECCIONES(ID_SECCION)
            )""")

        # --- ESTANTE 5: CLASES (Las materias) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_CLASES (
                ID_CLASE INTEGER PRIMARY KEY AUTOINCREMENT,
                NOMBRE_MATERIA TEXT, ID_PROFESOR INTEGER, ID_GRADO INTEGER, ID_SECCION INTEGER,
                FOREIGN KEY(ID_PROFESOR) REFERENCES TBL_PROFESORES(ID_PROFESOR),
                FOREIGN KEY(ID_GRADO) REFERENCES TBL_GRADOS(ID_GRADO),
                FOREIGN KEY(ID_SECCION) REFERENCES TBL_SECCIONES(ID_SECCION)
            )""")

        # --- ESTANTE 6: ASISTENCIA (Pasar la lista) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_ASISTENCIA (
                ID_ASISTENCIA INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_CLASE INTEGER, ID_ESTUDIANTE TEXT, FECHA TEXT, ESTADO TEXT,
                FOREIGN KEY(ID_CLASE) REFERENCES TBL_CLASES(ID_CLASE) ON DELETE CASCADE,
                FOREIGN KEY(ID_ESTUDIANTE) REFERENCES TBL_ESTUDIANTES(ID_ESTUDIANTE) ON DELETE CASCADE ON UPDATE CASCADE
            )""")

        # --- ESTANTE 7: JUSTIFICACIONES (Las excusas médicas) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_JUSTIFICACIONES (
                ID_JUSTIFICACION INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_ASISTENCIA INTEGER, MOTIVO TEXT,
                FOREIGN KEY(ID_ASISTENCIA) REFERENCES TBL_ASISTENCIA(ID_ASISTENCIA) ON DELETE CASCADE
            )""")
        
        # Guardamos todos los cambios (como darle a "Guardar" en Word)
        self.conexion.commit()

# Esta parte es para probar si el archivo funciona solo
if __name__ == "__main__":
    mi_base_de_datos = ConexionBD()
    conn = mi_base_de_datos.conectar()
    if conn:
        print("¡Excelente! La base de datos se creó y conectó correctamente.")
        mi_base_de_datos.cerrar()
