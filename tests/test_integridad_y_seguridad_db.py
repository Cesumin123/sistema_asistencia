# tests/test_integridad_y_seguridad_db.py
"""
Pruebas de Integridad Referencial y Seguridad de Base de Datos (RNF-05 y RNF-06).

Cubre:
1. Verificación de activación obligatoria de PRAGMA foreign_keys = ON y PRAGMA journal_mode = WAL.
2. Integridad referencial estricta: rechazo de FK inexistente, ON DELETE CASCADE en cadena
   (TBL_CLASES -> TBL_ASISTENCIA -> TBL_JUSTIFICACIONES) y ON UPDATE CASCADE en TBL_ESTUDIANTES.
3. Restricción UNIQUE en TBL_JUSTIFICACIONES para ID_ASISTENCIA (prevención de justificaciones duplicadas).
4. Resistencia a inyecciones SQL mediante consultas parametrizadas en autenticación,
   búsquedas y listados.
"""

import sqlite3
import pytest

from db_conexion import ConexionBD
from dominio.usuario import Usuario
from dominio.estudiante import Estudiante
from adaptadores.db.sqlite_usuario import SQLiteRepositorioUsuario
from adaptadores.db.sqlite_estudiante import RepositorioEstudianteSQLite
from adaptadores.db.sqlite_listados import RepositorioListadosSQLite


@pytest.fixture
def bd_archivo_wal(tmp_path):
    """Crea una base de datos SQLite en disco temporal para comprobar WAL y foreign keys."""
    ruta_archivo = str(tmp_path / "test_seguridad.db")
    db = ConexionBD(ruta_db=ruta_archivo)
    yield db, ruta_archivo
    db.cerrar_definitivo()


@pytest.fixture
def bd_en_memoria():
    """Crea una base de datos en memoria con foreign keys activos para pruebas de integridad."""
    db = ConexionBD(ruta_db=":memory:")
    yield db
    db.cerrar_definitivo()


# =============================================================================
# 1. PRUEBA DE PRAGMAS OBLIGATORIOS (RNF-05)
# =============================================================================

def test_pragmas_foreign_keys_y_wal_activos(bd_archivo_wal):
    """
    RNF-05: Toda conexión persistente debe tener activados:
    PRAGMA foreign_keys = ON;
    PRAGMA journal_mode = WAL;
    """
    db, _ = bd_archivo_wal
    conn = db.conectar()
    cursor = conn.cursor()

    # Verificar foreign_keys activado
    cursor.execute("PRAGMA foreign_keys;")
    fk_status = cursor.fetchone()[0]
    assert fk_status == 1, "PRAGMA foreign_keys DEBE ser 1 (ON)."

    # Verificar journal_mode WAL
    cursor.execute("PRAGMA journal_mode;")
    journal_mode = cursor.fetchone()[0]
    assert str(journal_mode).upper() == "WAL", "PRAGMA journal_mode DEBE ser WAL en base de datos física."


# =============================================================================
# 2. PRUEBAS DE INTEGRIDAD REFERENCIAL Y RESTRICCIONES FK
# =============================================================================

def test_fk_rechazo_insercion_profesor_inexistente(bd_en_memoria):
    """No se puede crear una clase asignando un ID_PROFESOR que no existe en TBL_PROFESORES."""
    conn = bd_en_memoria.conectar()
    cursor = conn.cursor()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION)
            VALUES ('Matemáticas', 9999, 1, 1)
            """
        )
        conn.commit()


def test_fk_rechazo_asistencia_estudiante_inexistente(bd_en_memoria):
    """No se puede registrar asistencia de un ID_ESTUDIANTE no inscrito en TBL_ESTUDIANTES."""
    conn = bd_en_memoria.conectar()
    cursor = conn.cursor()

    # Crear profesor y clase válida primero
    cursor.execute("INSERT INTO TBL_PROFESORES (CEDULA, NOMBRE_COMPLETO) VALUES ('V-111', 'Profesor A')")
    id_prof = cursor.lastrowid
    cursor.execute("INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES ('Física', ?, 1, 1)", (id_prof,))
    id_clase = cursor.lastrowid
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO)
            VALUES (?, 'V-ESTUDIANTE-FANTASMA', '2026-11-24', 'P')
            """,
            (id_clase,)
        )
        conn.commit()


