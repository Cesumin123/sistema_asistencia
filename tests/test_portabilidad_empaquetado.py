# tests/test_portabilidad_empaquetado.py
"""
Pruebas de portabilidad, resolución de rutas PyInstaller (--onedir/--onefile)
y validación estática de recetas de empaquetado Windows/Linux Mint y GitHub Actions.
"""

import ast
import os
import sys
from pathlib import Path
import pytest

import rutas_app
from db_conexion import ConexionBD
from adaptadores.documentos.gestor_fotos import GestorFotos
from adaptadores.respaldo.json_asistencia import RespaldoAsistenciaJSON
from adaptadores.ui.ui_menu_principal import resolver_ruta_recurso
from adaptadores.ui.ui_profesor import resolver_ruta_logo


RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


def test_rutas_app_solo_usa_stdlib():
    """Garantiza que rutas_app.py utilice únicamente módulos de stdlib (os, sys)."""
    ruta = RAIZ_PROYECTO / "rutas_app.py"
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    importados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                importados.add(alias.name.split(".")[0])
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module.split(".")[0])

    assert importados <= {"os", "sys"}


def test_resolucion_rutas_modo_frozen_pyinstaller_onedir(tmp_path, monkeypatch):
    """
    Simula un entorno PyInstaller 6+ --onedir con sys.frozen=True,
    sys._MEIPASS=.../_internal y sys.executable=.../app/sistema_escolar.
    Verifica separación estricta entre recursos de solo lectura y datos persistentes.
    """
    app_dir = tmp_path / "app"
    internal_dir = app_dir / "_internal"
    internal_dir.mkdir(parents=True)

    logo_interno = internal_dir / "LOGOLICEO.png"
    logo_interno.write_bytes(b"PNG_SIMULADO")
    exe_simulado = app_dir / "sistema_escolar"

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(internal_dir), raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_simulado), raising=False)

    # 1. Recursos estáticos apuntan a _internal (_MEIPASS)
    ruta_logo = rutas_app.obtener_ruta_recurso("LOGOLICEO.png")
    assert Path(ruta_logo) == logo_interno
    assert Path(resolver_ruta_recurso("LOGOLICEO.png")) == logo_interno
    assert Path(resolver_ruta_logo()) == logo_interno

    # 2. Datos persistentes apuntan junto al ejecutable (NUNCA dentro de _internal)
    assert Path(rutas_app.obtener_directorio_datos()) == app_dir
    ruta_db = Path(rutas_app.obtener_ruta_dato("sistema_escolar.db"))
    ruta_json = Path(rutas_app.obtener_ruta_dato("memoria_emergencia.json"))
    assert ruta_db == app_dir / "sistema_escolar.db"
    assert ruta_json == app_dir / "memoria_emergencia.json"
    assert "_internal" not in ruta_db.parts
    assert "_internal" not in ruta_json.parts

    # 3. Adaptadores y ConexionBD() heredan el directorio junto al binario
    db_defecto = ConexionBD()
    assert Path(db_defecto.ruta_db) == app_dir / "sistema_escolar.db"
    assert ConexionBD(":memory:").ruta_db == ":memory:"

    gestor = GestorFotos()
    assert Path(gestor.directorio_base) == app_dir
    assert "_internal" not in Path(gestor.directorio_base).parts

    respaldo = RespaldoAsistenciaJSON()
    assert Path(respaldo.ruta_archivo) == app_dir / "memoria_emergencia.json"


def test_resolucion_rutas_modo_desarrollo(monkeypatch):
    """En modo desarrollo (frozen=False), recursos y datos resuelven a la raíz."""
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    assert Path(rutas_app.obtener_directorio_datos()) == RAIZ_PROYECTO
    assert Path(rutas_app.obtener_ruta_recurso("LOGOLICEO.png")) == RAIZ_PROYECTO / "LOGOLICEO.png"
    assert Path(rutas_app.obtener_ruta_dato("sistema_escolar.db")) == RAIZ_PROYECTO / "sistema_escolar.db"
    assert Path(ConexionBD().ruta_db) == RAIZ_PROYECTO / "sistema_escolar.db"
    assert Path(GestorFotos().directorio_base) == RAIZ_PROYECTO
    assert Path(RespaldoAsistenciaJSON().ruta_archivo) == RAIZ_PROYECTO / "memoria_emergencia.json"


