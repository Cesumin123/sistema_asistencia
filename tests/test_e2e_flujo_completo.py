# tests/test_e2e_flujo_completo.py
"""
Suite de Pruebas Integrales End-to-End (E2E) - Ciclo de Vida Real del Sistema.
Complejo Educativo 'Colinas del Llano'.

Valida el ciclo de vida real completo de punta a punta:
1. Autenticación con usuario ADMIN (PBKDF2) y control de acceso RBAC frente a ASISTENTE y DOCENTE.
2. Registro de profesores, inscripción de estudiantes de 4to año (Secciones A y B) y asignación de clases.
3. Pase de lista completo con simulación de corte eléctrico (escritura y recuperación en memoria_emergencia.json),
   marcado de P/A/J con justificación, guardado atómico sin duplicados en SQLite y limpieza del JSON.
4. Generación de reportes diario, mensual e historial, verificando la detección automática de alumno en
   riesgo (< 75.0% según Art. 109 RGLOE) y alumno en regla (>= 75.0%).
5. Exportación real a PDF con ReportLab verificando existencia física y cabecera %PDF.
6. Consulta en Listados Centralizados y ejecución de Promoción Anual en cascada inversa protegida
   por clave maestra institucional, verificando actualización de grados y auditoría en TBL_AUDITORIA.
"""

import os
import pytest

from db_conexion import ConexionBD

# Capa de Dominio
from dominio.usuario import Usuario
from dominio.profesor import Profesor
from dominio.estudiante import Estudiante
from dominio.clase import Clase
from dominio.asistencia import PlanillaAsistencia, RegistroAsistencia, EstadoAsistencia
from dominio.reportes import AnalizadorEstadistico
from dominio.promocion import ServicioPromocionDominio
from dominio.permisos import (
    obtener_permisos_rol,
    tiene_permiso,
    validar_permiso,
    MODULO_ESTUDIANTES,
    MODULO_ACADEMICO,
    MODULO_ASISTENCIA,
    MODULO_LISTADOS,
    MODULO_REPORTES,
    MODULO_PROMOCION,
    MODULO_USUARIOS,
)

# Capa de Adaptadores de Persistencia y Documentos
from adaptadores.db.sqlite_usuario import SQLiteRepositorioUsuario
from adaptadores.db.sqlite_profesor import SQLiteRepositorioProfesor
from adaptadores.db.sqlite_estudiante import RepositorioEstudianteSQLite
from adaptadores.db.sqlite_clase import SQLiteRepositorioClase
from adaptadores.db.sqlite_asistencia import RepositorioAsistenciaSQLite
from adaptadores.respaldo.json_asistencia import RespaldoAsistenciaJSON
from adaptadores.db.sqlite_reportes import RepositorioReportesSQLite
from adaptadores.db.sqlite_listados import RepositorioListadosSQLite
from adaptadores.db.sqlite_promocion import RepositorioPromocionSQLite
from adaptadores.documentos.pdf_reportes import ExportadorPDFReportLab


@pytest.fixture
def base_de_datos_aislada():
    """Inicializa una base de datos SQLite en memoria completamente aislada para la prueba E2E."""
    db = ConexionBD(ruta_db=":memory:")
    yield db
    db.cerrar_definitivo()


