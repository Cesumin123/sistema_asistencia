#!/usr/bin/env bash
set -euo pipefail

# Instalador local para Linux Mint 21.x / 22.x (sin root, hacia Documentos)
# Actualiza el binario y librerías internas preservando intactos BD, fotos y respaldo JSON.

ORIGEN="$(cd "$(dirname "$0")" && pwd)"

# Detectar carpeta de Documentos independientemente del idioma
DOCS_DIR=""
if command -v xdg-user-dir >/dev/null 2>&1; then
    DOCS_DIR="$(xdg-user-dir DOCUMENTS 2>/dev/null || true)"
fi
if [ -z "$DOCS_DIR" ] || [ ! -d "$DOCS_DIR" ]; then
    if [ -d "$HOME/Documentos" ]; then
        DOCS_DIR="$HOME/Documentos"
    elif [ -d "$HOME/Documents" ]; then
        DOCS_DIR="$HOME/Documents"
    else
        DOCS_DIR="$HOME/Documentos"
    fi
fi

# Detectar carpeta de Escritorio independientemente del idioma
DESKTOP_DIR=""
if command -v xdg-user-dir >/dev/null 2>&1; then
    DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
fi
if [ -z "$DESKTOP_DIR" ] || [ ! -d "$DESKTOP_DIR" ]; then
    if [ -d "$HOME/Escritorio" ]; then
        DESKTOP_DIR="$HOME/Escritorio"
    elif [ -d "$HOME/Desktop" ]; then
        DESKTOP_DIR="$HOME/Desktop"
    else
        DESKTOP_DIR=""
    fi
fi

DEST="$DOCS_DIR/Sistema_Asistencia_Colinas"
mkdir -p "$DEST"

if [ ! -f "$ORIGEN/sistema_escolar" ] || [ ! -d "$ORIGEN/_internal" ]; then
    MSG="No se encontraron 'sistema_escolar' y '_internal/' en $ORIGEN."
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --title="Error de Instalación" --text="$MSG" 2>/dev/null || echo "$MSG" >&2
    else
        echo "$MSG" >&2
    fi
    exit 1
fi

# Actualizar binario, librerías internas y logo preservando datos persistentes:
# sistema_escolar.db, sistema_escolar.db-wal, sistema_escolar.db-shm, fotos/ y memoria_emergencia.json
cp -f "$ORIGEN/sistema_escolar" "$DEST/sistema_escolar"
chmod +x "$DEST/sistema_escolar"

rm -rf "$DEST/_internal"
cp -a "$ORIGEN/_internal" "$DEST/_internal"

if [ -f "$ORIGEN/LOGOLICEO.png" ]; then
    cp -f "$ORIGEN/LOGOLICEO.png" "$DEST/LOGOLICEO.png"
fi

if [ -f "$ORIGEN/LEEME_INSTALACION.txt" ]; then
    cp -f "$ORIGEN/LEEME_INSTALACION.txt" "$DEST/LEEME_INSTALACION.txt"
fi

# Crear lanzadores .desktop (Escritorio y Menú de Aplicaciones)
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"

CONTENIDO_DESKTOP="[Desktop Entry]
Version=1.0
Type=Application
Name=Sistema de Asistencia Colinas del Llano
Comment=Gestión de Asistencia Estudiantil — Complejo Educativo Colinas del Llano
Exec=\"$DEST/sistema_escolar\"
Path=$DEST
Icon=$DEST/LOGOLICEO.png
Terminal=false
Categories=Education;Office;
StartupNotify=true
"

APP_DESKTOP_FILE="$APPS_DIR/Sistema_Asistencia_Colinas.desktop"
printf '%s' "$CONTENIDO_DESKTOP" > "$APP_DESKTOP_FILE"
chmod +x "$APP_DESKTOP_FILE"

if [ -n "$DESKTOP_DIR" ]; then
    mkdir -p "$DESKTOP_DIR"
    DESKTOP_FILE="$DESKTOP_DIR/Sistema_Asistencia_Colinas.desktop"
    printf '%s' "$CONTENIDO_DESKTOP" > "$DESKTOP_FILE"
    chmod +x "$DESKTOP_FILE"
    gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true
fi

MENSAJE_OK="Instalación completada exitosamente en:
$DEST

Sus datos existentes (sistema_escolar.db, fotos/ y memoria_emergencia.json) se mantienen intactos.
Ya puede abrir el sistema desde el acceso directo en el Escritorio o el Menú de Aplicaciones."

if command -v zenity >/dev/null 2>&1; then
    zenity --info --title="Colinas del Llano — Instalación Completada" --text="$MENSAJE_OK" 2>/dev/null || echo "$MENSAJE_OK"
else
    echo "$MENSAJE_OK"
fi
