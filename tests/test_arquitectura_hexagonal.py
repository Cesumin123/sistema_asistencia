# tests/test_arquitectura_hexagonal.py
"""
Guardrail Arquitectónico Hexagonal (AST Static Analysis).

Inspecciona estáticamente el árbol de sintaxis abstracta (AST) de todos los archivos
Python del proyecto (excluyendo 'Sistema Legacy/' y entornos virtuales) para garantizar
el cumplimiento de los límites arquitectónicos del patrón Puertos y Adaptadores:

1. Capa de Dominio (dominio/):
   - Python puro.
   - PROHIBIDO importar: sqlite3, tkinter, tkcalendar, reportlab, adaptadores, db_conexion.

2. Capa de Puertos (puertos/):
   - Contratos e interfaces abstractas.
   - PROHIBIDO importar: sqlite3, tkinter, tkcalendar, reportlab, adaptadores, db_conexion.

3. Capa de UI (adaptadores/ui/):
   - Interfaces gráficas desacopladas de la persistencia directa.
   - PROHIBIDO importar: sqlite3, db_conexion (las dependencias deben ser inyectadas desde main.py).
"""

import os
import ast
from pathlib import Path
import pytest

RUTA_RAIZ = Path(__file__).resolve().parent.parent

DIRECTORIOS_IGNORADOS = {
    "Sistema Legacy",
    "Sistema_Legacy",
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".vscode",
}


def obtener_todos_los_archivos_py(subdirectorio: str) -> list[Path]:
    """Obtiene la lista de archivos .py dentro de un subdirectorio relativo a la raíz."""
    dir_objetivo = RUTA_RAIZ / subdirectorio
    if not dir_objetivo.exists():
        return []

    archivos = []
    for root, dirs, files in os.walk(dir_objetivo):
        # Excluir carpetas ignoradas
        dirs[:] = [d for d in dirs if d not in DIRECTORIOS_IGNORADOS]
        for f in files:
            if f.endswith(".py"):
                archivos.append(Path(root) / f)
    return archivos


def extraer_modulos_importados(ruta_archivo: Path) -> list[str]:
    """Analiza el código con ast y retorna los nombres de todos los módulos importados."""
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        arbol = ast.parse(f.read(), filename=str(ruta_archivo))

    modulos_importados = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                modulos_importados.append(alias.name)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.module:
                modulos_importados.append(nodo.module)

    return modulos_importados


# =============================================================================
# 1. GUARDRAIL: CAPA DE DOMINIO (dominio/)
# =============================================================================

MODULOS_PROHIBIDOS_EN_DOMINIO = [
    "sqlite3",
    "tkinter",
    "tkcalendar",
    "reportlab",
    "adaptadores",
    "db_conexion",
]


def test_arquitectura_dominio_puro_sin_infraestructura_ni_ui():
    """
    Ningún archivo en 'dominio/' puede depender de SQLite, Tkinter,
    generación de reportes PDF ni de la capa de Adaptadores.
    """
    archivos_dominio = obtener_todos_los_archivos_py("dominio")
    assert len(archivos_dominio) > 0, "Deben existir archivos en la capa de dominio."

    violaciones = []
    for archivo in archivos_dominio:
        importaciones = extraer_modulos_importados(archivo)
        for imp in importaciones:
            for prohibido in MODULOS_PROHIBIDOS_EN_DOMINIO:
                if imp == prohibido or imp.startswith(f"{prohibido}."):
                    violaciones.append(f"{archivo.name} importa '{imp}' (prohibido en dominio/)")

    assert len(violaciones) == 0, (
        f"Se encontraron violaciones arquitectónicas en dominio/:\n" + "\n".join(violaciones)
    )


# =============================================================================
# 2. GUARDRAIL: CAPA DE PUERTOS (puertos/)
# =============================================================================

MODULOS_PROHIBIDOS_EN_PUERTOS = [
    "sqlite3",
    "tkinter",
    "tkcalendar",
    "reportlab",
    "adaptadores",
    "db_conexion",
]


def test_arquitectura_puertos_sin_adaptadores_ni_sql():
    """
    Ningún archivo en 'puertos/' puede depender de SQLite, Tkinter ni Adaptadores.
    Los puertos solo deben depender de bibliotecas estándar y de 'dominio/'.
    """
    archivos_puertos = obtener_todos_los_archivos_py("puertos")
    assert len(archivos_puertos) > 0, "Deben existir archivos en la capa de puertos."

    violaciones = []
    for archivo in archivos_puertos:
        importaciones = extraer_modulos_importados(archivo)
        for imp in importaciones:
            for prohibido in MODULOS_PROHIBIDOS_EN_PUERTOS:
                if imp == prohibido or imp.startswith(f"{prohibido}."):
                    violaciones.append(f"{archivo.name} importa '{imp}' (prohibido en puertos/)")

    assert len(violaciones) == 0, (
        f"Se encontraron violaciones arquitectónicas en puertos/:\n" + "\n".join(violaciones)
    )


# =============================================================================
# 3. GUARDRAIL: CAPA DE PRESENTACIÓN / UI (adaptadores/ui/)
# =============================================================================

MODULOS_PROHIBIDOS_EN_UI = [
    "sqlite3",
    "db_conexion",
]


def test_arquitectura_ui_desacoplada_de_sql_directo():
    """
    Ningún archivo en 'adaptadores/ui/' puede importar sqlite3 ni db_conexion.
    Toda persistencia debe consumirse a través de los puertos/repositorios inyectados.
    """
    archivos_ui = obtener_todos_los_archivos_py("adaptadores/ui")
    assert len(archivos_ui) > 0, "Deben existir archivos en la capa adaptadores/ui/."

    violaciones = []
    for archivo in archivos_ui:
        importaciones = extraer_modulos_importados(archivo)
        for imp in importaciones:
            for prohibido in MODULOS_PROHIBIDOS_EN_UI:
                if imp == prohibido or imp.startswith(f"{prohibido}."):
                    violaciones.append(f"{archivo.name} importa '{imp}' (prohibido en adaptadores/ui/)")

    assert len(violaciones) == 0, (
        f"Se encontraron violaciones arquitectónicas en adaptadores/ui/:\n" + "\n".join(violaciones)
    )
