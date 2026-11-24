# tests/test_estadisticas_y_recuperacion.py
"""
Suite de pruebas unitarias y de integración para la Fase 2:
1. Recuperación y restablecimiento offline de credenciales (dominio + SQLite + TBL_AUDITORIA).
2. Estadísticas institucionales (dominio puro + RepositorioEstadisticasSQLite en :memory:).
3. Permisos RBAC del módulo 'estadisticas'.
"""

import pytest

from db_conexion import ConexionBD
from dominio.usuario import Usuario, ServicioRecuperacionUsuario
from dominio.permisos import (
    obtener_permisos_rol,
    tiene_permiso,
    validar_permiso,
    MODULO_ESTADISTICAS,
)
from dominio.estadisticas import CalculadoraEstadisticas
from adaptadores.db.sqlite_usuario import SQLiteRepositorioUsuario
from adaptadores.db.sqlite_estadisticas import RepositorioEstadisticasSQLite


@pytest.fixture
def db_mem():
    """Base de datos SQLite en memoria con esquema migrado e inicializado."""
    con = ConexionBD(":memory:")
    con.conectar()
    yield con
    con.cerrar_definitivo()


# ═════════════════════════════════════════════════════════════════════
# 1. RECUPERACIÓN / RESTABLECIMIENTO OFFLINE DE CREDENCIALES
# ═════════════════════════════════════════════════════════════════════

def test_recuperacion_rechaza_clave_maestra_erronea_sin_tocar_bd(db_mem):
    """Clave maestra errónea lanza PermissionError, mantiene hash intacto y no audita cambio."""
    repo = SQLiteRepositorioUsuario(db_mem)
    usr_antes = repo.obtener_por_username("admin")
    assert usr_antes is not None
    hash_original = usr_antes.password

    with pytest.raises(PermissionError):
        repo.restablecer_contrasena_con_auditoria(
            username="admin",
            nueva_password_plana="NuevaClave99",
            clave_maestra="CLAVE_INCORRECTA",
        )

    usr_despues = repo.obtener_por_username("admin")
    assert usr_despues.password == hash_original
    assert repo.autenticar("admin", "1234") is not None
    assert repo.autenticar("admin", "NuevaClave99") is None

    conn = db_mem.conectar()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM TBL_AUDITORIA WHERE ACCION = 'RESTABLECER_CREDENCIALES'")
    assert cur.fetchone()[0] == 0


def test_recuperacion_exitosa_pbkdf2_y_auditoria_sin_exponer_clave(db_mem):
    """
    Con clave maestra correcta:
    - La clave anterior deja de autenticar.
    - La clave nueva autentica con PBKDF2-HMAC-SHA256 (salt nuevo, hash != texto plano).
    - Se registra evento en TBL_AUDITORIA sin almacenar la contraseña.
    """
    repo = SQLiteRepositorioUsuario(db_mem)
    nuevo = Usuario(
        nombre_completo="Asistente Escolar",
        username="asistente_rec",
        password="ClaveInicial1",
        rol="ASISTENTE",
    )
    repo.guardar(nuevo)
    hash_viejo = repo.obtener_por_username("asistente_rec").password

    nueva_clave_plana = "ClaveRecuperada2026!"
    resultado = repo.restablecer_contrasena_con_auditoria(
        username="asistente_rec",
        nueva_password_plana=nueva_clave_plana,
        clave_maestra=ServicioRecuperacionUsuario.CLAVE_MAESTRA_INSTITUCIONAL,
    )
    assert resultado is True

    # Clave vieja rechazada, clave nueva autenticada
    assert repo.autenticar("asistente_rec", "ClaveInicial1") is None
    autenticado = repo.autenticar("asistente_rec", nueva_clave_plana)
    assert autenticado is not None
    assert autenticado.rol == "ASISTENTE"

    # Hash almacenado seguro y distinto del texto plano y del hash anterior
    assert "$" in autenticado.password
    assert autenticado.password != nueva_clave_plana
    assert autenticado.password != hash_viejo

    # Verificar registro en TBL_AUDITORIA sin exponer la contraseña
    conn = db_mem.conectar()
    cur = conn.cursor()
    cur.execute(
        "SELECT USUARIO, MODULO, ACCION, DETALLES FROM TBL_AUDITORIA "
        "WHERE ACCION = 'RESTABLECER_CREDENCIALES'"
    )
    fila = cur.fetchone()
    assert fila is not None
    assert fila[0] == "RECUPERACION_LOGIN"
    assert fila[1] == "SEGURIDAD"
    assert fila[2] == "RESTABLECER_CREDENCIALES"
    assert "asistente_rec" in fila[3]
    assert nueva_clave_plana not in fila[3]
    assert autenticado.password not in fila[3]


