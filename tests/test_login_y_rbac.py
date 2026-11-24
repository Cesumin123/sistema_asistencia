# tests/test_login_y_rbac.py
"""
Pruebas Unitarias para Autenticación (CU-01), Control de Acceso por Roles (RBAC)
y Registro de Usuarios Protegido por Clave Maestra (RF-02).
"""

import pytest

from db_conexion import ConexionBD
from dominio.usuario import Usuario
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
from adaptadores.db.sqlite_usuario import SQLiteRepositorioUsuario


@pytest.fixture
def repo_usuario_db():
    """Inicializa la base de datos en memoria para pruebas de autenticación."""
    db = ConexionBD(ruta_db=":memory:")
    repo = SQLiteRepositorioUsuario(db)
    yield repo, db
    db.cerrar_definitivo()


# ============================================================================
# 1. PRUEBAS DE AUTENTICACIÓN (CP-01 y CP-02)
# ============================================================================

def test_autenticacion_exitosa_pbkdf2_cp01(repo_usuario_db):
    """
    CP-01: Autenticación exitosa con hash PBKDF2.
    Verifica que el repositorio autentique la contraseña plana contra el hash
    criptográfico seguro (salt$hash) y devuelva la entidad de Usuario activa.
    """
    repo, db = repo_usuario_db

    # Guardar usuario con contraseña en texto plano; el repositorio debe hashearla
    usuario = Usuario(
        nombre_completo="Coordinador de Prueba",
        username="coordinador1",
        password="PasswordSegura2026",
        rol="ASISTENTE"
    )
    usuario.validar()
    repo.guardar(usuario)

    # Verificar que en la base de datos la contraseña fue hasheada con salt$hash
    usuario_guardado = repo.obtener_por_username("coordinador1")
    assert usuario_guardado is not None
    assert "$" in usuario_guardado.password
    assert usuario_guardado.password != "PasswordSegura2026"

    # Autenticar con credenciales correctas
    autenticado = repo.autenticar("coordinador1", "PasswordSegura2026")
    assert autenticado is not None
    assert autenticado.username == "coordinador1"
    assert autenticado.rol == "ASISTENTE"
    assert autenticado.verificar_password("PasswordSegura2026") is True


def test_autenticacion_rechazo_clave_invalida_o_inactivo_cp02(repo_usuario_db):
    """
    CP-02: Rechazo ante credenciales inválidas o usuario inactivo.
    Verifica que:
    1. Contraseña incorrecta retorne None.
    2. Usuario inexistente retorne None.
    3. Usuario desactivado (ESTADO_ACTIVO = 0) no pueda iniciar sesión.
    """
    repo, db = repo_usuario_db

    usuario = Usuario(
        nombre_completo="Docente Temporal",
        username="docente_temp",
        password="ClaveDocente123",
        rol="DOCENTE"
    )
    repo.guardar(usuario)

    # 1. Contraseña incorrecta
    rechazado_clave = repo.autenticar("docente_temp", "ClaveErronea")
    assert rechazado_clave is None

    # 2. Usuario inexistente
    rechazado_inexistente = repo.autenticar("usuario_fantasma", "1234")
    assert rechazado_inexistente is None

    # 3. Usuario desactivado (Soft delete)
    usuario_activo = repo.obtener_por_username("docente_temp")
    assert usuario_activo is not None
    repo.desactivar(usuario_activo.id_usuario)

    # Intentar autenticar tras ser desactivado
    rechazado_inactivo = repo.autenticar("docente_temp", "ClaveDocente123")
    assert rechazado_inactivo is None
    assert repo.obtener_por_username("docente_temp") is None


# ============================================================================
# 2. PRUEBAS DE LA MATRIZ DE CONTROL DE ACCESO POR ROLES (RBAC)
# ============================================================================

def test_matriz_rbac_rol_admin():
    """ADMIN debe tener acceso irrestricto a todos los módulos."""
    permisos = obtener_permisos_rol("ADMIN")
    assert permisos[MODULO_ESTUDIANTES] is True
    assert permisos[MODULO_ACADEMICO] is True
    assert permisos[MODULO_ASISTENCIA] is True
    assert permisos[MODULO_LISTADOS] is True
    assert permisos[MODULO_REPORTES] is True
    assert permisos[MODULO_PROMOCION] is True
    assert permisos[MODULO_USUARIOS] is True

    for mod in [MODULO_ESTUDIANTES, MODULO_ACADEMICO, MODULO_ASISTENCIA,
                MODULO_LISTADOS, MODULO_REPORTES, MODULO_PROMOCION, MODULO_USUARIOS]:
        assert tiene_permiso("ADMIN", mod) is True
        assert validar_permiso("ADMIN", mod) is True


