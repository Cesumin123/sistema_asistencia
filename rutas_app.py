# rutas_app.py
"""
Módulo neutro de resolución de rutas portables (solo stdlib: os, sys).

Diseñado para funcionar de forma idéntica en desarrollo y empaquetado con PyInstaller 6+
(--onedir y --onefile) sin acoplar la capa UI ni la infraestructura a sqlite3.

Regla fundamental de portabilidad (RNF-07):
- Recursos estáticos de solo lectura (logos, assets): `obtener_ruta_recurso()` -> `_MEIPASS`.
- Datos persistentes de lectura/escritura (BD, fotos, respaldo JSON, reportes):
  `obtener_directorio_datos()` / `obtener_ruta_dato()` -> siempre junto al ejecutable,
  NUNCA dentro de `_MEIPASS` ni `_internal/`.
"""

import os
import sys


def _directorio_raiz_dev() -> str:
    """Retorna la raíz del proyecto en modo desarrollo."""
    return os.path.dirname(os.path.abspath(__file__))


def obtener_ruta_recurso(ruta_relativa: str) -> str:
    """
    Resuelve la ruta de un recurso de SOLO LECTURA empaquetado (ej. 'LOGOLICEO.png').

    - En binario PyInstaller (`sys.frozen == True` y `sys._MEIPASS` presente):
      resuelve dentro de `sys._MEIPASS`.
    - En desarrollo: resuelve respecto a la raíz del repositorio.
    """
    if getattr(sys, "frozen", False):
        base_meipass = getattr(sys, "_MEIPASS", None)
        if base_meipass:
            return os.path.join(base_meipass, ruta_relativa)
        return os.path.join(os.path.dirname(os.path.abspath(sys.executable)), ruta_relativa)
    return os.path.join(_directorio_raiz_dev(), ruta_relativa)


def obtener_directorio_datos() -> str:
    """
    Retorna el directorio persistente de LECTURA/ESCRITURA del sistema.

    - En binario PyInstaller (`sys.frozen == True`): directorio que contiene el ejecutable
      (junto al binario, nunca dentro de `_MEIPASS` / `_internal/`).
    - En desarrollo: raíz del proyecto.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return _directorio_raiz_dev()


def obtener_ruta_dato(ruta_relativa: str) -> str:
    """
    Resuelve una ruta persistente de LECTURA/ESCRITURA (BD, fotos/, JSON de respaldo)
    siempre dentro de `obtener_directorio_datos()`.
    """
    return os.path.join(obtener_directorio_datos(), ruta_relativa)