def test_recuperacion_rechaza_inexistente_inactivo_y_usernames_sin_hashes(db_mem):
    """
    Valida rechazo de usuario inexistente/inactivo, contraseña corta
    y que obtener_usernames_activos() retorne solo (username, rol) de activos sin hashes.
    """
    repo = SQLiteRepositorioUsuario(db_mem)
    activo = Usuario("Docente Activo", "doc_activo", "clave123", "DOCENTE")
    inactivo = Usuario("Docente Inactivo", "doc_inactivo", "clave456", "DOCENTE")
    repo.guardar(activo)
    repo.guardar(inactivo)
    repo.desactivar(inactivo.id_usuario)

    # Listado seguro solo de activos (username, rol)
    listado = repo.obtener_usernames_activos()
    usernames = [u for u, _ in listado]
    assert "admin" in usernames
    assert "doc_activo" in usernames
    assert "doc_inactivo" not in usernames
    for u, r in listado:
        assert isinstance(u, str) and isinstance(r, str)
        assert "$" not in u and "$" not in r
        assert "clave" not in u.lower()

    # Usuario inexistente -> ValueError
    with pytest.raises(ValueError):
        repo.restablecer_contrasena_con_auditoria("fantasma", "Nueva123", "DIRECTOR2025")

    # Usuario inactivo -> ValueError
    with pytest.raises(ValueError):
        repo.restablecer_contrasena_con_auditoria("doc_inactivo", "Nueva123", "DIRECTOR2025")

    # Contraseña corta -> ValueError
    with pytest.raises(ValueError):
        repo.restablecer_contrasena_con_auditoria("doc_activo", "12", "DIRECTOR2025")


# ═════════════════════════════════════════════════════════════════════
# 2. ESTADÍSTICAS INSTITUCIONALES (DOMINIO + SQLITE :MEMORY:)
# ═════════════════════════════════════════════════════════════════════

def test_estadisticas_bd_vacia_sin_division_por_cero(db_mem):
    """En una BD sin estudiantes ni asistencia, no lanza ZeroDivisionError y retorna defaults."""
    repo_est = RepositorioEstadisticasSQLite(db_mem)
    resumen = repo_est.obtener_resumen_institucional()

    assert resumen.total_estudiantes_activos == 0
    assert resumen.total_docentes_activos == 0
    assert resumen.total_clases_activas == 0
    assert resumen.total_registros_asistencia == 0
    assert resumen.tasa_asistencia_global == 100.0
    assert resumen.total_en_riesgo == 0
    assert resumen.distribucion_estados.total == 0
    assert resumen.distribucion_genero.total == 0
    assert resumen.metricas_por_seccion == []
    assert resumen.estudiantes_en_riesgo == []

    # Validación pura adicional en CalculadoraEstadisticas
    assert CalculadoraEstadisticas.calcular_tasa_efectiva(0, 0, 0) == 100.0
    assert CalculadoraEstadisticas.calcular_proporcion(0, 0) == 0.0
    assert CalculadoraEstadisticas.es_en_riesgo(74.9, 1) is True
    assert CalculadoraEstadisticas.es_en_riesgo(75.0, 4) is False
    assert CalculadoraEstadisticas.es_en_riesgo(0.0, 0) is False