def test_matriz_rbac_rol_asistente():
    """
    ASISTENTE:
    - Autorizado: Estudiantes, Asistencia, Listados y Reportes PDF.
    - Denegado: Gestión Académica, Promoción Anual y Gestión de Usuarios.
    """
    permisos = obtener_permisos_rol("ASISTENTE")

    # Módulos permitidos
    assert permisos[MODULO_ESTUDIANTES] is True
    assert permisos[MODULO_ASISTENCIA] is True
    assert permisos[MODULO_LISTADOS] is True
    assert permisos[MODULO_REPORTES] is True

    # Módulos prohibidos
    assert permisos[MODULO_ACADEMICO] is False
    assert permisos[MODULO_PROMOCION] is False
    assert permisos[MODULO_USUARIOS] is False

    assert tiene_permiso("ASISTENTE", MODULO_PROMOCION) is False
    assert tiene_permiso("ASISTENTE", MODULO_USUARIOS) is False
    assert tiene_permiso("ASISTENTE", MODULO_ACADEMICO) is False

    with pytest.raises(PermissionError, match="Acceso denegado"):
        validar_permiso("ASISTENTE", MODULO_PROMOCION)

    with pytest.raises(PermissionError, match="Acceso denegado"):
        validar_permiso("ASISTENTE", MODULO_USUARIOS)


def test_matriz_rbac_rol_docente():
    """
    DOCENTE:
    - Autorizado: Asistencia y Listados (solo lectura).
    - Denegado: Estudiantes, Gestión Académica, Reportes PDF, Promoción Anual y Gestión de Usuarios.
    """
    permisos = obtener_permisos_rol("DOCENTE")

    # Módulos permitidos
    assert permisos[MODULO_ASISTENCIA] is True
    assert permisos[MODULO_LISTADOS] is True

    # Módulos prohibidos
    assert permisos[MODULO_ESTUDIANTES] is False
    assert permisos[MODULO_ACADEMICO] is False
    assert permisos[MODULO_REPORTES] is False
    assert permisos[MODULO_PROMOCION] is False
    assert permisos[MODULO_USUARIOS] is False

    assert tiene_permiso("DOCENTE", MODULO_ESTUDIANTES) is False
    assert tiene_permiso("DOCENTE", MODULO_REPORTES) is False
    assert tiene_permiso("DOCENTE", MODULO_PROMOCION) is False
    assert tiene_permiso("DOCENTE", MODULO_USUARIOS) is False

    with pytest.raises(PermissionError, match="Acceso denegado"):
        validar_permiso("DOCENTE", MODULO_ESTUDIANTES)

    with pytest.raises(PermissionError, match="Acceso denegado"):
        validar_permiso("DOCENTE", MODULO_REPORTES)


def test_matriz_rbac_rol_invalido():
    """Un rol no reconocido o vacío no debe tener acceso a ningún módulo."""
    permisos_vacio = obtener_permisos_rol("")
    assert all(permiso is False for permiso in permisos_vacio.values())

    permisos_desconocido = obtener_permisos_rol("INVITADO")
    assert all(permiso is False for permiso in permisos_desconocido.values())


# ============================================================================
# 3. PRUEBAS DE REGISTRO DE USUARIOS PROTEGIDO POR CLAVE MAESTRA (RF-02)
# ============================================================================

def test_registro_usuario_autorizado_con_clave_maestra(repo_usuario_db):
    """
    Verifica que la clave maestra correcta ('DIRECTOR2025') autorice el alta
    de un nuevo usuario y que éste se almacene correctamente con hash seguro.
    """
    repo, db = repo_usuario_db

    # 1. Autorización mediante dominio
    autorizado = ServicioPromocionDominio.validar_autorizacion("DIRECTOR2025")
    assert autorizado is True

    # 2. Guardar nuevo usuario asistente
    nuevo_asistente = Usuario(
        nombre_completo="Asistente Administrativo",
        username="asistente1",
        password="ClaveAsistente123",
        rol="ASISTENTE"
    )
    nuevo_asistente.validar()
    repo.guardar(nuevo_asistente)

    # 3. Comprobar existencia y autenticación
    guardado = repo.obtener_por_username("asistente1")
    assert guardado is not None
    assert guardado.rol == "ASISTENTE"
    assert repo.autenticar("asistente1", "ClaveAsistente123") is not None


def test_registro_usuario_rechazado_con_clave_maestra_incorrecta(repo_usuario_db):
    """
    Verifica que una clave maestra errada o vacía lance PermissionError
    impidiendo la autorización para el registro de nuevos usuarios.
    """
    with pytest.raises(PermissionError, match="Clave maestra administrativa inválida"):
        ServicioPromocionDominio.validar_autorizacion("CLAVE_ERRADA_123")

    with pytest.raises(PermissionError, match="Clave maestra administrativa inválida"):
        ServicioPromocionDominio.validar_autorizacion("")
