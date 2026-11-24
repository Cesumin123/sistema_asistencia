# tests/test_expedientes_y_fichas.py
"""
Suite de pruebas integrales para la FASE A:
1. Migración idempotente en caliente sobre esquema existente.
2. Persistencia y CRUD de Profesor con profesión y fotografía.
3. Persistencia y CRUD de Estudiante con datos familiares y fotografía.
4. Adaptador portable GestorFotos (recorte 240x240, sanitización, portabilidad POSIX).
5. Generación real de Ficha Docente y Ficha Estudiantil en PDF con ReportLab.
"""

import os
import sqlite3
import pytest
from PIL import Image

from db_conexion import ConexionBD
from dominio.profesor import Profesor
from dominio.estudiante import Estudiante
from adaptadores.db.sqlite_profesor import SQLiteRepositorioProfesor
from adaptadores.db.sqlite_estudiante import RepositorioEstudianteSQLite
from adaptadores.documentos.gestor_fotos import GestorFotos
from adaptadores.documentos.pdf_reportes import ExportadorPDFReportLab


# ═════════════════════════════════════════════════════════════════════
# 1. MIGRACIÓN IDEMPOTENTE EN CALIENTE (db_conexion.py)
# ═════════════════════════════════════════════════════════════════════

def test_migracion_idempotente_esquema_existente(tmp_path):
    """
    Simula una base de datos existente previa a la FASE A (sin columnas nuevas),
    inserta datos previos, inicializa ConexionBD y verifica que:
    - Las nuevas columnas se agregan sin pérdida de datos.
    - La ejecución repetida no falla (idempotencia).
    """
    db_file = str(tmp_path / "colegio_legacy.db")

    # Crear base de datos simulando esquema antiguo sin las columnas de FASE A
    conn_raw = sqlite3.connect(db_file)
    cur = conn_raw.cursor()
    cur.execute("""
        CREATE TABLE TBL_PROFESORES (
            ID_PROFESOR INTEGER PRIMARY KEY AUTOINCREMENT,
            NOMBRE_COMPLETO TEXT NOT NULL,
            CEDULA TEXT UNIQUE NOT NULL,
            ESTADO_ACTIVO INTEGER DEFAULT 1
        );
    """)
    cur.execute("""
        CREATE TABLE TBL_GRADOS (
            ID_GRADO INTEGER PRIMARY KEY,
            DESCRIPCION TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE TBL_SECCIONES (
            ID_SECCION INTEGER PRIMARY KEY,
            DESCRIPCION TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE TBL_ESTUDIANTES (
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
            ESTADO_ACTIVO INTEGER DEFAULT 1
        );
    """)
    cur.execute("INSERT INTO TBL_GRADOS VALUES (4, '4to Año')")
    cur.execute("INSERT INTO TBL_SECCIONES VALUES (1, 'A')")

    # Insertar registros previos
    cur.execute(
        "INSERT INTO TBL_PROFESORES (NOMBRE_COMPLETO, CEDULA) VALUES (?, ?)",
        ("PROFESOR PREVIO", "V-11111111")
    )
    cur.execute(
        "INSERT INTO TBL_ESTUDIANTES (ID_ESTUDIANTE, NOMBRE, ID_GRADO, ID_SECCION) VALUES (?, ?, 4, 1)",
        ("V-22222222", "ESTUDIANTE PREVIO")
    )
    conn_raw.commit()
    conn_raw.close()

    # Inicializar ConexionBD sobre el archivo legacy (esto dispara _migrar_esquema)
    conexion = ConexionBD(ruta_db=db_file)
    conn_migrada = conexion.conectar()
    assert conn_migrada is not None

    cur_mig = conn_migrada.cursor()

    # Verificar que existen las columnas en TBL_PROFESORES
    cur_mig.execute("PRAGMA table_info(TBL_PROFESORES)")
    cols_prof = [c[1] for c in cur_mig.fetchall()]
    assert "PROFESION" in cols_prof
    assert "FOTO_PATH" in cols_prof

    # Verificar que existen las columnas en TBL_ESTUDIANTES
    cur_mig.execute("PRAGMA table_info(TBL_ESTUDIANTES)")
    cols_est = [c[1] for c in cur_mig.fetchall()]
    assert "NOMBRE_MADRE" in cols_est
    assert "TELEFONO_MADRE" in cols_est
    assert "NOMBRE_PADRE" in cols_est
    assert "TELEFONO_PADRE" in cols_est
    assert "FOTO_PATH" in cols_est
    assert "REPRESENTANTE" in cols_est  # Conservada intacta
    assert "TELEFONO" in cols_est       # Conservada intacta

    # Verificar que los registros previos permanecen intactos
    cur_mig.execute("SELECT NOMBRE_COMPLETO, CEDULA, PROFESION, FOTO_PATH FROM TBL_PROFESORES WHERE CEDULA = 'V-11111111'")
    fila_prof = cur_mig.fetchone()
    assert fila_prof[0] == "PROFESOR PREVIO"
    assert fila_prof[2] in ("", None)
    assert fila_prof[3] in ("", None)

    cur_mig.execute("SELECT ID_ESTUDIANTE, NOMBRE, NOMBRE_MADRE, FOTO_PATH FROM TBL_ESTUDIANTES WHERE ID_ESTUDIANTE = 'V-22222222'")
    fila_est = cur_mig.fetchone()
    assert fila_est[0] == "V-22222222"
    assert fila_est[1] == "ESTUDIANTE PREVIO"
    assert fila_est[2] in ("", None)

    conexion.cerrar()

    # Verificar IDEMPOTENCIA: reconectar de nuevo no debe lanzar excepción
    conn_segunda = conexion.conectar()
    assert conn_segunda is not None
    conexion.cerrar()


