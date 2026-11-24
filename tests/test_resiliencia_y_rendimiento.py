# tests/test_resiliencia_y_rendimiento.py
"""
Pruebas de Resiliencia ante Fallos Eléctricos y Rendimiento (RNF-01 y RNF-04).

Cubre:
1. Resiliencia JSON (RNF-04): Manejo defensivo de archivo memoria_emergencia.json corrupto,
   truncado por corte de luz, vacío o con estructura malformada, garantizando que
   RespaldoAsistenciaJSON nunca lance excepciones no controladas.
2. Rendimiento (RNF-01): Medición estricta con time.perf_counter() en una base de datos con
   150 estudiantes y 1.500 registros de asistencia:
   - Consulta y análisis estadístico del 75% (Art. 109 RGLOE) en < 1.5 segundos.
   - Generación real de documento PDF con ReportLab Platypus en < 3.0 segundos.
"""

import time
import pytest
from db_conexion import ConexionBD
from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia
from dominio.reportes import AnalizadorEstadistico
from adaptadores.respaldo.json_asistencia import RespaldoAsistenciaJSON
from adaptadores.db.sqlite_reportes import RepositorioReportesSQLite
from adaptadores.documentos.pdf_reportes import ExportadorPDFReportLab


# =============================================================================
# 1. PRUEBAS DE RESILIENCIA ANTE APAGONES Y CORRUPCIÓN DE ARCHIVO JSON (RNF-04)
# =============================================================================

def test_resiliencia_json_archivo_vacio(tmp_path):
    """Un archivo de 0 bytes producto de un apagón repentino debe retornar None limpiamente."""
    archivo_json = tmp_path / "memoria_emergencia.json"
    archivo_json.write_text("", encoding="utf-8")

    respaldo = RespaldoAsistenciaJSON(ruta_archivo=str(archivo_json))
    resultado = respaldo.recuperar_respaldo(id_clase=1, fecha="2026-11-24")
    assert resultado is None, "Un archivo vacío de 0 bytes debe retornar None sin fallar."


def test_resiliencia_json_archivo_truncado_por_apagon(tmp_path):
    """
    Simula corte eléctrico durante la escritura: archivo JSON cortado a mitad de un string.
    No debe provocar JSONDecodeError no controlado.
    """
    archivo_json = tmp_path / "memoria_emergencia.json"
    # JSON cortado abruptamente
    archivo_json.write_text('{"id_clase": 1, "fecha": "2026-11-24", "registros": [{"id_estudia', encoding="utf-8")

    respaldo = RespaldoAsistenciaJSON(ruta_archivo=str(archivo_json))
    resultado = respaldo.recuperar_respaldo(id_clase=1, fecha="2026-11-24")
    assert resultado is None, "Un archivo JSON truncado debe ser ignorado de forma segura retornando None."


@pytest.mark.parametrize("contenido_malformado", [
    "[]",
    "null",
    '"solo un string"',
    "12345",
    '{"id_clase": 1}',  # Falta clave fecha
    '{"id_clase": 1, "fecha": "2026-11-24", "registros": "no es una lista"}',
])
def test_resiliencia_json_estructura_invalida(tmp_path, contenido_malformado):
    """Estructuras JSON que no coinciden con el esquema esperado deben retornar None."""
    archivo_json = tmp_path / "memoria_emergencia.json"
    archivo_json.write_text(contenido_malformado, encoding="utf-8")

    respaldo = RespaldoAsistenciaJSON(ruta_archivo=str(archivo_json))
    resultado = respaldo.recuperar_respaldo(id_clase=1, fecha="2026-11-24")
    assert resultado is None


def test_resiliencia_json_registro_con_estado_invalido(tmp_path):
    """Si un registro individual contiene un estado desconocido, se omite defensivamente."""
    archivo_json = tmp_path / "memoria_emergencia.json"
    json_data = """{
        "id_clase": 5,
        "fecha": "2026-11-24",
        "registros": [
            {"id_estudiante": "V-100", "estado": "P"},
            {"id_estudiante": "V-200", "estado": "ESTADO_CORRUPTO_O_DESCONOCIDO"},
            {"id_estudiante": "V-300", "estado": "A"}
        ]
    }"""
    archivo_json.write_text(json_data, encoding="utf-8")

    respaldo = RespaldoAsistenciaJSON(ruta_archivo=str(archivo_json))
    recuperada = respaldo.recuperar_respaldo(id_clase=5, fecha="2026-11-24")

    assert recuperada is not None
    # Debe haber recuperado los dos válidos ("V-100" y "V-300") omitiendo el corrupto
    ids_recuperados = [r.id_estudiante for r in recuperada.registros]
    assert "V-100" in ids_recuperados
    assert "V-300" in ids_recuperados
    assert "V-200" not in ids_recuperados


# =============================================================================
# 2. PRUEBAS DE RENDIMIENTO CON VOLUMEN DE DATOS (RNF-01)
# =============================================================================

