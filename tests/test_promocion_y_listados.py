# tests/test_promocion_y_listados.py
"""
Pruebas Unitarias y de Integración para:
- Promoción Anual en Cascada Inversa (RF-16)
- Listados Centralizados (RF-13)
"""

import pytest
import sqlite3

from db_conexion import ConexionBD
from dominio.promocion import ServicioPromocionDominio, ResumenGradoPromocion
from adaptadores.db.sqlite_promocion import RepositorioPromocionSQLite
from adaptadores.db.sqlite_listados import RepositorioListadosSQLite


@pytest.fixture
def bd_promocion():
    """Inicializa una base de datos en memoria con grados, secciones y estudiantes de 1ro a 5to año."""
    db = ConexionBD(ruta_db=":memory:")
    conn = db.conectar()
    cursor = conn.cursor()

    # Estudiantes Activos en cada grado (1 al 5)
    cursor.execute("""
        INSERT INTO TBL_ESTUDIANTES 
        (ID_ESTUDIANTE, NOMBRE, FECHA_NACIMIENTO, REPRESENTANTE, TELEFONO, GENERO, ESCOLARIDAD, TURNO, CONDICION, ID_GRADO, ID_SECCION, ESTADO_ACTIVO)
        VALUES 
        ('V-101', 'Alumno de Primero', '2012-01-01', 'Rep 1', '0414', 'M', 'Regular', 'Mañana', 'Activo', 1, 1, 1),
        ('V-102', 'Alumno de Segundo', '2011-01-01', 'Rep 2', '0414', 'F', 'Regular', 'Mañana', 'Activo', 2, 1, 1),
        ('V-103', 'Alumno de Tercero', '2010-01-01', 'Rep 3', '0414', 'M', 'Regular', 'Mañana', 'Activo', 3, 1, 1),
        ('V-104', 'Alumno de Cuarto',  '2009-01-01', 'Rep 4', '0414', 'F', 'Regular', 'Mañana', 'Activo', 4, 1, 1),
        ('V-105', 'Alumno de Quinto',  '2008-01-01', 'Rep 5', '0414', 'M', 'Regular', 'Mañana', 'Activo', 5, 1, 1),
        ('V-INACTIVO-1', 'Alumno Inactivo de Primero', '2012-05-05', 'Rep X', '0414', 'M', 'Regular', 'Mañana', 'Activo', 1, 1, 0),
        ('V-INACTIVO-4', 'Alumno Inactivo de Cuarto',  '2009-05-05', 'Rep Y', '0414', 'F', 'Regular', 'Mañana', 'Activo', 4, 1, 0)
    """)

    # Profesores y materias para listados
    cursor.execute("INSERT INTO TBL_PROFESORES (ID_PROFESOR, CEDULA, NOMBRE_COMPLETO, ESTADO_ACTIVO) VALUES (1, 'V-DOC1', 'Profesor Activo', 1)")
    cursor.execute("INSERT INTO TBL_PROFESORES (ID_PROFESOR, CEDULA, NOMBRE_COMPLETO, ESTADO_ACTIVO) VALUES (2, 'V-DOC2', 'Profesor Inactivo', 0)")

    cursor.execute("INSERT INTO TBL_CLASES (ID_CLASE, NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES (1, 'Castellano', 1, 1, 1)")
    cursor.execute("INSERT INTO TBL_CLASES (ID_CLASE, NOMBRE_MATERIA, ID_PROFESOR, ID_GRADO, ID_SECCION) VALUES (2, 'Matemática', 1, 4, 1)")

    conn.commit()
    yield db
    db.cerrar_definitivo()


# ============================================================================
# 1. PRUEBAS DE PROMOCIÓN ANUAL EN CASCADA DESCENDENTE (RF-16)
# ============================================================================

def test_promocion_cascada_no_traslape_grados_y_respeta_inactivos(bd_promocion):
    """
    Verifica que:
    1. La cascada descendente promueva en orden inverso:
       - 1ro sube a 2do (NO a 6to por efecto avalancha)
       - 2do sube a 3ro
       - 3ro sube a 4to
       - 4to sube a 5to
       - 5to sube a 6to (GRADUADO)
    2. Los estudiantes inactivos (ESTADO_ACTIVO = 0) permanezcan intactos.
    3. Se registre el evento en TBL_AUDITORIA.
    """
    repo = RepositorioPromocionSQLite(bd_promocion)

    # 1. Verificar censo previo
    resumen_previo = repo.obtener_resumen_grados()
    mapa_previo = {r.id_grado: r.total_estudiantes for r in resumen_previo}
    assert mapa_previo[1] == 1
    assert mapa_previo[2] == 1
    assert mapa_previo[3] == 1
    assert mapa_previo[4] == 1
    assert mapa_previo[5] == 1

    # 2. Ejecutar la promoción en cascada
    resultado = repo.ejecutar_promocion_cascada(usuario_responsable="ADMINISTRADOR")
    assert resultado.exito is True
    assert resultado.total_promovidos == 5

    # 3. Verificar en la base de datos el grado de cada alumno
    conn = bd_promocion.conectar()
    cur = conn.cursor()

    def obtener_grado(id_est):
        cur.execute("SELECT ID_GRADO FROM TBL_ESTUDIANTES WHERE ID_ESTUDIANTE = ?", (id_est,))
        return cur.fetchone()[0]

    # Alumno que estaba en 1ro ahora debe estar en 2do (NO haber avanzado más)
    assert obtener_grado("V-101") == 2

    # Alumno que estaba en 2do ahora en 3ro
    assert obtener_grado("V-102") == 3

    # Alumno que estaba en 3ro ahora en 4to
    assert obtener_grado("V-103") == 4

    # Alumno que estaba en 4to ahora en 5to
    assert obtener_grado("V-104") == 5

    # Alumno que estaba en 5to ahora en 6to (GRADUADO)
    assert obtener_grado("V-105") == 6

    # Los inactivos NO deben haber cambiado de grado
    assert obtener_grado("V-INACTIVO-1") == 1
    assert obtener_grado("V-INACTIVO-4") == 4

    # 4. Verificar registro en TBL_AUDITORIA
    cur.execute("SELECT MODULO, ACCION, DETALLES FROM TBL_AUDITORIA WHERE MODULO = 'PROMOCION_ANUAL'")
    auditoria = cur.fetchone()
    assert auditoria is not None
    assert auditoria[0] == "PROMOCION_ANUAL"
    assert auditoria[1] == "EJECUTAR_CASCADA"
    assert "Total promovidos: 5" in auditoria[2]