# ═════════════════════════════════════════════════════════════════════
# 2. PERSISTENCIA Y CRUD DE PROFESOR CON PROFESIÓN Y FOTO
# ═════════════════════════════════════════════════════════════════════

def test_crud_profesor_con_profesion_y_foto():
    """Valida guardado, actualización y lectura de Profesor con profesión y foto_path."""
    conexion = ConexionBD(":memory:")
    repo = SQLiteRepositorioProfesor(conexion)

    prof = Profesor(
        cedula="V-14567890",
        nombre_completo="Carlos Mendoza",
        profesion="Lcdo. en Matemáticas",
        foto_path="fotos/profesores/V_14567890.jpg"
    )
    prof.validar()
    assert repo.guardar(prof) is True
    assert prof.id_profesor is not None

    # Consultar por ID
    obtenido = repo.obtener_por_id(prof.id_profesor)
    assert obtenido is not None
    assert obtenido.cedula == "V-14567890"
    assert obtenido.nombre_completo == "CARLOS MENDOZA"
    assert obtenido.profesion == "LCDO. EN MATEMÁTICAS"
    assert obtenido.foto_path == "fotos/profesores/V_14567890.jpg"

    # Actualizar campos
    prof.profesion = "MSc. en Educación Matemática"
    prof.foto_path = "fotos/profesores/V_14567890_v2.jpg"
    assert repo.actualizar(prof) is True

    actualizado = repo.obtener_por_id(prof.id_profesor)
    assert actualizado.profesion == "MSC. EN EDUCACIÓN MATEMÁTICA"
    assert actualizado.foto_path == "fotos/profesores/V_14567890_v2.jpg"

    # Soft delete
    assert repo.eliminar(prof.id_profesor) is True
    activos = repo.obtener_activos()
    assert not any(p.cedula == "V-14567890" for p in activos)


# ═════════════════════════════════════════════════════════════════════
# 3. PERSISTENCIA Y CRUD DE ESTUDIANTE CON DATOS FAMILIARES Y FOTO
# ═════════════════════════════════════════════════════════════════════

