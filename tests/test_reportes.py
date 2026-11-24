# tests/test_reportes.py
"""
Pruebas Unitarias para el Módulo de Reportes Hexagonal (RF-14, RF-15, CU-04).
Cubre:
1. Casos límite de la fórmula Art. 109 RGLOE y alertas de riesgo (CP-04).
2. Consultas SQLite en memoria: Diario, Mensual, Historial y demografía (períodos con datos y vacíos).
3. Generación real de PDF verificando existencia, contenido y cabecera %PDF (CP-05).
"""

import pytest
from pathlib import Path

from db_conexion import ConexionBD
from dominio.reportes import AnalizadorEstadistico, AsistenciaEnriquecida, AlertaRiesgo
from adaptadores.db.sqlite_reportes import RepositorioReportesSQLite
from adaptadores.documentos.pdf_reportes import ExportadorPDFReportLab


# ============================================================================
# 1. PRUEBAS DE DOMINIO: FÓRMULA OFICIAL ART. 109 RGLOE Y ALERTAS DE RIESGO
# ============================================================================

def test_formula_caso_limite_cero_clases():
    """
    Prevención de división entre cero:
    Cuando total_clases == 0, debe retornar 100.0% y NO debe marcar alerta de riesgo.
    """
    porcentaje = AnalizadorEstadistico.calcular_porcentaje(asistencias_efectivas=0, total_clases=0)
    assert porcentaje == 100.0
    assert AnalizadorEstadistico.es_alerta_riesgo(porcentaje) is False

    alerta = AlertaRiesgo(
        id_estudiante="V-001",
        nombre="Estudiante Sin Clases",
        total_clases=0,
        presentes=0,
        justificadas=0,
        faltas_injustificadas=0,
        porcentaje_asistencia=porcentaje
    )
    assert alerta.asistencias_efectivas == 0
    assert alerta.es_critico is False


def test_formula_caso_limite_cien_por_ciento():
    """
    100% de asistencia efectiva:
    asistencias_efectivas == total_clases -> 100.0%, NO riesgo.
    """
    porcentaje = AnalizadorEstadistico.calcular_porcentaje(asistencias_efectivas=20, total_clases=20)
    assert porcentaje == 100.0
    assert AnalizadorEstadistico.es_alerta_riesgo(porcentaje) is False

    alerta = AlertaRiesgo(
        id_estudiante="V-002",
        nombre="Estudiante Ejemplar",
        total_clases=20,
        presentes=20,
        justificadas=0,
        faltas_injustificadas=0,
        porcentaje_asistencia=porcentaje
    )
    assert alerta.es_critico is False


def test_formula_caso_limite_exactamente_75_por_ciento():
    """
    Caso Límite Legal:
    Exactamente 75.0% cumple el mínimo exigido por el Art. 109 RGLOE.
    NO debe estar en riesgo (es_critico == False).
    """
    # 75 asistencias de 100 clases = 75.0%
    porcentaje = AnalizadorEstadistico.calcular_porcentaje(asistencias_efectivas=75, total_clases=100)
    assert porcentaje == 75.0
    assert AnalizadorEstadistico.es_alerta_riesgo(porcentaje) is False

    alerta = AlertaRiesgo(
        id_estudiante="V-003",
        nombre="Estudiante Justo en Límite",
        total_clases=100,
        presentes=75,
        justificadas=0,
        faltas_injustificadas=25,
        porcentaje_asistencia=porcentaje
    )
    assert alerta.es_critico is False


def test_formula_caso_limite_74_9_por_ciento_en_riesgo_cp04():
    """
    CP-04: Caso Límite de Alerta Estricta:
    74.9% es estrictamente menor al 75.0% mínimo.
    DEBE marcar alerta de riesgo (es_critico == True).
    """
    porcentaje = AnalizadorEstadistico.calcular_porcentaje(asistencias_efectivas=749, total_clases=1000)
    assert porcentaje == 74.9
    assert AnalizadorEstadistico.es_alerta_riesgo(porcentaje) is True

    alerta = AlertaRiesgo(
        id_estudiante="V-004",
        nombre="Estudiante en Peligro",
        total_clases=1000,
        presentes=749,
        justificadas=0,
        faltas_injustificadas=251,
        porcentaje_asistencia=porcentaje
    )
    assert alerta.es_critico is True