def test_on_delete_cascade_en_cadena(bd_en_memoria):
    """
    ON DELETE CASCADE:
    Al eliminar una clase de TBL_CLASES, deben eliminarse en cascada:
    TBL_CLASES -> TBL_ASISTENCIA -> TBL_JUSTIFICACIONES
    """
    conn = bd_en_memoria.conectar()
    cursor = conn.cursor()

    # 1. Crear profesor, estudiante y clase
    cursor.execute("INSERT INTO TBL_PROFESORES (CEDULA, NOMBRE_COMPLETO) VALUES ('V-222', 'Profesor Titular')")
    id_prof = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO TBL_ESTUDIANTES 
        (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO, ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION)
        VALUES ('V-990001', 'Estudiante Prueba', '2010-01-01', 'Rep', '0414', 'M', 'Regular', 'Mañana', 'Activo', 1, 1)
        """
    )

    cursor.execute("INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES ('Química', ?, 1, 1)", (id_prof,))
    id_clase = cursor.lastrowid

    # 2. Insertar asistencia y su correspondiente justificación
    cursor.execute(
        "INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (?, 'V-990001', '2026-11-24', 'J')",
        (id_clase,)
    )
    id_asistencia = cursor.lastrowid

    cursor.execute("INSERT INTO TBL_JUSTIFICACIONES (ID_ASISTENCIA, MOTIVO) VALUES (?, 'Reposo Médico')", (id_asistencia,))
    conn.commit()

    # Verificar que existen los registros
    cursor.execute("SELECT COUNT(*) FROM TBL_ASISTENCIA WHERE ID_CLASE = ?", (id_clase,))
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT COUNT(*) FROM TBL_JUSTIFICACIONES WHERE ID_ASISTENCIA = ?", (id_asistencia,))
    assert cursor.fetchone()[0] == 1

    # 3. Eliminar la clase: debe activar CASCADE
    cursor.execute("DELETE FROM TBL_CLASES WHERE ID_CLASE = ?", (id_clase,))
    conn.commit()

    # Verificar eliminación en cascada
    cursor.execute("SELECT COUNT(*) FROM TBL_ASISTENCIA WHERE ID_CLASE = ?", (id_clase,))
    assert cursor.fetchone()[0] == 0, "Las asistencias debieron borrarse en cascada."

    cursor.execute("SELECT COUNT(*) FROM TBL_JUSTIFICACIONES WHERE ID_ASISTENCIA = ?", (id_asistencia,))
    assert cursor.fetchone()[0] == 0, "Las justificaciones debieron borrarse en cascada tras la asistencia."


def test_on_update_cascade_estudiante(bd_en_memoria):
    """
    ON UPDATE CASCADE:
    Al modificar la cédula escolar (ID_ESTUDIANTE) en TBL_ESTUDIANTES,
    se debe propagar automáticamente a TBL_ASISTENCIA sin romper la integridad.
    """
    conn = bd_en_memoria.conectar()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO TBL_PROFESORES (CEDULA, NOMBRE_COMPLETO) VALUES ('V-333', 'Profesor C')")
    id_prof = cursor.lastrowid
    cursor.execute("INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES ('Biología', ?, 1, 1)", (id_prof,))
    id_clase = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO TBL_ESTUDIANTES 
        (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO, ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION)
        VALUES ('V-ORIGINAL', 'Alumno Cedula Original', '2010-01-01', 'Rep', '0414', 'M', 'Regular', 'Mañana', 'Activo', 1, 1)
        """
    )
    cursor.execute(
        "INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (?, 'V-ORIGINAL', '2026-11-24', 'P')",
        (id_clase,)
    )
    conn.commit()

    # Actualizar la clave primaria del estudiante
    cursor.execute("UPDATE TBL_ESTUDIANTES SET ID_ESTUDIANTE = 'V-ACTUALIZADA' WHERE ID_ESTUDIANTE = 'V-ORIGINAL'")
    conn.commit()

    # Verificar que en TBL_ASISTENCIA se propagó la nueva cédula
    cursor.execute("SELECT ID_ESTUDIANTE FROM TBL_ASISTENCIA WHERE ID_CLASE = ?", (id_clase,))
    fila = cursor.fetchone()
    assert fila[0] == "V-ACTUALIZADA", "ON UPDATE CASCADE debió actualizar la clave foránea en TBL_ASISTENCIA."