def test_rechazo_clave_maestra_incorrecta(bd_promocion):
    """
    Verifica que el servicio de dominio rechace claves incorrectas, nulas o vacías
    con PermissionError, y que la base de datos no sufra modificaciones.
    """
    with pytest.raises(PermissionError, match="Clave maestra administrativa inválida"):
        ServicioPromocionDominio.validar_autorizacion("CLAVE_EQUIVOCADA")

    with pytest.raises(PermissionError, match="Clave maestra administrativa inválida"):
        ServicioPromocionDominio.validar_autorizacion("")

    with pytest.raises(PermissionError, match="Clave maestra administrativa inválida"):
        ServicioPromocionDominio.validar_autorizacion(None)

    # Clave correcta autoriza
    assert ServicioPromocionDominio.validar_autorizacion("DIRECTOR2025") is True

    # Comprobar que en BD los alumnos siguen en sus grados originales
    conn = bd_promocion.conectar()
    cur = conn.cursor()
    cur.execute("SELECT ID_GRADO FROM TBL_ESTUDIANTES WHERE ID_ESTUDIANTE = 'V-101'")
    assert cur.fetchone()[0] == 1


def test_rollback_atomico_ante_error_simulado(bd_promocion):
    """
    Verifica que si ocurre un fallo a mitad de la cascada descendente,
    la transacción se revierta completamente (ROLLBACK) y ningún grado
    quede alterado o en estado inconsistente.
    """
    repo = RepositorioPromocionSQLite(bd_promocion)
    conn = bd_promocion.conectar()
    cur = conn.cursor()

    # Creamos un TRIGGER temporal que aborta forzosamente cuando se intente actualizar hacia el grado 4
    # La cascada intenta: 5->6 (pasa), 4->5 (pasa), 3->4 (falla aquí y dispara ROLLBACK)
    cur.execute("""
        CREATE TRIGGER abortar_promocion_hacia_cuarto
        BEFORE UPDATE OF ID_GRADO ON TBL_ESTUDIANTES
        WHEN NEW.ID_GRADO = 4
        BEGIN
            SELECT RAISE(ABORT, 'Fallo simulado de hardware/integridad');
        END;
    """)
    conn.commit()

    with pytest.raises(RuntimeError, match="Fallo crítico durante la promoción en cascada. Se ejecutó Rollback"):
        repo.ejecutar_promocion_cascada("ADMIN")

    # Verificar que gracias al ROLLBACK, incluso los que iban antes (5to y 4to) fueron revertidos
    cur.execute("SELECT ID_GRADO FROM TBL_ESTUDIANTES WHERE ID_ESTUDIANTE = 'V-105'")
    assert cur.fetchone()[0] == 5  # No se quedó en 6

    cur.execute("SELECT ID_GRADO FROM TBL_ESTUDIANTES WHERE ID_ESTUDIANTE = 'V-104'")
    assert cur.fetchone()[0] == 4  # No se quedó en 5

    cur.execute("SELECT ID_GRADO FROM TBL_ESTUDIANTES WHERE ID_ESTUDIANTE = 'V-101'")
    assert cur.fetchone()[0] == 1


# ============================================================================
# 2. PRUEBAS DE LISTADOS CENTRALIZADOS (RF-13)
# ============================================================================

def test_listados_centralizados_consultas_consolidadas(bd_promocion):
    """
    Verifica que las consultas de listados centralizados:
    1. Retornen los consolidados de estudiantes activos (excluyendo inactivos).
    2. Retornen las materias con su profesor, grado y sección.
    3. Retornen la nómina de profesores activos (excluyendo inactivos).
    """
    repo_listados = RepositorioListadosSQLite(bd_promocion)

    # 1. Alumnos activos
    alumnos = repo_listados.obtener_estudiantes_activos()
    assert len(alumnos) == 5  # Solo los 5 activos, no los 2 inactivos
    cedulas = [a["cedula"] for a in alumnos]
    assert "V-101" in cedulas
    assert "V-105" in cedulas
    assert "V-INACTIVO-1" not in cedulas
    assert "V-INACTIVO-4" not in cedulas

    # Comprobar que incluye los campos consolidados
    primer_alumno = alumnos[0]
    assert "grado" in primer_alumno
    assert "seccion" in primer_alumno
    assert "nombre" in primer_alumno

    # 2. Materias consolidadas
    materias = repo_listados.obtener_materias_consolidadas()
    assert len(materias) == 2
    nombres_materias = [m["materia"] for m in materias]
    assert "Castellano" in nombres_materias
    assert "Matemática" in nombres_materias
    profesores_asignados = [m["profesor"] for m in materias]
    assert "Profesor Activo" in profesores_asignados

    # 3. Profesores activos
    profesores = repo_listados.obtener_profesores_activos()
    assert len(profesores) == 1
    assert profesores[0]["nombre"] == "Profesor Activo"
    assert profesores[0]["cedula"] == "V-DOC1"