def test_e2e_ciclo_completo_sistema_escolar(base_de_datos_aislada, tmp_path):
    """
    Prueba End-to-End exhaustiva del ciclo operativo y académico completo del sistema.
    """
    db = base_de_datos_aislada

    # =========================================================================
    # FASE 1: AUTENTICACIÓN CRIPTOGRÁFICA (PBKDF2) Y MATRIZ RBAC
    # =========================================================================
    repo_usuario = SQLiteRepositorioUsuario(db)

    # 1.1 Autenticación de cuenta ADMIN inicial creada por el DDL de db_conexion
    admin_auth = repo_usuario.autenticar("admin", "1234")
    assert admin_auth is not None, "El administrador inicial 'admin' debe autenticar correctamente."
    assert admin_auth.rol == "ADMIN"
    assert admin_auth.estado_activo == 1

    # 1.2 Creación y autenticación de cuentas con roles ASISTENTE y DOCENTE
    usuario_asistente = Usuario(
        nombre_completo="MARIA COORDINADORA",
        username="masistente",
        password="claveSegura2026*",
        rol="ASISTENTE"
    )
    usuario_asistente.validar()
    repo_usuario.guardar(usuario_asistente)

    asistente_auth = repo_usuario.autenticar("masistente", "claveSegura2026*")
    assert asistente_auth is not None
    assert asistente_auth.rol == "ASISTENTE"

    usuario_docente = Usuario(
        nombre_completo="PEDRO PROFESOR",
        username="pdocente",
        password="docentePass2026*",
        rol="DOCENTE"
    )
    usuario_docente.validar()
    repo_usuario.guardar(usuario_docente)

    docente_auth = repo_usuario.autenticar("pdocente", "docentePass2026*")
    assert docente_auth is not None
    assert docente_auth.rol == "DOCENTE"

    # 1.3 Verificación de la matriz RBAC para los tres roles
    # ADMIN: Acceso total a todos los módulos
    permisos_admin = obtener_permisos_rol("ADMIN")
    assert all(permisos_admin.values())
    assert validar_permiso("ADMIN", MODULO_ACADEMICO) is True
    assert validar_permiso("ADMIN", MODULO_PROMOCION) is True

    # ASISTENTE: Estudiantes, Asistencia, Listados, Reportes (Sin acceso a Carga Académica, Promoción ni Usuarios)
    permisos_asist = obtener_permisos_rol("ASISTENTE")
    assert permisos_asist[MODULO_ESTUDIANTES] is True
    assert permisos_asist[MODULO_ASISTENCIA] is True
    assert permisos_asist[MODULO_LISTADOS] is True
    assert permisos_asist[MODULO_REPORTES] is True
    assert permisos_asist[MODULO_ACADEMICO] is False
    assert permisos_asist[MODULO_PROMOCION] is False
    assert permisos_asist[MODULO_USUARIOS] is False

    with pytest.raises(PermissionError):
        validar_permiso("ASISTENTE", MODULO_PROMOCION)

    # DOCENTE: Solo Asistencia y Listados de lectura
    permisos_doc = obtener_permisos_rol("DOCENTE")
    assert permisos_doc[MODULO_ASISTENCIA] is True
    assert permisos_doc[MODULO_LISTADOS] is True
    assert permisos_doc[MODULO_ESTUDIANTES] is False
    assert permisos_doc[MODULO_REPORTES] is False
    assert permisos_doc[MODULO_ACADEMICO] is False

    with pytest.raises(PermissionError):
        validar_permiso("DOCENTE", MODULO_ESTUDIANTES)

    # =========================================================================
    # FASE 2: REGISTRO DE PROFESORES, ESTUDIANTES Y ASIGNACIÓN DE CLASES
    # =========================================================================
    repo_profesor = SQLiteRepositorioProfesor(db)
    repo_estudiante = RepositorioEstudianteSQLite(db)
    repo_clase = SQLiteRepositorioClase(db)

    # 2.1 Registro de Profesores
    prof1 = Profesor(cedula="V-11223344", nombre_completo="PROF. ROBERTO MENDEZ")
    prof1.validar()
    repo_profesor.guardar(prof1)

    prof2 = Profesor(cedula="V-22334455", nombre_completo="PROF. CARMEN BLANCO")
    prof2.validar()
    repo_profesor.guardar(prof2)

    profesores_activos = repo_profesor.obtener_todos()
    assert len(profesores_activos) == 2
    id_prof_mendez = profesores_activos[0].id_profesor
    id_prof_blanco = profesores_activos[1].id_profesor

    # 2.2 Inscripción de Estudiantes en 4to Año (ID_GRADO = 4)
    # Sección A (ID_SECCION = 1)
    est_carlos = Estudiante(
        cedula="V-30111222",
        nombre="CARLOS ALBERTO RUIZ",
        fecha_nacimiento="15/03/2009",
        representante="MARTA RUIZ",
        telefono="0414-1111111",
        genero="M",
        escolaridad="Regular",
        turno="Mañana",
        condicion="Activo",
        id_grado=4,
        id_seccion=1
    )
    est_carlos.validar()
    assert repo_estudiante.guardar(est_carlos) is True

    est_ana = Estudiante(
        cedula="V-30222333",
        nombre="ANA MARIA GOMEZ",
        fecha_nacimiento="22/07/2009",
        representante="JOSE GOMEZ",
        telefono="0424-2222222",
        genero="F",
        escolaridad="Regular",
        turno="Mañana",
        condicion="Activo",
        id_grado=4,
        id_seccion=1
    )
    est_ana.validar()
    assert repo_estudiante.guardar(est_ana) is True

    # Sección B (ID_SECCION = 2)
    est_luis = Estudiante(
        cedula="V-30333444",
        nombre="LUIS EDUARDO TORRES",
        fecha_nacimiento="10/11/2009",
        representante="ROSA TORRES",
        telefono="0416-3333333",
        genero="M",
        escolaridad="Regular",
        turno="Tarde",
        condicion="Activo",
        id_grado=4,
        id_seccion=2
    )
    est_luis.validar()
    assert repo_estudiante.guardar(est_luis) is True

    est_elena = Estudiante(
        cedula="V-30444555",
        nombre="ELENA PATRICIA VARGAS",
        fecha_nacimiento="05/01/2009",
        representante="LUIS VARGAS",
        telefono="0412-4444444",
        genero="F",
        escolaridad="Regular",
        turno="Tarde",
        condicion="Activo",
        id_grado=4,
        id_seccion=2
    )
    est_elena.validar()
    assert repo_estudiante.guardar(est_elena) is True

    estudiantes_totales = repo_estudiante.obtener_todos_activos()
    assert len(estudiantes_totales) == 4

    # 2.3 Creación de Clases y Asignación de Materias
    clase_mat_4a = Clase(
        nombre_materia="MATEMATICAS",
        id_profesor=id_prof_mendez,
        id_grado=4,
        id_seccion=1
    )
    clase_fis_4a = Clase(
        nombre_materia="FISICA",
        id_profesor=id_prof_blanco,
        id_grado=4,
        id_seccion=1
    )
    clase_qui_4b = Clase(
        nombre_materia="QUIMICA",
        id_profesor=id_prof_blanco,
        id_grado=4,
        id_seccion=2
    )
    clase_mat_4a.validar()
    clase_fis_4a.validar()
    clase_qui_4b.validar()

    repo_clase.guardar_lote([clase_mat_4a, clase_fis_4a, clase_qui_4b])

    clases_disponibles = repo_clase.obtener_clases_disponibles()
    assert len(clases_disponibles) == 3
    id_clase_matematica_4a = clases_disponibles[0][0]

    # Verificar obtención de alumnos por clase (desacoplada de UI)
    alumnos_4a = repo_clase.obtener_estudiantes_por_clase(id_clase_matematica_4a)
    assert len(alumnos_4a) == 2
    cedulas_4a = [a[0] for a in alumnos_4a]
    assert "V-30111222" in cedulas_4a
    assert "V-30222333" in cedulas_4a

    # =========================================================================
    # FASE 3: PASE DE LISTA, ANTI-APAGONES (JSON), JUSTIFICACIONES Y GUARDADO ATÓMICO
    # =========================================================================
    repo_asistencia = RepositorioAsistenciaSQLite(db)
    ruta_memoria_json = str(tmp_path / "memoria_emergencia.json")
    respaldo_json = RespaldoAsistenciaJSON(ruta_archivo=ruta_memoria_json)

    # 3.1 Día 1: 2026-11-20 — Simulación de toma interactiva y corte eléctrico repentino
    planilla_dia1 = PlanillaAsistencia(id_clase=id_clase_matematica_4a, fecha="2026-11-20")
    planilla_dia1.registros.append(
        RegistroAsistencia(id_estudiante="V-30111222", estado=EstadoAsistencia.PRESENTE)
    )
    planilla_dia1.registros.append(
        RegistroAsistencia(id_estudiante="V-30222333", estado=EstadoAsistencia.AUSENTE)
    )

    # Se guarda síncronamente en JSON ante cada marcaje
    respaldo_json.guardar_respaldo(planilla_dia1)
    assert os.path.exists(ruta_memoria_json), "El archivo JSON de respaldo de emergencia debe crearse."

    # Se simula apagón eléctrico y reinicio: se recupera la sesión inconclusa
    planilla_restaurada = respaldo_json.recuperar_respaldo(id_clase=id_clase_matematica_4a, fecha="2026-11-20")
    assert planilla_restaurada is not None
    assert len(planilla_restaurada.registros) == 2

    # Se actualiza el segundo estudiante con inasistencia JUSTIFICADA y motivo legal
    planilla_restaurada.actualizar_registro(
        id_estudiante="V-30222333",
        nuevo_estado=EstadoAsistencia.JUSTIFICADO,
        motivo="Consulta médica de emergencia - Constancia presentada"
    )

    # Se guarda definitivamente en SQLite con transacción atómica
    repo_asistencia.guardar_planilla(planilla_restaurada)

    # Se limpia el JSON tras el guardado exitoso
    respaldo_json.limpiar_respaldo()
    assert not os.path.exists(ruta_memoria_json), "El JSON de emergencia debe eliminarse tras el guardado en BD."

    # Guardado defensivo repetido: no debe duplicar registros por clave primaria/fecha
    repo_asistencia.guardar_planilla(planilla_restaurada)
    planilla_verificada = repo_asistencia.obtener_planilla(id_clase_matematica_4a, "2026-11-20")
    assert planilla_verificada is not None
    assert len(planilla_verificada.registros) == 2

    # =========================================================================
    # FASE 4: HISTORIAL DE ASISTENCIA, REPORTES Y ALERTA DE RIESGO (ART. 109 RGLOE)
    # =========================================================================
    # Registrar 3 fechas adicionales de clase para Matemáticas de 4to A
    # Total de clases dictadas = 4:
    # - Carlos (V-30111222): 4 Asistencias ('P', 'P', 'P', 'P') = 100.0% -> En Regla (>= 75.0%)
    # - Ana (V-30222333): 1 Justificada ('J') + 3 Inasistencias injustificadas ('A', 'A', 'A')
    #   Asistencias efectivas = 1 ('J' cuenta como efectiva según Art. 109).
    #   Porcentaje = (1 / 4) * 100 = 25.0% -> ALERTA DE RIESGO (< 75.0%)
    fechas_adicionales = [
        ("2026-11-21", EstadoAsistencia.PRESENTE, EstadoAsistencia.AUSENTE),
        ("2026-11-22", EstadoAsistencia.PRESENTE, EstadoAsistencia.AUSENTE),
        ("2026-11-23", EstadoAsistencia.PRESENTE, EstadoAsistencia.AUSENTE),
    ]

    for fecha_iso, st_carlos, st_ana in fechas_adicionales:
        p = PlanillaAsistencia(id_clase=id_clase_matematica_4a, fecha=fecha_iso)
        p.registros.append(RegistroAsistencia(id_estudiante="V-30111222", estado=st_carlos))
        p.registros.append(RegistroAsistencia(id_estudiante="V-30222333", estado=st_ana))
        repo_asistencia.guardar_planilla(p)

    repo_reportes = RepositorioReportesSQLite(db)

    # 4.1 Reporte Diario
    reporte_diario = repo_reportes.obtener_asistencia_por_fecha("2026-11-20")
    assert len(reporte_diario) == 2

    # 4.2 Reporte Mensual (Noviembre 2026)
    reporte_mensual = repo_reportes.obtener_asistencia_por_mes("11", "2026")
    assert len(reporte_mensual) == 8  # 2 alumnos * 4 fechas

    # 4.3 Historial individual
    historial_carlos = repo_reportes.obtener_historial_estudiante("V-30111222")
    historial_ana = repo_reportes.obtener_historial_estudiante("V-30222333")
    assert len(historial_carlos) == 4
    assert len(historial_ana) == 4

    # 4.4 Evaluación de Riesgo por Servicio de Dominio (Art. 109 RGLOE)
    resumen_estudiantes = AnalizadorEstadistico.generar_resumen_estudiantes(reporte_mensual)
    mapa_resumen = {r.id_estudiante: r for r in resumen_estudiantes}

    alerta_carlos = mapa_resumen["V-30111222"]
    alerta_ana = mapa_resumen["V-30222333"]

    # Carlos: 100% -> Cumple con la normativa escolar
    assert alerta_carlos.porcentaje_asistencia == 100.0
    assert alerta_carlos.asistencias_efectivas == 4
    assert alerta_carlos.faltas_injustificadas == 0
    assert alerta_carlos.es_critico is False

    # Ana: 25.0% -> Estado crítico de reprobación según Art. 109 RGLOE
    assert alerta_ana.porcentaje_asistencia == 25.0
    assert alerta_ana.asistencias_efectivas == 1  # 1 'J'
    assert alerta_ana.faltas_injustificadas == 3   # 3 'A'
    assert alerta_ana.es_critico is True

    # El filtro de riesgo debe detectar exclusivamente a Ana
    alumnos_en_riesgo = AnalizadorEstadistico.detectar_riesgo(reporte_mensual)
    assert len(alumnos_en_riesgo) == 1
    assert alumnos_en_riesgo[0].id_estudiante == "V-30222333"

    # =========================================================================
    # FASE 5: EXPORTACIÓN REAL A PDF (REPORTLAB PLATYPUS)
    # =========================================================================
    exportador_pdf = ExportadorPDFReportLab()
    ruta_pdf_salida = str(tmp_path / "Reporte_Oficial_Asistencia_4to.pdf")

    encabezados_pdf = ["Fecha", "Cédula", "Estudiante", "Gen", "Materia", "ST", "Justificación", "% Asist."]
    filas_pdf = [
        [
            r.fecha,
            r.id_estudiante,
            r.nombre,
            r.genero,
            r.materia,
            r.estado,
            r.observacion or "-",
            f"{mapa_resumen[r.id_estudiante].porcentaje_asistencia:.1f}%"
        ]
        for r in reporte_mensual
    ]

    exito_pdf = exportador_pdf.exportar_tabla(
        titulo="REPORTE OFICIAL DE ASISTENCIA — 4TO AÑO SECCIÓN A",
        encabezados=encabezados_pdf,
        datos=filas_pdf,
        ruta_salida=ruta_pdf_salida
    )

    assert exito_pdf is True, "La exportación a PDF debe completarse con éxito."
    assert os.path.exists(ruta_pdf_salida), "El archivo PDF debe crearse físicamente en disco."
    assert os.path.getsize(ruta_pdf_salida) > 500, "El PDF generado debe contener datos legibles."

    with open(ruta_pdf_salida, "rb") as f_pdf:
        cabecera = f_pdf.read(4)
        assert cabecera == b"%PDF", "El documento debe poseer una cabecera binaria válida %PDF."

    # =========================================================================
    # FASE 6: LISTADOS CENTRALIZADOS Y PROMOCIÓN ANUAL EN CASCADA CON AUDITORÍA
    # =========================================================================
    repo_listados = RepositorioListadosSQLite(db)
    repo_promocion = RepositorioPromocionSQLite(db)

    # 6.1 Listados de Alumnos Activos
    nomina_alumnos = repo_listados.obtener_estudiantes_activos()
    assert len(nomina_alumnos) == 4
    for al in nomina_alumnos:
        assert al["grado"] == "4to AÑO"

    # 6.2 Censo previo por grado en Promoción
    censo_previo = repo_promocion.obtener_resumen_grados()
    mapa_censo = {c.id_grado: c.total_estudiantes for c in censo_previo}
    assert mapa_censo.get(4, 0) == 4
    assert mapa_censo.get(5, 0) == 0

    # 6.3 Autorización por Clave Maestra del Dominio
    # Rechazo con clave incorrecta
    with pytest.raises(PermissionError):
        ServicioPromocionDominio.validar_autorizacion("CLAVE_INCORRECTA")

    # Aprobación con clave maestra institucional válida
    assert ServicioPromocionDominio.validar_autorizacion("DIRECTOR2025") is True

    # 6.4 Ejecución de la Promoción en Cascada Inversa (4to -> 5to Año)
    resultado_promocion = repo_promocion.ejecutar_promocion_cascada(usuario_responsable="admin")
    assert resultado_promocion.exito is True
    assert resultado_promocion.total_promovidos == 4
    assert resultado_promocion.detalles_por_grado.get("4_a_5") == 4

    # 6.5 Verificación en BD: Los estudiantes ahora pertenecen a 5to Año (ID_GRADO = 5)
    conn = db.conectar()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM TBL_ESTUDIANTES WHERE ID_GRADO = 5 AND ESTADO_ACTIVO = 1")
    assert cur.fetchone()[0] == 4, "Los 4 alumnos deben haber sido promovidos a 5to Año."

    cur.execute("SELECT COUNT(*) FROM TBL_ESTUDIANTES WHERE ID_GRADO = 4 AND ESTADO_ACTIVO = 1")
    assert cur.fetchone()[0] == 0, "No deben quedar estudiantes en 4to Año tras la promoción."

    # 6.6 Verificación de TBL_AUDITORIA
    cur.execute(
        """
        SELECT USUARIO, MODULO, ACCION, DETALLES 
        FROM TBL_AUDITORIA 
        WHERE MODULO = 'PROMOCION_ANUAL'
        ORDER BY ID_AUDITORIA DESC LIMIT 1
        """
    )
    fila_auditoria = cur.fetchone()
    assert fila_auditoria is not None, "Debe existir un registro en TBL_AUDITORIA tras la promoción."
    assert fila_auditoria[0] == "admin"
    assert fila_auditoria[1] == "PROMOCION_ANUAL"
    assert fila_auditoria[2] == "EJECUTAR_CASCADA"
    assert "4to->5to: 4" in fila_auditoria[3]