def test_validacion_estatica_archivos_empaquetado_gitignore_y_workflow():
    """Verifica existencia y reglas críticas de empaquetado, .gitignore y GitHub Actions."""
    # 1. .gitignore completo para evitar ruido en GitHub Desktop
    gitignore = (RAIZ_PROYECTO / ".gitignore").read_text(encoding="utf-8")
    for entrada in (
        "build/",
        "dist/",
        "empaquetado/icono_colegio.ico",
        "*.db",
        "*.db-wal",
        "*.db-shm",
        "fotos/",
        "memoria_emergencia.json",
    ):
        assert entrada in gitignore, f"Falta '{entrada}' en .gitignore"

    # 2. Archivos requeridos existen
    archivos_requeridos = [
        RAIZ_PROYECTO / "rutas_app.py",
        RAIZ_PROYECTO / "LOGOLICEO.png",
        RAIZ_PROYECTO / "construir_windows.bat",
        RAIZ_PROYECTO / "construir_linux.sh",
        RAIZ_PROYECTO / "empaquetado" / "generar_icono.py",
        RAIZ_PROYECTO / "empaquetado" / "windows.spec",
        RAIZ_PROYECTO / "empaquetado" / "instalar_windows.iss",
        RAIZ_PROYECTO / "empaquetado" / "linux.spec",
        RAIZ_PROYECTO / "empaquetado" / "Instalar_en_Mint.sh",
        RAIZ_PROYECTO / ".github" / "workflows" / "build_releases.yml",
    ]
    for archivo in archivos_requeridos:
        assert archivo.exists(), f"Archivo requerido no existe: {archivo}"

    # 3. Permisos de ejecución en scripts Linux
    assert os.access(RAIZ_PROYECTO / "construir_linux.sh", os.X_OK)
    assert os.access(RAIZ_PROYECTO / "empaquetado" / "Instalar_en_Mint.sh", os.X_OK)

    # 4. Recetas PyInstaller (.spec)
    for spec_nombre, dist_nombre in (
        ("windows.spec", "ColinasDelLlano_Windows"),
        ("linux.spec", "ColinasDelLlano_LinuxMint"),
    ):
        contenido_spec = (RAIZ_PROYECTO / "empaquetado" / spec_nombre).read_text(encoding="utf-8")
        assert "exclude_binaries=True" in contenido_spec
        assert f'name="{dist_nombre}"' in contenido_spec
        assert "console=False" in contenido_spec
        assert "upx=False" in contenido_spec
        assert "LOGOLICEO.png" in contenido_spec
        assert "babel.numbers" in contenido_spec
        assert "PIL._tkinter_finder" in contenido_spec
        assert "tkcalendar" in contenido_spec
        assert "reportlab" in contenido_spec
        for pesado in ("matplotlib", "numpy", "pandas", "scipy"):
            assert f'"{pesado}"' in contenido_spec

    # 5. Inno Setup Windows
    iss = (RAIZ_PROYECTO / "empaquetado" / "instalar_windows.iss").read_text(encoding="utf-8")
    assert "PrivilegesRequired=lowest" in iss
    assert r"{userdocs}\Sistema_Asistencia_Colinas" in iss
    assert "Spanish.isl" in iss
    assert "sistema_escolar.db" in iss
    assert "memoria_emergencia.json" in iss
    assert r"{autodesktop}" in iss

    # 6. Script Linux Mint
    mint_sh = (RAIZ_PROYECTO / "empaquetado" / "Instalar_en_Mint.sh").read_text(encoding="utf-8")
    assert "xdg-user-dir DOCUMENTS" in mint_sh
    assert "xdg-user-dir DESKTOP" in mint_sh
    assert "Sistema_Asistencia_Colinas" in mint_sh
    assert "Terminal=false" in mint_sh
    assert "LOGOLICEO.png" in mint_sh

    # 7. Pipeline GitHub Actions
    wf = (RAIZ_PROYECTO / ".github" / "workflows" / "build_releases.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in wf
    assert "feat/integracion-agente" in wf
    assert "main" in wf
    assert "windows-latest" in wf
    assert "ubuntu-22.04" in wf
    assert "ColinasDelLlano_Windows_Portable.zip" in wf
    assert "Instalar_ColinasDelLlano_Windows.exe" in wf
    assert "ColinasDelLlano_LinuxMint.tar.gz" in wf