def test_crud_estudiante_con_datos_familiares_y_foto():
    """Valida guardado, actualización y lectura de Estudiante con padre, madre y foto_path."""
    conexion = ConexionBD(":memory:")
    repo = RepositorioEstudianteSQLite(conexion)

    est = Estudiante(
        cedula="V-32100200",
        nombre="Valeria Sofia Gómez",
        fecha_nacimiento="15/04/2009",
        representante="María Gómez",
        telefono="0414-1112233",
        genero="F",
        escolaridad="Regular",
        turno="Mañana",
        condicion="Activo",
        id_grado=4,
        id_seccion=1,
        nombre_madre="María Gómez",
        telefono_madre="0414-1112233",
        nombre_padre="José Gómez",
        telefono_padre="0424-4445566",
        foto_path="fotos/estudiantes/V_32100200.jpg"
    )
    est.validar()
    assert repo.guardar(est) is True

    # Consultar por cédula
    obtenido = repo.obtener_por_cedula("V-32100200")
    assert obtenido is not None
    assert obtenido.cedula == "V-32100200"
    assert obtenido.nombre == "Valeria Sofia Gómez"
    assert obtenido.nombre_madre == "María Gómez"
    assert obtenido.telefono_madre == "0414-1112233"
    assert obtenido.nombre_padre == "José Gómez"
    assert obtenido.telefono_padre == "0424-4445566"
    assert obtenido.foto_path == "fotos/estudiantes/V_32100200.jpg"

    # Actualizar datos familiares
    est.nombre_madre = "María Auxiliadora Gómez"
    est.foto_path = "fotos/estudiantes/V_32100200_actualizada.jpg"
    assert repo.actualizar(est) is True

    actualizado = repo.obtener_por_cedula("V-32100200")
    assert actualizado.nombre_madre == "María Auxiliadora Gómez"
    assert actualizado.foto_path == "fotos/estudiantes/V_32100200_actualizada.jpg"


# ═════════════════════════════════════════════════════════════════════
# 4. ADAPTADOR GESTORFOTOS (PORTABILIDAD, SANITIZACIÓN Y RECORTE)
# ═════════════════════════════════════════════════════════════════════

def test_gestor_fotos_procesamiento_y_rutas(tmp_path):
    """Verifica que GestorFotos recorte a 240x240, use rutas POSIX y maneje errores defensivamente."""
    gestor = GestorFotos(directorio_base=str(tmp_path))

    # Sanitización de cédula
    assert gestor.sanitizar_cedula("V-30.123.456") == "V_30_123_456"
    assert gestor.sanitizar_cedula("E-88.999.000") == "E_88_999_000"
    assert gestor.sanitizar_cedula("") == "sin_identificacion"

    # Crear imagen sintética temporal (600x400 px RGB)
    ruta_img_origen = str(tmp_path / "foto_original.png")
    img_origen = Image.new("RGB", (600, 400), color=(30, 144, 255))
    img_origen.save(ruta_img_origen, "PNG")

    # Guardar foto para estudiante
    ruta_relativa = gestor.guardar_foto(ruta_img_origen, "estudiante", "V-30.123.456")
    assert ruta_relativa.startswith("fotos/estudiantes/")
    assert ruta_relativa.endswith(".jpg")
    assert "\\" not in ruta_relativa  # Debe ser ruta normalizada POSIX

    # Verificar que existe en disco en el directorio_base
    ruta_absoluta = gestor.resolver_ruta_absoluta(ruta_relativa)
    assert ruta_absoluta is not None
    assert os.path.exists(ruta_absoluta)

    # Validar dimensiones exactas del recorte
    with Image.open(ruta_absoluta) as img_guardada:
        assert img_guardada.size == (240, 240)
        assert img_guardada.format == "JPEG"

    # Verificar resolución de archivo inexistente
    assert gestor.resolver_ruta_absoluta("fotos/inexistente.jpg") is None
    assert gestor.resolver_ruta_absoluta("") is None

    # Verificar excepción ante archivo de origen que no existe
    with pytest.raises(FileNotFoundError):
        gestor.guardar_foto(str(tmp_path / "archivo_fantasma.jpg"), "profesor", "V-123")

    # Verificar eliminación
    assert gestor.eliminar_foto(ruta_relativa) is True
    assert not os.path.exists(ruta_absoluta)
    assert gestor.eliminar_foto("fotos/inexistente.jpg") is False