@pytest.fixture
def bd_rendimiento_1500_registros():
    """
    Inicializa una base de datos en memoria con:
    - 150 estudiantes en 4to Año.
    - 1 Profesor y 1 Clase de Matemáticas.
    - 10 jornadas de asistencia (1.500 registros de asistencia en TBL_ASISTENCIA).
    """
    db = ConexionBD(ruta_db=":memory:")
    conn = db.conectar()
    cur = conn.cursor()

    # 1. Crear profesor y clase
    cur.execute("INSERT INTO TBL_PROFESORES (CEDULA, NOMBRE_COMPLETO) VALUES ('V-DOC-BENCH', 'Profesor Benchmark')")
    id_prof = cur.lastrowid
    cur.execute("INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES ('MATEMÁTICAS', ?, 4, 1)", (id_prof,))
    id_clase = cur.lastrowid

    # 2. Crear 150 estudiantes
    estudiantes_lote = []
    for i in range(1, 151):
        cedula = f"V-BENCH-{i:04d}"
        nombre = f"ESTUDIANTE DE PRUEBA NUMERO {i:04d}"
        genero = "M" if i % 2 == 0 else "F"
        estudiantes_lote.append((cedula, nombre, "2009-01-01", "Representante", "0414", genero, "Regular", "Mañana", "Activo", 4, 1, 1))

    cur.executemany(
        """
        INSERT INTO TBL_ESTUDIANTES 
        (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO, ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION, ESTADO_ACTIVO)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        estudiantes_lote
    )

    # 3. Crear 10 jornadas de asistencia (150 alumnos * 10 días = 1.500 registros)
    fechas = [f"2026-11-{d:02d}" for d in range(1, 11)]
    asistencias_lote = []

    for dia_idx, fecha in enumerate(fechas):
        for i in range(1, 151):
            cedula = f"V-BENCH-{i:04d}"
            # Alumnos 1 al 20 tienen inasistencias intencionales para evaluar < 75%
            if i <= 20 and dia_idx >= 4:
                estado = "A"
            elif i % 15 == 0:
                estado = "J"
            else:
                estado = "P"

            asistencias_lote.append((id_clase, cedula, fecha, estado))

    cur.executemany(
        "INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (?, ?, ?, ?)",
        asistencias_lote
    )
    conn.commit()

    yield db
    db.cerrar_definitivo()


def test_rendimiento_consulta_reporte_y_calculo_75_porciento(bd_rendimiento_1500_registros):
    """
    RNF-01: La consulta mensual de 1.500 registros de asistencia junto con el cálculo
    del porcentaje y la detección de alertas de riesgo debe ejecutarse en menos de 1.5 segundos.
    """
    repo_reportes = RepositorioReportesSQLite(bd_rendimiento_1500_registros)

    t_inicio = time.perf_counter()

    # 1. Consulta en persistencia SQLite
    registros = repo_reportes.obtener_asistencia_por_mes("11", "2026")
    assert len(registros) == 1500

    # 2. Procesamiento estadístico en capa de Dominio
    resumenes = AnalizadorEstadistico.generar_resumen_estudiantes(registros)
    assert len(resumenes) == 150

    alertas = AnalizadorEstadistico.detectar_riesgo(registros)
    assert len(alertas) >= 20  # Los primeros 20 alumnos caen en riesgo

    t_total = time.perf_counter() - t_inicio

    print(f"\n[BENCHMARK] Tiempo consulta 1.500 registros + cálculo 75%: {t_total:.4f} s")
    assert t_total < 1.5, f"El procesamiento tardó {t_total:.4f}s, superando el límite de 1.5 segundos."


def test_rendimiento_generacion_pdf_con_alto_volumen(bd_rendimiento_1500_registros, tmp_path):
    """
    RNF-01: La exportación a PDF oficial de 1.500 registros con ReportLab Platypus
    debe completarse en menos de 3.0 segundos.
    """
    repo_reportes = RepositorioReportesSQLite(bd_rendimiento_1500_registros)
    registros = repo_reportes.obtener_asistencia_por_mes("11", "2026")

    resumenes = AnalizadorEstadistico.generar_resumen_estudiantes(registros)
    mapa_pct = {r.id_estudiante: f"{r.porcentaje_asistencia:.1f}%" for r in resumenes}

    encabezados = ["Fecha", "Cédula", "Estudiante", "Gen", "Materia", "ST", "Justificación", "% Asist."]
    filas_datos = [
        [
            r.fecha,
            r.id_estudiante,
            r.nombre[:25],
            r.genero,
            r.materia,
            r.estado,
            r.observacion or "-",
            mapa_pct.get(r.id_estudiante, "-")
        ]
        for r in registros
    ]

    exportador_pdf = ExportadorPDFReportLab()
    ruta_salida = str(tmp_path / "benchmark_1500_asistencias.pdf")

    t_inicio = time.perf_counter()
    exito = exportador_pdf.exportar_tabla(
        titulo="REPORTE DE RENDIMIENTO — 1500 REGISTROS DE ASISTENCIA",
        encabezados=encabezados,
        datos=filas_datos,
        ruta_salida=ruta_salida
    )
    t_total = time.perf_counter() - t_inicio

    assert exito is True
    print(f"\n[BENCHMARK] Tiempo generación PDF de 1.500 filas: {t_total:.4f} s")
    assert t_total < 3.0, f"La generación de PDF tardó {t_total:.4f}s, superando el límite de 3.0 segundos."