def test_formula_faltas_justificadas_y_desglose_individual():
    """
    Considera 'P' y 'J' como asistencias efectivas (y 'A' como falta injustificada),
    manteniendo el desglose individual de P, A y J.
    """
    registros = [
        # Estudiante 1: 2 P, 1 J, 1 A en 4 clases -> 3 efectivas / 4 = 75.0% (NO riesgo)
        AsistenciaEnriquecida("V-10", "Carlos Perez", "M", "2026-11-01", "P"),
        AsistenciaEnriquecida("V-10", "Carlos Perez", "M", "2026-11-02", "P"),
        AsistenciaEnriquecida("V-10", "Carlos Perez", "M", "2026-11-03", "J", observacion="Médico"),
        AsistenciaEnriquecida("V-10", "Carlos Perez", "M", "2026-11-04", "A"),

        # Estudiante 2: 1 P, 1 J, 2 A en 4 clases -> 2 efectivas / 4 = 50.0% (EN RIESGO)
        AsistenciaEnriquecida("V-20", "Maria Gomez", "F", "2026-11-01", "P"),
        AsistenciaEnriquecida("V-20", "Maria Gomez", "F", "2026-11-02", "J", observacion="Constancia"),
        AsistenciaEnriquecida("V-20", "Maria Gomez", "F", "2026-11-03", "A"),
        AsistenciaEnriquecida("V-20", "Maria Gomez", "F", "2026-11-04", "A"),
    ]

    resumenes = AnalizadorEstadistico.generar_resumen_estudiantes(registros)
    mapa = {r.id_estudiante: r for r in resumenes}

    # Desglose y porcentaje Estudiante 1
    carlos = mapa["V-10"]
    assert carlos.presentes == 2
    assert carlos.justificadas == 1
    assert carlos.faltas_injustificadas == 1
    assert carlos.asistencias_efectivas == 3
    assert carlos.total_clases == 4
    assert carlos.porcentaje_asistencia == 75.0
    assert carlos.es_critico is False

    # Desglose y porcentaje Estudiante 2
    maria = mapa["V-20"]
    assert maria.presentes == 1
    assert maria.justificadas == 1
    assert maria.faltas_injustificadas == 2
    assert maria.asistencias_efectivas == 2
    assert maria.total_clases == 4
    assert maria.porcentaje_asistencia == 50.0
    assert maria.es_critico is True

    # Detección de riesgo
    alertas = AnalizadorEstadistico.detectar_riesgo(registros)
    assert len(alertas) == 1
    assert alertas[0].id_estudiante == "V-20"


def test_demografia_desglose_genero_y_estados():
    """Verifica que calcular_demografia cuente P, J y A para varones y hembras."""
    registros = [
        AsistenciaEnriquecida("V-1", "Juan", "M", "2026-11-01", "P"),
        AsistenciaEnriquecida("V-2", "Pedro", "M", "2026-11-01", "J"),
        AsistenciaEnriquecida("V-3", "Luis", "M", "2026-11-01", "A"),
        AsistenciaEnriquecida("V-4", "Ana", "F", "2026-11-01", "P"),
        AsistenciaEnriquecida("V-5", "Sofia", "F", "2026-11-01", "A"),
    ]
    demo = AnalizadorEstadistico.calcular_demografia(registros)
    assert demo["total_general"] == 5
    assert demo["total_masculino"] == 3
    assert demo["total_femenino"] == 2
    assert demo["masculino_presente"] == 1
    assert demo["masculino_justificado"] == 1
    assert demo["masculino_ausente"] == 1
    assert demo["femenino_presente"] == 1
    assert demo["femenino_ausente"] == 1
    assert demo["femenino_justificado"] == 0


# ============================================================================
# 2. PRUEBAS DE ADAPTADOR PERSISTENCIA SQLITE (:memory:)
# ============================================================================