# ═════════════════════════════════════════════════════════════════════
# 5. GENERACIÓN REAL DE FICHAS TÉCNICAS EN PDF (REPORTLAB)
# ═════════════════════════════════════════════════════════════════════

def test_generar_ficha_docente_pdf(tmp_path):
    """Verifica la generación física del PDF de Ficha Técnica Docente con y sin foto."""
    gestor = GestorFotos(directorio_base=str(tmp_path))
    exportador = ExportadorPDFReportLab(gestor_fotos=gestor)

    # 1. Crear foto sintética para el docente
    ruta_img = str(tmp_path / "prof_foto.png")
    Image.new("RGB", (300, 300), color=(46, 204, 113)).save(ruta_img)
    foto_rel = gestor.guardar_foto(ruta_img, "profesor", "V-15999888")

    docente = Profesor(
        cedula="V-15999888",
        nombre_completo="Ana María Rodríguez",
        id_profesor=1,
        profesion="Lcda. en Castellano y Literatura",
        foto_path=foto_rel
    )

    materias = [
        {"materia": "Castellano", "grado": "4to Año", "seccion": "A"},
        {"materia": "Castellano", "grado": "4to Año", "seccion": "B"},
        {"materia": "Literatura Universal", "grado": "5to Año", "seccion": "A"},
    ]

    salida_pdf = str(tmp_path / "ficha_docente_prueba.pdf")
    pdf_generado = exportador.generar_ficha_docente(docente, materias, ruta_salida=salida_pdf)

    assert os.path.exists(pdf_generado)
    assert os.path.getsize(pdf_generado) > 1000

    # Validar cabecera binaria %PDF
    with open(pdf_generado, "rb") as f:
        cabecera = f.read(5)
        assert cabecera.startswith(b"%PDF-")


def test_generar_ficha_estudiante_pdf(tmp_path):
    """Verifica la generación física del PDF de Ficha Técnica Estudiantil con resumen y sin foto."""
    exportador = ExportadorPDFReportLab()  # Sin gestor_fotos explícito (fallback [ SIN FOTO ])

    estudiante = Estudiante(
        cedula="V-33444555",
        nombre="Gabriel Alejandro Pérez",
        fecha_nacimiento="10/11/2009",
        representante="Luisa Pérez",
        telefono="0412-5556677",
        genero="M",
        escolaridad="Regular",
        turno="Mañana",
        condicion="Activo",
        id_grado=4,
        id_seccion=1,
        nombre_madre="Luisa Pérez",
        telefono_madre="0412-5556677",
        nombre_padre="Carlos Pérez",
        telefono_padre="0416-8889900",
        foto_path=""  # Sin fotografía
    )

    resumen_asistencia = {
        "total_clases": 20,
        "presentes": 18,
        "ausencias": 1,
        "justificadas": 1,
        "porcentaje": 95.0,
        "en_riesgo": False
    }

    salida_pdf = str(tmp_path / "ficha_estudiante_prueba.pdf")
    pdf_generado = exportador.generar_ficha_estudiante(estudiante, resumen_asistencia, ruta_salida=salida_pdf)

    assert os.path.exists(pdf_generado)
    assert os.path.getsize(pdf_generado) > 1000

    # Validar cabecera binaria %PDF
    with open(pdf_generado, "rb") as f:
        cabecera = f.read(5)
        assert cabecera.startswith(b"%PDF-")
