# tests/test_estudiante_y_usuario.py
import pytest
from db_conexion import ConexionBD
from dominio.usuario import Usuario
from dominio.estudiante import Estudiante
from adaptadores.db.sqlite_usuario import SQLiteRepositorioUsuario
from adaptadores.db.sqlite_estudiante import RepositorioEstudianteSQLite

@pytest.fixture
def db_memoria():
    """Crea una base de datos en memoria para pruebas aisladas."""
    db = ConexionBD(ruta_db=":memory:")
    db.conectar()
    yield db
    db.cerrar_definitivo()

# =========================================================================
# PRUEBAS DEL MÓDULO DE USUARIOS (DOMINIO + PERSISTENCIA + HASH PBKDF2)
# =========================================================================

def test_usuario_dominio_validaciones():
    """Valida reglas de negocio para usuarios."""
    # Nombre vacío
    with pytest.raises(ValueError, match="El nombre completo es obligatorio"):
        Usuario(nombre_completo="", username="admin", password="password", rol="ADMIN").validar()
    
    # Username corto (< 4)
    with pytest.raises(ValueError, match="al menos 4 caracteres"):
        Usuario(nombre_completo="Juan Perez", username="abc", password="password", rol="ADMIN").validar()
    
    # Contraseña corta (< 4)
    with pytest.raises(ValueError, match="al menos 4 caracteres"):
        Usuario(nombre_completo="Juan Perez", username="jperez", password="12", rol="ADMIN").validar()

def test_usuario_hashing_pbkdf2():
    """Verifica la generación y validación de hash seguro con salt."""
    hash_pwd = Usuario.generar_hash("clave_secreta_123")
    assert "$" in hash_pwd
    salt, hash_val = hash_pwd.split("$")
    assert len(salt) == 32  # 16 bytes en hex
    assert len(hash_val) == 64  # sha256 hex
    
    usuario = Usuario(nombre_completo="Docente Test", username="docente", password=hash_pwd, rol="DOCENTE")
    assert usuario.verificar_password("clave_secreta_123") is True
    assert usuario.verificar_password("clave_errada") is False
    assert usuario.verificar_password("") is False

def test_sqlite_usuario_persistencia_y_hashing(db_memoria):
    """Verifica que el repositorio SQLite guarde la clave hasheada y permita autenticación."""
    repo = SQLiteRepositorioUsuario(db_memoria)
    
    # 1. El admin por defecto creado por DDL debe autenticarse con '1234'
    admin_auth = repo.autenticar("admin", "1234")
    assert admin_auth is not None
    assert admin_auth.username == "admin"
    assert "$" in admin_auth.password  # Debe estar almacenada como hash, no '1234'
    
    # 2. Guardar un nuevo usuario pasando contraseña en texto plano
    nuevo = Usuario(nombre_completo="Coordinador", username="coord", password="mi_password_seguro", rol="ADMIN")
    repo.guardar(nuevo)
    
    # Verificar en la base de datos que NO se guardó en texto plano
    conn = db_memoria.conectar()
    cur = conn.cursor()
    cur.execute("SELECT PASSWORD FROM TBL_USUARIOS WHERE USERNAME = 'coord'")
    pwd_en_bd = cur.fetchone()[0]
    assert pwd_en_bd != "mi_password_seguro"
    assert "$" in pwd_en_bd
    
    # 3. Autenticación exitosa y fallida
    assert repo.autenticar("coord", "mi_password_seguro") is not None
    assert repo.autenticar("coord", "password_falso") is None
    assert repo.autenticar("usuario_inexistente", "clave") is None

def test_sqlite_usuario_soft_delete(db_memoria):
    """Verifica el borrado lógico con ESTADO_ACTIVO = 0."""
    repo = SQLiteRepositorioUsuario(db_memoria)
    user = Usuario(nombre_completo="Asistente", username="asistente", password="password123", rol="ASISTENTE")
    repo.guardar(user)
    
    activos = repo.obtener_activos()
    usernames_activos = [u.username for u in activos]
    assert "asistente" in usernames_activos
    
    # Desactivar
    repo.desactivar(user.id_usuario)
    
    # Ya no debe figurar entre los activos
    activos_post = repo.obtener_activos()
    usernames_post = [u.username for u in activos_post]
    assert "asistente" not in usernames_post
    
    # Tampoco debe autenticarse
    assert repo.autenticar("asistente", "password123") is None

def test_sqlite_usuario_username_duplicado(db_memoria):
    """Verifica que no se permita duplicar el nombre de usuario."""
    repo = SQLiteRepositorioUsuario(db_memoria)
    u1 = Usuario(nombre_completo="Usuario 1", username="unico", password="password1", rol="ASISTENTE")
    repo.guardar(u1)
    
    u2 = Usuario(nombre_completo="Usuario 2", username="unico", password="password2", rol="DOCENTE")
    with pytest.raises(ValueError, match="ya está en uso"):
        repo.guardar(u2)

# =========================================================================
# PRUEBAS DEL MÓDULO DE ESTUDIANTES (DOMINIO + PERSISTENCIA + SOFT-DELETE)
# =========================================================================

def test_estudiante_dominio_validaciones():
    """Valida reglas de datos obligatorios en Estudiante."""
    e = Estudiante(
        cedula="", nombre="Carlos", fecha_nacimiento="2008-01-01",
        representante="Maria", telefono="0414", genero="M",
        escolaridad="Regular", turno="Mañana", condicion="Activo",
        id_grado=4, id_seccion=1
    )
    with pytest.raises(ValueError, match="cédula .* es obligatoria"):
        e.validar()

def test_sqlite_estudiante_crud_y_soft_delete(db_memoria):
    """Verifica operaciones completas de estudiante con soft-delete."""
    repo = RepositorioEstudianteSQLite(db_memoria)
    
    estudiante = Estudiante(
        cedula="V-30111222", nombre="Estudiante Prueba", fecha_nacimiento="2008-05-15",
        representante="Representante Test", telefono="0412-1234567", genero="F",
        escolaridad="Regular", turno="Mañana", condicion="Activo",
        id_grado=4, id_seccion=1
    )
    
    # Guardar
    assert repo.guardar(estudiante) is True
    
    # Consultar por cédula
    obtenido = repo.obtener_por_cedula("V-30111222")
    assert obtenido is not None
    assert obtenido.nombre == "Estudiante Prueba"
    assert obtenido.genero == "F"
    
    # Actualizar
    obtenido.nombre = "Estudiante Nombre Actualizado"
    assert repo.actualizar(obtenido) is True
    assert repo.obtener_por_cedula("V-30111222").nombre == "Estudiante Nombre Actualizado"
    
    # Soft Delete
    assert repo.eliminar("V-30111222") is True
    assert repo.obtener_por_cedula("V-30111222") is None
    
    # Ya no aparece en lista de activos
    todos = repo.obtener_todos_activos()
    assert not any(e.cedula == "V-30111222" for e in todos)
    
    # Intentar guardar duplicado retorna False por IntegrityError
    assert repo.guardar(estudiante) is False