@pytest.fixture
def repo_reportes_db():
    """Inicializa una base de datos en memoria con esquema y datos completos de prueba."""
    db = ConexionBD(ruta_db=":memory:")
    conn = db.conectar()
    cursor = conn.cursor()

    # 1. Docente y Clase
    cursor.execute("INSERT INTO TBL_PROFESORES (ID_PROFESOR, CEDULA, NOMBRE_COMPLETO) VALUES (1, 'V-1111', 'Prof. Roberto')")
    cursor.execute("INSERT INTO TBL_CLASES (ID_CLASE, NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES (1, 'Física', 1, 4, 1)")

    # 2. Estudiantes (Varón y Hembra)
    cursor.execute("""
        INSERT INTO TBL_ESTUDIANTES 
        (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO, ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION)
        VALUES 
        ('V-101', 'Alejandro Morales', '2008-03-10', 'Rep A', '0414', 'M', 'Regular', 'Mañana', 'Activo', 4, 1),
        ('V-102', 'Beatriz Colmenares', '2008-07-22', 'Rep B', '0416', 'F', 'Regular', 'Mañana', 'Activo', 4, 1)
    """)

    # 3. Asistencias en fechas distintas
    # Fecha 1: 2026-11-20 (Alejandro 'P', Beatriz 'J' con justificación)
    cursor.execute("INSERT INTO TBL_ASISTENCIA (ID_ASISTENCIA, ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (1, 1, 'V-101', '2026-11-20', 'P')")
    cursor.execute("INSERT INTO TBL_ASISTENCIA (ID_ASISTENCIA, ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (2, 1, 'V-102', '2026-11-20', 'J')")
    cursor.execute("INSERT INTO TBL_JUSTIFICACIONES (ID_JUSTIFICACION, ID_ASISTENCIA, MOTIVO) VALUES (1, 2, 'Cita odontológica')")

    # Fecha 2: 2026-11-21 (Alejandro 'P', Beatriz 'A')
    cursor.execute("INSERT INTO TBL_ASISTENCIA (ID_ASISTENCIA, ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (3, 1, 'V-101', '2026-11-21', 'P')")
    cursor.execute("INSERT INTO TBL_ASISTENCIA (ID_ASISTENCIA, ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (4, 1, 'V-102', '2026-11-21', 'A')")

    # Fecha 3: Mes 10 (Octubre 2026-10-15): Alejandro 'A', Beatriz 'A'
    cursor.execute("INSERT INTO TBL_ASISTENCIA (ID_ASISTENCIA, ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (5, 1, 'V-101', '2026-10-15', 'A')")
    cursor.execute("INSERT INTO TBL_ASISTENCIA (ID_ASISTENCIA, ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (6, 1, 'V-102', '2026-10-15', 'A')")

    conn.commit()

    repo = RepositorioReportesSQLite(db)
    yield repo, db
    db.cerrar_definitivo()


def test_sqlite_reporte_diario_fecha_exacta(repo_reportes_db):
    """Consulta de asistencia por fecha exacta y recuperación de justificación."""
    repo, _ = repo_reportes_db

    # Fecha con registros
    registros = repo.obtener_asistencia_por_fecha("2026-11-20")
    assert len(registros) == 2

    mapa = {r.id_estudiante: r for r in registros}
    assert "V-101" in mapa
    assert mapa["V-101"].estado == "P"
    assert mapa["V-101"].observacion == "-"
    assert mapa["V-101"].materia == "Física"

    assert "V-102" in mapa
    assert mapa["V-102"].estado == "J"
    assert mapa["V-102"].observacion == "Cita odontológica"
    assert mapa["V-102"].genero == "F"


def test_sqlite_reporte_diario_periodo_vacio(repo_reportes_db):
    """Consulta por fecha sin registros debe retornar lista vacía."""
    repo, _ = repo_reportes_db
    registros = repo.obtener_asistencia_por_fecha("2026-01-01")
    assert registros == []