def test_estadisticas_exactitud_kpis_secciones_genero_y_alertas(db_mem):
    """Verifica exactitud de KPIs, distribución P/A/J, tasas por sección, género y alertas < 75%."""
    conn = db_mem.conectar()
    cur = conn.cursor()

    # 2 profesores activos y 1 inactivo
    cur.execute("INSERT INTO TBL_PROFESORES (CEDULA, NOMBRE_COMPLETO, ESTADO_ACTIVO) VALUES ('V-101', 'PROF A', 1)")
    id_p1 = cur.lastrowid
    cur.execute("INSERT INTO TBL_PROFESORES (CEDULA, NOMBRE_COMPLETO, ESTADO_ACTIVO) VALUES ('V-102', 'PROF B', 1)")
    id_p2 = cur.lastrowid
    cur.execute("INSERT INTO TBL_PROFESORES (CEDULA, NOMBRE_COMPLETO, ESTADO_ACTIVO) VALUES ('V-103', 'PROF INACT', 0)")

    # Clases en 4to A (id_seccion=1) y 4to B (id_seccion=2)
    cur.execute("INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES ('MATEMÁTICAS', ?, 4, 1)", (id_p1,))
    c1 = cur.lastrowid
    cur.execute("INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES ('FÍSICA', ?, 4, 2)", (id_p2,))
    c2 = cur.lastrowid

    # 3 estudiantes activos (2 M, 1 F) + 1 inactivo (no debe contar)
    cur.execute(
        "INSERT INTO TBL_ESTUDIANTES (ID_ESTUDIANTE, NOMBRE, GENERO, ID_GRADO, ID_SECCION, ESTADO_ACTIVO) "
        "VALUES ('V-301', 'ALUMNO UNO', 'M', 4, 1, 1)"
    )
    cur.execute(
        "INSERT INTO TBL_ESTUDIANTES (ID_ESTUDIANTE, NOMBRE, GENERO, ID_GRADO, ID_SECCION, ESTADO_ACTIVO) "
        "VALUES ('V-302', 'ALUMNA DOS', 'F', 4, 1, 1)"
    )
    cur.execute(
        "INSERT INTO TBL_ESTUDIANTES (ID_ESTUDIANTE, NOMBRE, GENERO, ID_GRADO, ID_SECCION, ESTADO_ACTIVO) "
        "VALUES ('V-303', 'ALUMNO TRES', 'M', 4, 2, 1)"
    )
    cur.execute(
        "INSERT INTO TBL_ESTUDIANTES (ID_ESTUDIANTE, NOMBRE, GENERO, ID_GRADO, ID_SECCION, ESTADO_ACTIVO) "
        "VALUES ('V-304', 'INACTIVO', 'F', 4, 2, 0)"
    )

    # Asistencia V-301 (4to A): 3 P, 1 J => 4/4 = 100.0% (NO riesgo)
    for idx, est in enumerate(["P", "P", "P", "J"], start=1):
        cur.execute(
            "INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (?, 'V-301', ?, ?)",
            (c1, f"2026-11-0{idx}", est),
        )

    # Asistencia V-302 (4to A): 2 P, 2 A => 2/4 = 50.0% (EN RIESGO)
    for idx, est in enumerate(["P", "P", "A", "A"], start=1):
        cur.execute(
            "INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (?, 'V-302', ?, ?)",
            (c1, f"2026-11-0{idx}", est),
        )

    # Asistencia V-303 (4to B): 3 P, 1 A => 3/4 = 75.0% (EXACTAMENTE 75% -> NO riesgo)
    for idx, est in enumerate(["P", "P", "P", "A"], start=1):
        cur.execute(
            "INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (?, 'V-303', ?, ?)",
            (c2, f"2026-11-0{idx}", est),
        )

    # Registro de inactivo (no debe distorsionar métricas)
    cur.execute(
        "INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (?, 'V-304', '2026-11-01', 'A')",
        (c2,),
    )
    conn.commit()

    repo_est = RepositorioEstadisticasSQLite(db_mem)
    resumen = repo_est.obtener_resumen_institucional()

    assert resumen.total_estudiantes_activos == 3
    assert resumen.total_docentes_activos == 2
    assert resumen.total_clases_activas == 2
    assert resumen.total_registros_asistencia == 12

    # P = 8, J = 1, A = 3 => efectivas = 9/12 = 75.0%
    assert resumen.distribucion_estados.presentes == 8
    assert resumen.distribucion_estados.justificadas == 1
    assert resumen.distribucion_estados.ausentes == 3
    assert resumen.tasa_asistencia_global == 75.0

    # Género activos: 2 M, 1 F
    assert resumen.distribucion_genero.masculino == 2
    assert resumen.distribucion_genero.femenino == 1

    # Métricas por sección: 4to A = 6/8 (75.0%), 4to B = 3/4 (75.0%)
    mapa_sec = {m.etiqueta: m for m in resumen.metricas_por_seccion}
    assert "4to A" in mapa_sec and mapa_sec["4to A"].tasa_efectiva == 75.0
    assert "4to B" in mapa_sec and mapa_sec["4to B"].tasa_efectiva == 75.0

    # Alertas < 75%: solo V-302 (50.0%)
    assert resumen.total_en_riesgo == 1
    assert len(resumen.estudiantes_en_riesgo) == 1
    assert resumen.estudiantes_en_riesgo[0].id_estudiante == "V-302"
    assert resumen.estudiantes_en_riesgo[0].porcentaje_asistencia == 50.0


