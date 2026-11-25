# -*- mode: python ; coding: utf-8 -*-
"""
Receta PyInstaller (--onedir) para Windows 10/11.
Empaqueta el Sistema de Asistencia Estudiantil 'Colinas del Llano' sin consola,
respetando RNF-02 (sin librerías pesadas) y RNF-07 (portabilidad offline).
"""

import os
from PyInstaller.utils.hooks import collect_submodules

SPEC_DIR = os.path.abspath(SPECPATH)
ROOT_DIR = os.path.abspath(os.path.join(SPEC_DIR, ".."))
ICON_PATH = os.path.join(SPEC_DIR, "icono_colegio.ico")
LOGO_PATH = os.path.join(ROOT_DIR, "LOGOLICEO.png")
LICENSE_PATH = os.path.join(ROOT_DIR, "LICENSE")
NOTICES_PATH = os.path.join(ROOT_DIR, "THIRD_PARTY_NOTICES.txt")

datas_empaquetado = [(LOGO_PATH, ".")]
for _archivo_legal in (LICENSE_PATH, NOTICES_PATH):
    if os.path.exists(_archivo_legal):
        datas_empaquetado.append((_archivo_legal, "."))

for _nombre_foto in ("foto_equipo.jpg", "foto_equipo.png", "foto_equipo.jpeg", "nosotros.jpeg", "nosotros.jpg"):
    _ruta_foto = os.path.join(ROOT_DIR, _nombre_foto)
    if os.path.exists(_ruta_foto):
        datas_empaquetado.append((_ruta_foto, "."))
        break

hidden_imports = [
    "babel.numbers",
    "PIL._tkinter_finder",
    "tkcalendar",
    "rutas_app",
    "db_conexion",
    "dominio",
    "puertos",
    "adaptadores",
    "reportlab.platypus",
    "reportlab.lib.pagesizes",
    "reportlab.lib.styles",
    "reportlab.lib.colors",
    "reportlab.graphics.barcode.common",
    "reportlab.graphics.barcode.code39",
    "reportlab.graphics.barcode.code93",
    "reportlab.graphics.barcode.code128",
    "reportlab.graphics.barcode.usps",
    "reportlab.graphics.barcode.usps4s",
    "reportlab.graphics.barcode.ecc200datamatrix",
]
hidden_imports += collect_submodules("dominio")
hidden_imports += collect_submodules("puertos")
hidden_imports += collect_submodules("adaptadores")

a = Analysis(
    [os.path.join(ROOT_DIR, "main.py")],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=datas_empaquetado,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "pytest",
        "IPython",
        "jupyter",
        "PyQt5",
        "PyQt6",
        "PySide6",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="sistema_escolar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH if os.path.exists(ICON_PATH) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ColinasDelLlano_Windows",
)
