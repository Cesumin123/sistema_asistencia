# tests/test_profesor_y_clase.py
"""
Pruebas Unitarias y de Integración para Profesores y Clases (RF-07 y RF-08).

Cubre:
1. Validaciones de dominio en Profesor y Clase (campos vacíos, formatos inválidos, restricciones).
2. Persistencia en SQLiteRepositorioProfesor: inserción, unicidad de cédula, actualización y borrado lógico.
3. Persistencia en SQLiteRepositorioClase: asignación de una materia a múltiples secciones en lote,
   listados y verificación de integridad de relaciones con profesor, grado y sección.
"""

import pytest
from db_conexion import ConexionBD
from dominio.profesor import Profesor
from dominio.clase import Clase
from adaptadores.db.sqlite_profesor import SQLiteRepositorioProfesor
from adaptadores.db.sqlite_clase import SQLiteRepositorioClase


@pytest.fixture
def bd_profesor_clase():
    """Inicializa una base de datos SQLite en memoria para pruebas de Profesor y Clase."""
    db = ConexionBD(ruta_db=":memory:")
    yield db
    db.cerrar_definitivo()


# =============================================================================
# 1. PRUEBAS DE DOMINIO: PROFESOR
# =============================================================================

def test_profesor_dominio_valido():
    """Un profesor con cédula y nombre completos debe crearse y validarse sin errores."""
    prof = Profesor(cedula="V-12345678", nombre_completo="Carlos Alberto Mendoza")
    prof.validar()
    assert prof.cedula == "V-12345678"
    assert prof.nombre_completo == "CARLOS ALBERTO MENDOZA"
    assert prof.estado_activo == 1


@pytest.mark.parametrize("cedula_invalida", ["", "   ", None, "12"])
def test_profesor_dominio_cedula_invalida(cedula_invalida):
    """Cédula vacía o menor a 4 caracteres debe lanzar ValueError."""
    prof = Profesor(cedula=cedula_invalida, nombre_completo="Profesor Válido")
    with pytest.raises(ValueError, match="cédula"):
        prof.validar()


@pytest.mark.parametrize("nombre_invalido", ["", "  ", None, "AB"])
def test_profesor_dominio_nombre_invalido(nombre_invalido):
    """Nombre vacío o menor a 3 caracteres debe lanzar ValueError."""
    prof = Profesor(cedula="V-99887766", nombre_completo=nombre_invalido)
    with pytest.raises(ValueError, match="nombre"):
        prof.validar()


# =============================================================================
# 2. PRUEBAS DE DOMINIO: CLASE
# =============================================================================

def test_clase_dominio_valida():
    """Una clase con materia, profesor, grado y sección válidos debe validar correctamente."""
    clase = Clase(nombre_materia="Matemáticas", id_profesor=1, id_grado=4, id_seccion=1)
    clase.validar()
    assert clase.nombre_materia == "MATEMÁTICAS"
    assert clase.id_profesor == 1
    assert clase.id_grado == 4
    assert clase.id_seccion == 1


@pytest.mark.parametrize("materia_invalida", ["", "  ", None, "M", "AB"])
def test_clase_dominio_materia_invalida(materia_invalida):
    """Nombre de materia vacío o menor a 3 caracteres debe lanzar ValueError."""
    clase = Clase(nombre_materia=materia_invalida, id_profesor=1, id_grado=4, id_seccion=1)
    with pytest.raises(ValueError, match="materia"):
        clase.validar()


@pytest.mark.parametrize("id_prof_inv", [0, -1, None, "1"])
def test_clase_dominio_profesor_invalido(id_prof_inv):
    """ID de profesor inválido debe lanzar ValueError."""
    clase = Clase(nombre_materia="Física", id_profesor=id_prof_inv, id_grado=4, id_seccion=1)
    with pytest.raises(ValueError, match="profesor"):
        clase.validar()


@pytest.mark.parametrize("id_grado_inv", [0, -5, None])
def test_clase_dominio_grado_invalido(id_grado_inv):
    """ID de grado inválido debe lanzar ValueError."""
    clase = Clase(nombre_materia="Química", id_profesor=1, id_grado=id_grado_inv, id_seccion=1)
    with pytest.raises(ValueError, match="grado"):
        clase.validar()


@pytest.mark.parametrize("id_sec_inv", [0, -2, None])
def test_clase_dominio_seccion_invalida(id_sec_inv):
    """ID de sección inválido debe lanzar ValueError."""
    clase = Clase(nombre_materia="Biología", id_profesor=1, id_grado=4, id_seccion=id_sec_inv)
    with pytest.raises(ValueError, match="sección"):
        clase.validar()


# =============================================================================
# 3. PRUEBAS DE PERSISTENCIA: SQLITE REPOSITORIO PROFESOR
# =============================================================================