# ═════════════════════════════════════════════════════════════════════
# 3. PERMISOS RBAC DE ESTADÍSTICAS
# ═════════════════════════════════════════════════════════════════════

def test_rbac_modulo_estadisticas():
    """ADMIN y ASISTENTE tienen acceso a estadísticas; DOCENTE no."""
    assert tiene_permiso("ADMIN", MODULO_ESTADISTICAS) is True
    assert tiene_permiso("ASISTENTE", MODULO_ESTADISTICAS) is True
    assert tiene_permiso("DOCENTE", MODULO_ESTADISTICAS) is False

    assert obtener_permisos_rol("ADMIN")[MODULO_ESTADISTICAS] is True
    assert obtener_permisos_rol("ASISTENTE")[MODULO_ESTADISTICAS] is True
    assert obtener_permisos_rol("DOCENTE")[MODULO_ESTADISTICAS] is False

    assert validar_permiso("ADMIN", MODULO_ESTADISTICAS) is True
    assert validar_permiso("ASISTENTE", MODULO_ESTADISTICAS) is True
    with pytest.raises(PermissionError, match="Acceso denegado"):
        validar_permiso("DOCENTE", MODULO_ESTADISTICAS)


def test_exportador_pdf_generar_reporte_estadisticas_real(db_mem, tmp_path):
    """Genera un archivo PDF físico real desde ExportadorPDFReportLab.generar_reporte_estadisticas."""
    import os
    from adaptadores.documentos.pdf_reportes import ExportadorPDFReportLab

    conn = db_mem.conectar()
    cur = conn.cursor()
    cur.execute("INSERT INTO TBL_PROFESORES (CEDULA, NOMBRE_COMPLETO, ESTADO_ACTIVO) VALUES ('V-501', 'DOC PDF', 1)")
    id_p = cur.lastrowid
    cur.execute("INSERT INTO TBL_CLASES (NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES ('HISTORIA', ?, 4, 1)", (id_p,))
    id_c = cur.lastrowid
    cur.execute(
        "INSERT INTO TBL_ESTUDIANTES (ID_ESTUDIANTE, NOMBRE, GENERO, ID_GRADO, ID_SECCION, ESTADO_ACTIVO) "
        "VALUES ('V-601', 'ALUMNO RIESGO PDF', 'M', 4, 1, 1)"
    )
    cur.execute("INSERT INTO TBL_ASISTENCIA (ID_CLASE, ID_ESTUDIANTE, FECHA, ESTADO) VALUES (?, 'V-601', '2026-11-10', 'A')", (id_c,))
    conn.commit()

    repo_est = RepositorioEstadisticasSQLite(db_mem)
    resumen = repo_est.obtener_resumen_institucional()

    ruta_pdf = str(tmp_path / "estadisticas_institucionales.pdf")
    exportador = ExportadorPDFReportLab()
    assert exportador.generar_reporte_estadisticas(resumen, ruta_pdf) is True
    assert os.path.exists(ruta_pdf)
    assert os.path.getsize(ruta_pdf) > 1000
    with open(ruta_pdf, "rb") as f:
        assert f.read(5).startswith(b"%PDF-")