def test_tbl_justificaciones_rechazo_duplicados_unique(bd_en_memoria):
    """TBL_JUSTIFICACIONES tiene restricción UNIQUE en ID_ASISTENCIA."""
    conn = bd_en_memoria.conectar()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO TBL_PROFESORES (CEDULA, NOMBRE_COMPLETO) VALUES ('V-444', 'Profesor D')")
    id_prof = cursor.lastrowid
    cursor.execute("INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES ('Inglés', ?, 1, 1)", (id_prof,))
    id_clase = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO TBL_ESTUDIANTES 
        (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO, ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION)
        VALUES ('V-ALUMNO-J', 'Alumno Justificado', '2010-01-01', 'Rep', '0414', 'F', 'Regular', 'Mañana', 'Activo', 1, 1)
        """
    )
    cursor.execute(
        "INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (?, 'V-ALUMNO-J', '2026-11-24', 'J')",
        (id_clase,)
    )
    id_asistencia = cursor.lastrowid

    cursor.execute("INSERT INTO TBL_JUSTIFICACIONES (ID_ASISTENCIA, MOTIVO) VALUES (?, 'Motivo 1')", (id_asistencia,))
    conn.commit()

    # Intentar registrar una segunda justificación sobre la misma asistencia debe fallar
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO TBL_JUSTIFICACIONES (ID_ASISTENCIA, MOTIVO) VALUES (?, 'Motivo 2')", (id_asistencia,))
        conn.commit()


# =============================================================================
# 3. PRUEBAS DE RESISTENCIA A INYECCIÓN SQL (SQL INJECTION)
# =============================================================================

PAYLOADS_SQL_INJECTION = [
    "' OR '1'='1",
    "admin' --",
    "'; DROP TABLE TBL_ESTUDIANTES; --",
    "' UNION SELECT 1, 'hacker', 'hacker', 'ADMIN', 1 --",
    "1' OR 1=1; --",
]


@pytest.mark.parametrize("payload", PAYLOADS_SQL_INJECTION)
def test_seguridad_inyeccion_sql_en_login(bd_en_memoria, payload):
    """
    Las consultas parametrizadas deben neutralizar cualquier intento de SQL Injection
    en la autenticación, retornando None y manteniendo la integridad de las tablas.
    """
    repo_usuario = SQLiteRepositorioUsuario(bd_en_memoria)

    # Intento con payload en username
    resultado = repo_usuario.autenticar(username=payload, password_plano="1234")
    assert resultado is None, f"El payload '{payload}' no debe autenticar como usuario legítimo."

    # Intento con payload en password
    resultado2 = repo_usuario.autenticar(username="admin", password_plano=payload)
    assert resultado2 is None, f"El payload '{payload}' en la contraseña no debe conceder acceso."


@pytest.mark.parametrize("payload", PAYLOADS_SQL_INJECTION)
def test_seguridad_inyeccion_sql_en_busqueda_estudiante(bd_en_memoria, payload):
    """
    Búsqueda de estudiante con payloads maliciosos no debe alterar la base de datos
    ni provocar errores de sintaxis SQL.
    """
    repo_est = RepositorioEstudianteSQLite(bd_en_memoria)

    # Insertar un estudiante legítimo para comprobar persistencia
    est = Estudiante(
        cedula="V-55555",
        nombre="ALUMNO PROTEGIDO",
        fecha_nacimiento="01/01/2009",
        representante="Rep",
        telefono="0414",
        genero="M",
        escolaridad="Regular",
        turno="Mañana",
        condicion="Activo",
        id_grado=1,
        id_seccion=1
    )
    repo_est.guardar(est)

    # Intentar búsqueda con inyección
    resultado = repo_est.obtener_por_cedula(payload)
    assert resultado is None, "La búsqueda con payload no debe devolver datos espurios."

    # Verificar que la tabla TBL_ESTUDIANTES permanece íntegra
    conn = bd_en_memoria.conectar()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM TBL_ESTUDIANTES")
    assert cur.fetchone()[0] == 1, "La tabla TBL_ESTUDIANTES no debe haber sido alterada."
