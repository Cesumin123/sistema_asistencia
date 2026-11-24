# dominio/permisos.py
"""
Núcleo de Dominio: Control de Acceso Basado en Roles (RBAC).
Define las reglas de negocio puras para la autorización y permisos por módulo
según el estándar del Complejo Educativo 'Colinas del Llano'.
"""

from typing import Dict, Set

# Constantes de Módulos del Sistema
MODULO_ESTUDIANTES = "estudiantes"
MODULO_ACADEMICO = "academico"
MODULO_ASISTENCIA = "asistencia"
MODULO_LISTADOS = "listados"
MODULO_REPORTES = "reportes"
MODULO_ESTADISTICAS = "estadisticas"
MODULO_PROMOCION = "promocion"
MODULO_USUARIOS = "usuarios"

TODOS_LOS_MODULOS = {
    MODULO_ESTUDIANTES,
    MODULO_ACADEMICO,
    MODULO_ASISTENCIA,
    MODULO_LISTADOS,
    MODULO_REPORTES,
    MODULO_ESTADISTICAS,
    MODULO_PROMOCION,
    MODULO_USUARIOS
}

# Matriz Oficial de Permisos por Rol (AGENTS.md)
# - ADMIN: acceso total a todos los módulos.
# - ASISTENTE: acceso a Estudiantes, Asistencia, Listados, Reportes PDF y Estadísticas.
#              Denegado: Gestión Académica, Promoción Anual y Gestión de Usuarios.
# - DOCENTE: acceso a Asistencia y Listados (solo lectura).
#            Denegado: Estudiantes, Gestión Académica, Reportes PDF, Estadísticas, Promoción Anual y Gestión de Usuarios.
MATRIZ_PERMISOS_ROLES: Dict[str, Set[str]] = {
    "ADMIN": {
        MODULO_ESTUDIANTES,
        MODULO_ACADEMICO,
        MODULO_ASISTENCIA,
        MODULO_LISTADOS,
        MODULO_REPORTES,
        MODULO_ESTADISTICAS,
        MODULO_PROMOCION,
        MODULO_USUARIOS,
    },
    "ASISTENTE": {
        MODULO_ESTUDIANTES,
        MODULO_ASISTENCIA,
        MODULO_LISTADOS,
        MODULO_REPORTES,
        MODULO_ESTADISTICAS,
    },
    "DOCENTE": {
        MODULO_ASISTENCIA,
        MODULO_LISTADOS,
    },
}


def normalizar_rol(rol: str) -> str:
    """Normaliza la cadena del rol eliminando espacios y convirtiendo a mayúsculas."""
    if not rol:
        return ""
    return str(rol).strip().upper()


def obtener_permisos_rol(rol: str) -> Dict[str, bool]:
    """
    Retorna un diccionario indicando True/False para cada módulo del sistema
    según el rol proporcionado.
    """
    rol_norm = normalizar_rol(rol)
    modulos_autorizados = MATRIZ_PERMISOS_ROLES.get(rol_norm, set())

    return {
        modulo: (modulo in modulos_autorizados)
        for modulo in TODOS_LOS_MODULOS
    }


def tiene_permiso(rol: str, modulo: str) -> bool:
    """
    Verifica si un rol tiene autorización para acceder a un módulo específico.
    """
    rol_norm = normalizar_rol(rol)
    modulo_norm = str(modulo).strip().lower()
    modulos_autorizados = MATRIZ_PERMISOS_ROLES.get(rol_norm, set())
    return modulo_norm in modulos_autorizados


def validar_permiso(rol: str, modulo: str) -> bool:
    """
    Valida el permiso de un rol para un módulo.
    Lanza PermissionError si el acceso está restringido.
    """
    if not tiene_permiso(rol, modulo):
        raise PermissionError(
            f"Acceso denegado: El rol '{rol}' no tiene permisos para acceder al módulo '{modulo}'."
        )
    return True
