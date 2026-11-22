# tests/test_sqlite_asistencia.py
import pytest
from db_conexion import ConexionBD
from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia
from adaptadores.db.sqlite_asistencia import RepositorioAsistenciaSQLite

@pytest.fixture
def repo_asistencia():
    """Inicializa una base de datos en memoria con esquema y datos requeridos por las FKs."""
    db = ConexionBD(ruta_db=":memory:")
    conn = db.conectar()
    cursor = conn.cursor()
    
    # 1. Insertar profesor
    cursor.execute("INSERT INTO TBL_PROFESORES (ID_PROFESOR, CEDULA, NOMBRE_COMPLETO) VALUES (1, 'V-1000', 'Profesor Prueba')")
    
    # 2. Insertar clase (Materia en 4to Año 'A')
    cursor.execute("INSERT INTO TBL_CLASES (ID_CLASE, NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES (1, 'Matemáticas', 1, 4, 1)")
    
    # 3. Insertar estudiantes
    cursor.execute("""
        INSERT INTO TBL_ESTUDIANTES 
        (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO, ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION)
        VALUES 
        ('V-101', 'Alumno Uno', '2008-01-01', 'Rep Uno', '0414', 'M', 'Regular', 'Mañana', 'Activo', 4, 1),
        ('V-102', 'Alumno Dos', '2008-02-02', 'Rep Dos', '0414', 'F', 'Regular', 'Mañana', 'Activo', 4, 1)
    """)
    conn.commit()
    
    repo = RepositorioAsistenciaSQLite(db)
    yield repo, db
    
    db.cerrar_definitivo()

def test_guardar_y_obtener_planilla(repo_asistencia):
    """Verifica el guardado y recuperación íntegra de una planilla de asistencia."""
    repo, db = repo_asistencia
    
    reg1 = RegistroAsistencia(id_estudiante="V-101", estado=EstadoAsistencia.PRESENTE)
    reg2 = RegistroAsistencia(id_estudiante="V-102", estado=EstadoAsistencia.JUSTIFICADO, motivo_justificacion="Fiebre alta")
    planilla = PlanillaAsistencia(id_clase=1, fecha="2026-11-21", registros=[reg1, reg2])
    
    repo.guardar_planilla(planilla)
    
    recuperada = repo.obtener_planilla(id_clase=1, fecha="2026-11-21")
    assert recuperada is not None
    assert recuperada.id_clase == 1
    assert recuperada.fecha == "2026-11-21"
    assert len(recuperada.registros) == 2
    
    mapa_estados = {r.id_estudiante: r for r in recuperada.registros}
    assert mapa_estados["V-101"].estado == EstadoAsistencia.PRESENTE
    assert mapa_estados["V-101"].motivo_justificacion is None
    assert mapa_estados["V-102"].estado == EstadoAsistencia.JUSTIFICADO
    assert mapa_estados["V-102"].motivo_justificacion == "Fiebre alta"

def test_guardado_atomico_sobrescritura_sin_duplicados(repo_asistencia):
    """
    Verifica que al guardar nuevamente la misma clase y fecha:
    1. Se eliminen los registros previos.
    2. No queden registros huérfanos o duplicados en TBL_ASISTENCIA ni en TBL_JUSTIFICACIONES.
    """
    repo, db = repo_asistencia
    
    # Primer guardado: V-101 Presente, V-102 Ausente
    p1 = PlanillaAsistencia(id_clase=1, fecha="2026-11-21", registros=[
        RegistroAsistencia("V-101", EstadoAsistencia.PRESENTE),
        RegistroAsistencia("V-102", EstadoAsistencia.AUSENTE)
    ])
    repo.guardar_planilla(p1)
    
    conn = db.conectar()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM TBL_ASISTENCIA WHERE ID_CLASE = 1 AND FECHA = '2026-11-21'")
    assert cur.fetchone()[0] == 2
    
    # Segundo guardado (corrección): V-101 Ausente, V-102 Justificado
    p2 = PlanillaAsistencia(id_clase=1, fecha="2026-11-21", registros=[
        RegistroAsistencia("V-101", EstadoAsistencia.AUSENTE),
        RegistroAsistencia("V-102", EstadoAsistencia.JUSTIFICADO, motivo_justificacion="Llegó justificativo")
    ])
    repo.guardar_planilla(p2)
    
    # Comprobar que no hay duplicación (deben seguir siendo exactamente 2 filas)
    cur.execute("SELECT COUNT(*) FROM TBL_ASISTENCIA WHERE ID_CLASE = 1 AND FECHA = '2026-11-21'")
    assert cur.fetchone()[0] == 2
    
    # Comprobar que en justificaciones hay exactamente 1 fila
    cur.execute("SELECT COUNT(*) FROM TBL_JUSTIFICACIONES")
    assert cur.fetchone()[0] == 1
    
    recuperada = repo.obtener_planilla(id_clase=1, fecha="2026-11-21")
    mapa = {r.id_estudiante: r for r in recuperada.registros}
    assert mapa["V-101"].estado == EstadoAsistencia.AUSENTE
    assert mapa["V-102"].estado == EstadoAsistencia.JUSTIFICADO

def test_validacion_defensiva_fecha_invalida(repo_asistencia):
    """Verifica que una fecha que no cumpla con ISO 8601 YYYY-MM-DD sea rechazada."""
    repo, db = repo_asistencia
    planilla = PlanillaAsistencia(id_clase=1, fecha="21/11/2026", registros=[])
    
    with pytest.raises(ValueError, match="formato ISO 8601"):
        repo.guardar_planilla(planilla)
    
    assert repo.obtener_planilla(id_clase=1, fecha="21-11-2026") is None

def test_obtener_planilla_inexistente(repo_asistencia):
    """Consultar una clase o fecha no registrada debe retornar None."""
    repo, db = repo_asistencia
    assert repo.obtener_planilla(id_clase=999, fecha="2026-11-21") is None
