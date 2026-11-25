#!/usr/bin/env bash
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")" && pwd)"
cd "$RAIZ"

PYINSTALLER_BIN="$RAIZ/.venv/bin/pyinstaller"
if [ ! -x "$PYINSTALLER_BIN" ]; then
    echo "Error: No se encontró $PYINSTALLER_BIN. Instálelo con: .venv/bin/pip install pyinstaller" >&2
    exit 1
fi

echo "[1/4] Compilando paquete Linux Mint (--onedir) con PyInstaller..."
"$PYINSTALLER_BIN" --noconfirm --clean "$RAIZ/empaquetado/linux.spec"

DIST_DIR="$RAIZ/dist/ColinasDelLlano_LinuxMint"
TAR_PATH="$RAIZ/dist/ColinasDelLlano_LinuxMint.tar.gz"

echo "[2/4] Copiando asistente Instalar_en_Mint.sh, logo y guía LEEME_INSTALACION.txt..."
cp -f "$RAIZ/empaquetado/Instalar_en_Mint.sh" "$DIST_DIR/Instalar_en_Mint.sh"
cp -f "$RAIZ/LOGOLICEO.png" "$DIST_DIR/LOGOLICEO.png"
chmod +x "$DIST_DIR/Instalar_en_Mint.sh" "$DIST_DIR/sistema_escolar"

cat > "$DIST_DIR/LEEME_INSTALACION.txt" << 'EOF'
SISTEMA DE ASISTENCIA ESTUDIANTIL — COMPLEJO EDUCATIVO "COLINAS DEL LLANO"
Paquete Portable / Instalador para Linux Mint 21.x / 22.x
=========================================================================

OPCION A — MODO PORTABLE (Ejecución directa / Pendrive):
1. Extraiga esta carpeta completa ("ColinasDelLlano_LinuxMint").
2. Ejecute "./sistema_escolar" (doble clic o desde terminal).
3. Los datos persistentes (sistema_escolar.db, fotos/ y memoria_emergencia.json)
   se guardarán automáticamente en esta misma carpeta junto al ejecutable.

OPCION B — INSTALACIÓN EN DOCUMENTOS CON ACCESO DIRECTO:
1. Ejecute "./Instalar_en_Mint.sh" (o doble clic -> Ejecutar).
2. El sistema se instalará en "~/Documentos/Sistema_Asistencia_Colinas"
   y creará accesos directos en el Escritorio y en el Menú de Aplicaciones.
3. Si ya tenía una instalación previa, sus datos (sistema_escolar.db, fotos/
   y memoria_emergencia.json) se conservarán intactos.
EOF

echo "[3/4] Empaquetando archivo comprimido dist/ColinasDelLlano_LinuxMint.tar.gz..."
rm -f "$TAR_PATH"
tar -czf "$TAR_PATH" -C "$RAIZ/dist" "ColinasDelLlano_LinuxMint"

echo "[4/4] Resumen de tamaños (MB):"
TAM_DIR_MB=$(du -sm "$DIST_DIR" | awk '{print $1}')
TAM_TAR_MB=$(du -sm "$TAR_PATH" | awk '{print $1}')
echo " - Carpeta --onedir ($DIST_DIR): ${TAM_DIR_MB} MB ($(du -sh "$DIST_DIR" | awk '{print $1}'))"
echo " - Archivo tar.gz   ($TAR_PATH): ${TAM_TAR_MB} MB ($(du -sh "$TAR_PATH" | awk '{print $1}'))"