def test_sqlite_profesor_guardar_y_obtener(bd_profesor_clase):
    """Verifica inserción exitosa y consulta de profesores activos."""
    repo = SQLiteRepositorioProfesor(bd_profesor_clase)

    prof = Profesor(cedula="V-10203040", nombre_completo="Elena Rivas")
    assert repo.guardar(prof) is True
    assert prof.id_profesor is not None

    todos = repo.obtener_todos()
    assert len(todos) == 1
    assert todos[0].cedula == "V-10203040"
    assert todos[0].nombre_completo == "ELENA RIVAS"
    assert todos[0].estado_activo == 1


def test_sqlite_profesor_rechazo_cedula_duplicada(bd_profesor_clase):
    """No se permite registrar dos profesores con la misma cédula (IntegrityError -> ValueError)."""
    repo = SQLiteRepositorioProfesor(bd_profesor_clase)

    prof1 = Profesor(cedula="V-20304050", nombre_completo="Profesor Uno")
    repo.guardar(prof1)

    prof2 = Profesor(cedula="V-20304050", nombre_completo="Profesor Dos")
    with pytest.raises(ValueError, match="ya se encuentra registrada"):
        repo.guardar(prof2)


def test_sqlite_profesor_actualizar(bd_profesor_clase):
    """Permite modificar los datos de un profesor existente."""
    repo = SQLiteRepositorioProfesor(bd_profesor_clase)

    prof = Profesor(cedula="V-30405060", nombre_completo="Nombre Original")
    repo.guardar(prof)

    prof.nombre_completo = "NOMBRE MODIFICADO"
    assert repo.actualizar(prof) is True

    todos = repo.obtener_todos()
    assert todos[0].nombre_completo == "NOMBRE MODIFICADO"


def test_sqlite_profesor_borrado_logico(bd_profesor_clase):
    """El borrado debe ser lógico (ESTADO_ACTIVO = 0), conservando el historial."""
    repo = SQLiteRepositorioProfesor(bd_profesor_clase)

    prof = Profesor(cedula="V-40506070", nombre_completo="Docente A Desactivar")
    repo.guardar(prof)

    # Desactivar por ID
    assert repo.eliminar(prof.id_profesor) is True

    # obtener_activos no debe incluirlo
    activos = repo.obtener_activos()
    assert len(activos) == 0

    # obtener_todos sí lo conserva para historial referencial
    todos = repo.obtener_todos()
    assert len(todos) == 1
    assert todos[0].estado_activo == 0


# =============================================================================
# 4. PRUEBAS DE PERSISTENCIA: SQLITE REPOSITORIO CLASE
# =============================================================================

def test_sqlite_clase_guardar_lote_multiples_secciones(bd_profesor_clase):
    """
    Verifica la asignación de una misma materia a múltiples secciones (A, B, C)
    simultáneamente en una única transacción atómica.
    """
    repo_prof = SQLiteRepositorioProfesor(bd_profesor_clase)
    repo_clase = SQLiteRepositorioClase(bd_profesor_clase)

    # Crear profesor titular
    prof = Profesor(cedula="V-50607080", nombre_completo="Prof. Catedrático")
    repo_prof.guardar(prof)
    id_prof = prof.id_profesor

    # Crear la materia 'HISTORIA DE VENEZUELA' para 4to Año secciones A (1), B (2) y C (3)
    clases_lote = [
        Clase(nombre_materia="HISTORIA DE VENEZUELA", id_profesor=id_prof, id_grado=4, id_seccion=1),
        Clase(nombre_materia="HISTORIA DE VENEZUELA", id_profesor=id_prof, id_grado=4, id_seccion=2),
        Clase(nombre_materia="HISTORIA DE VENEZUELA", id_profesor=id_prof, id_grado=4, id_seccion=3),
    ]

    repo_clase.guardar_lote(clases_lote)

    # Verificar consultas
    disponibles = repo_clase.obtener_clases_disponibles()
    assert len(disponibles) == 3

    nombres_clases = [d[1] for d in disponibles]
    assert any("HISTORIA DE VENEZUELA - 4to AÑO A" in n for n in nombres_clases)
    assert any("HISTORIA DE VENEZUELA - 4to AÑO B" in n for n in nombres_clases)
    assert any("HISTORIA DE VENEZUELA - 4to AÑO C" in n for n in nombres_clases)


def test_sqlite_clase_obtener_grados_y_secciones(bd_profesor_clase):
    """Verifica que el repositorio de clases obtenga los catálogos del DDL inicial."""
    repo_clase = SQLiteRepositorioClase(bd_profesor_clase)

    grados = repo_clase.obtener_grados()
    # Grados 1 al 5 (el grado 6 es GRADUADO y se excluye de asignación de materias)
    assert len(grados) == 5
    assert grados[0][1] == "1er AÑO"
    assert grados[4][1] == "5to AÑO"

    secciones = repo_clase.obtener_secciones()
    assert len(secciones) >= 5  # A, B, C, D, E iniciales