def test_sqlite_reporte_mensual_con_datos_y_vacio(repo_reportes_db):
    """Consulta de asistencia por mes (usando strftime('%m', FECHA)) y año."""
    repo, _ = repo_reportes_db

    # Mes Noviembre (11) de 2026: 4 registros
    registros_nov = repo.obtener_asistencia_por_mes("11", "2026")
    assert len(registros_nov) == 4

    # Nombre de mes textual ("Noviembre")
    registros_nov_nombre = repo.obtener_asistencia_por_mes("Noviembre", "2026")
    assert len(registros_nov_nombre) == 4

    # Mes Octubre (10) de 2026: 2 registros
    registros_oct = repo.obtener_asistencia_por_mes("10", "2026")
    assert len(registros_oct) == 2

    # Mes sin registros (Mayo "05")
    registros_vacio = repo.obtener_asistencia_por_mes("05", "2026")
    assert registros_vacio == []


def test_sqlite_historial_estudiante(repo_reportes_db):
    """Consulta del historial completo por cédula del estudiante."""
    repo, _ = repo_reportes_db

    # Estudiante V-101: 3 clases (2 P, 1 A)
    historial_101 = repo.obtener_historial_estudiante("V-101")
    assert len(historial_101) == 3
    estados_101 = [r.estado for r in historial_101]
    assert estados_101.count("P") == 2
    assert estados_101.count("A") == 1

    # Estudiante V-102: 3 clases (1 J, 2 A)
    historial_102 = repo.obtener_historial_estudiante("V-102")
    assert len(historial_102) == 3
    obs = [r.observacion for r in historial_102 if r.estado == "J"]
    assert "Cita odontológica" in obs

    # Estudiante inexistente
    historial_fantasma = repo.obtener_historial_estudiante("V-999999")
    assert historial_fantasma == []


def test_sqlite_resumen_genero(repo_reportes_db):
    """Verifica agregación SQL de demografía por género."""
    repo, _ = repo_reportes_db
    stats_nov = repo.obtener_resumen_genero(mes="11", anio="2026")
    assert stats_nov.get("M_P") == 2
    assert stats_nov.get("F_J") == 1
    assert stats_nov.get("F_A") == 1


# ============================================================================
# 3. PRUEBAS DE ADAPTADOR PDF: REGLA CP-05 (CABECERA %PDF)
# ============================================================================

def test_exportador_pdf_generacion_real_y_cabecera_cp05(tmp_path: Path):
    """
    CP-05: Generación real de un PDF en tmp_path.
    Verifica que:
    1. El archivo se genera con éxito (retorna True).
    2. El archivo existe físicamente en el disco.
    3. No está vacío (tamaño > 0 bytes).
    4. Comienza estrictamente con la cabecera estándar de documento PDF: %PDF.
    """
    exportador = ExportadorPDFReportLab()
    ruta_pdf = tmp_path / "reporte_asistencia_oficial.pdf"

    titulo = "REPORTE MENSUAL DE ASISTENCIA ESCOLAR"
    encabezados = ["Fecha", "Cédula", "Estudiante", "Gen", "Materia", "ST", "Justificación"]
    datos = [
        ["2026-11-20", "V-101", "Alejandro Morales", "M", "Física", "P", "-"],
        ["2026-11-20", "V-102", "Beatriz Colmenares", "F", "Física", "J", "Cita odontológica"],
        ["2026-11-21", "V-101", "Alejandro Morales", "M", "Física", "P", "-"],
        ["2026-11-21", "V-102", "Beatriz Colmenares", "F", "Física", "A", "-"],
    ]

    exito = exportador.exportar_tabla(
        titulo=titulo,
        encabezados=encabezados,
        datos=datos,
        ruta_salida=str(ruta_pdf)
    )

    # 1. Generación exitosa
    assert exito is True

    # 2. Existencia en disco
    assert ruta_pdf.exists()

    # 3. Archivo no vacío
    tamano = ruta_pdf.stat().st_size
    assert tamano > 0

    # 4. Cabecera estándar de documento PDF (CP-05)
    with open(ruta_pdf, "rb") as archivo_pdf:
        cabecera = archivo_pdf.read(4)
        assert cabecera == b"%PDF", f"La cabecera obtenida fue {cabecera}, se esperaba b'%PDF'"
