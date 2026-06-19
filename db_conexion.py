import sqlite3 # Importa la librería estándar de Python para trabajar con bases de datos SQLite.
import os      # Importa la librería para interactuar con el sistema operativo (como buscar y crear rutas de archivos).
import sys     # Importa la librería que permite obtener información sobre cómo se está ejecutando el programa.

class ConexionBD:
    """
    Clase encargada de gestionar la conexión a la base de datos del sistema escolar.
    Contiene los métodos para conectar, desconectar y crear las tablas necesarias si no existen.
    """
    
    def __init__(self):
        # DETECTAR LA RUTA DEL ARCHIVO DE LA BASE DE DATOS
        # getattr(sys, 'frozen', False) verifica si el programa se está ejecutando como un archivo compilado (.exe).
        if getattr(sys, 'frozen', False):
            # Si es un .exe, obtiene la ruta de la carpeta donde se encuentra el ejecutable.
            carpeta_actual = os.path.dirname(sys.executable)
        else:
            # Si se está ejecutando como un script de Python (.py), obtiene la ruta de la carpeta de este archivo.
            carpeta_actual = os.path.dirname(os.path.abspath(__file__))
        
        # os.path.join une la ruta de la carpeta con el nombre del archivo de la base de datos.
        # Esto crea la ruta completa, por ejemplo: C:/Proyectos/Asistencia/sistema_escolar.db
        self.ruta_db = os.path.join(carpeta_actual, "sistema_escolar.db")

    def conectar(self):
        """
        Inicia la conexión con el archivo de la base de datos.
        Retorna el objeto de conexión si tiene éxito, o None si ocurre un error.
        """
        # Comprueba si el archivo de la base de datos ya existe en la computadora.
        es_nueva = not os.path.exists(self.ruta_db)
        
        try:
            # Conecta el programa con el archivo SQLite. Si no existe, SQLite lo crea en blanco automáticamente.
            self.conexion = sqlite3.connect(self.ruta_db)
            
            # Activa el soporte para "Claves Foráneas" (Foreign Keys). 
            # Esto obliga a la base de datos a respetar las relaciones entre tablas (ej. no borrar un grado si tiene alumnos).
            self.conexion.execute("PRAGMA foreign_keys = ON")
            
            # Si detectamos arriba que el archivo no existía, llamamos a la función que crea las tablas.
            if es_nueva:
                self.crear_tablas_iniciales()
                
            return self.conexion
            
        except Exception as error:
            # Si ocurre un error (por ejemplo, falta de permisos en la carpeta), se imprime en consola.
            print(f"Error al conectar con la base de datos: {error}")
            return None

    def cerrar(self):
        """
        Cierra la conexión con la base de datos para liberar memoria y evitar bloqueos de archivos.
        """
        # Verifica si la variable 'conexion' existe dentro de la clase antes de intentar cerrarla.
        if hasattr(self, 'conexion'):
            self.conexion.close()

    def crear_tablas_iniciales(self):
        """
        Ejecuta las instrucciones SQL para crear las tablas necesarias para que el sistema funcione.
        Solo se ejecuta la primera vez que se crea la base de datos.
        """
        # El cursor es el objeto que nos permite enviar y ejecutar comandos SQL dentro de la base de datos.
        cursor = self.conexion.cursor()
        
        # --- TABLA DE USUARIOS ---
        # Guarda a las personas que pueden iniciar sesión en el programa.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_USUARIOS (
                ID_USUARIO INTEGER PRIMARY KEY AUTOINCREMENT, -- Número de identificación único que aumenta solo.
                NOMBRE_COMPLETO TEXT,                         -- Nombre real del usuario.
                USERNAME TEXT UNIQUE,                         -- Nombre de usuario para iniciar sesión (no se puede repetir).
                PASSWORD TEXT,                                -- Contraseña.
                ROL TEXT,                                     -- Nivel de acceso (ej. ADMIN).
                ESTADO TEXT DEFAULT 'ACTIVO'                  -- Para el borrado lógico. Valor por defecto: 'ACTIVO'.
            )""")
        
        # Inserta el primer usuario administrador para poder entrar al sistema la primera vez.
        # INSERT OR IGNORE evita que dé error si el usuario ya existe.
        cursor.execute("INSERT OR IGNORE INTO TBL_USUARIOS (USERNAME, PASSWORD, ROL, ESTADO) VALUES ('admin', '1234', 'ADMIN', 'ACTIVO')")

        # --- TABLAS DE GRADOS Y SECCIONES ---
        # Guardan los años escolares y las letras de cada salón.
        cursor.execute("CREATE TABLE IF NOT EXISTS TBL_GRADOS (ID_GRADO INTEGER PRIMARY KEY, DESCRIPCION TEXT)")
        cursor.execute("INSERT OR IGNORE INTO TBL_GRADOS VALUES (1,'1er AÑO'),(2,'2do AÑO'),(3,'3er AÑO'),(4,'4to AÑO'),(5,'5to AÑO'),(6,'GRADUADO')")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS TBL_SECCIONES (ID_SECCION INTEGER PRIMARY KEY AUTOINCREMENT, DESCRIPCION TEXT UNIQUE)")
        cursor.execute("INSERT OR IGNORE INTO TBL_SECCIONES (DESCRIPCION) VALUES ('A'),('B'),('C'),('D'),('E')")

        # --- TABLA DE PROFESORES ---
        # Guarda la información de los docentes.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_PROFESORES (
                ID_PROFESOR INTEGER PRIMARY KEY AUTOINCREMENT, -- Número de identificación único.
                CEDULA TEXT UNIQUE,                            -- Documento de identidad (no se puede repetir).
                NOMBRE_COMPLETO TEXT,                          -- Nombre del profesor.
                ESTADO TEXT DEFAULT 'ACTIVO'                   -- Para el borrado lógico. Valor por defecto: 'ACTIVO'.
            )""")

        # --- TABLA DE ESTUDIANTES ---
        # Guarda la información personal y académica de los alumnos.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_ESTUDIANTES (
                ID_ESTUDIANTE TEXT PRIMARY KEY, -- Usamos la cédula o identificador escolar como clave principal.
                NOMBRE TEXT NOT NULL,           -- El nombre no puede quedar en blanco (NOT NULL).
                FECHA_NACIMIENTO TEXT,
                REPRESENTANTE TEXT,
                TELEFONO TEXT,
                GENERO TEXT,
                ESCOLARIDAD TEXT,               -- Indica si es Regular o Repitiente.
                TURNO TEXT,                     -- Indica si estudia en la Mañana o Tarde.
                CONDICION TEXT,                 -- Indica si está Activo, Retirado, etc.
                ID_GRADO INTEGER,               -- Se relaciona con TBL_GRADOS.
                ID_SECCION INTEGER,             -- Se relaciona con TBL_SECCIONES.
                FOREIGN KEY(ID_GRADO) REFERENCES TBL_GRADOS(ID_GRADO),
                FOREIGN KEY(ID_SECCION) REFERENCES TBL_SECCIONES(ID_SECCION)
            )""")

        # --- TABLA DE CLASES ---
        # Relaciona a un profesor con una materia, un grado y una sección específica.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_CLASES (
                ID_CLASE INTEGER PRIMARY KEY AUTOINCREMENT,
                NOMBRE_MATERIA TEXT, 
                ID_PROFESOR INTEGER, 
                ID_GRADO INTEGER, 
                ID_SECCION INTEGER,
                FOREIGN KEY(ID_PROFESOR) REFERENCES TBL_PROFESORES(ID_PROFESOR),
                FOREIGN KEY(ID_GRADO) REFERENCES TBL_GRADOS(ID_GRADO),
                FOREIGN KEY(ID_SECCION) REFERENCES TBL_SECCIONES(ID_SECCION)
            )""")

        # --- TABLA DE ASISTENCIA ---
        # Registra si un estudiante asistió, faltó o llegó tarde a una clase específica en una fecha.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_ASISTENCIA (
                ID_ASISTENCIA INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_CLASE INTEGER, 
                ID_ESTUDIANTE TEXT, 
                FECHA TEXT, 
                ESTADO TEXT,
                -- Si se borra una clase, se borran sus asistencias (ON DELETE CASCADE)
                FOREIGN KEY(ID_CLASE) REFERENCES TBL_CLASES(ID_CLASE) ON DELETE CASCADE,
                -- Si se borra o actualiza un estudiante, se actualizan sus asistencias
                FOREIGN KEY(ID_ESTUDIANTE) REFERENCES TBL_ESTUDIANTES(ID_ESTUDIANTE) ON DELETE CASCADE ON UPDATE CASCADE
            )""")

        # --- TABLA DE JUSTIFICACIONES ---
        # Guarda el motivo por el cual un estudiante faltó (soporte médico, permiso, etc).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TBL_JUSTIFICACIONES (
                ID_JUSTIFICACION INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_ASISTENCIA INTEGER, 
                MOTIVO TEXT,
                FOREIGN KEY(ID_ASISTENCIA) REFERENCES TBL_ASISTENCIA(ID_ASISTENCIA) ON DELETE CASCADE
            )""")
        
        # Confirma y guarda permanentemente todos los cambios estructurales hechos por el cursor.
        self.conexion.commit()

# Bloque de prueba.
# Este código solo se ejecuta si corres este archivo directamente, no si lo importas desde otro archivo.
if __name__ == "__main__":
    mi_base_de_datos = ConexionBD()          # Crea una instancia de la clase.
    conn = mi_base_de_datos.conectar()       # Intenta conectar y crear las tablas.
    if conn:
        print("Operación exitosa: La base de datos y sus tablas están listas.")
        mi_base_de_datos.cerrar()            # Cierra la conexión al terminar la prueba.