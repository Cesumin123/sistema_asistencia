@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ================================================================
echo  CONSTRUCCION DE PAQUETE WINDOWS - COLINAS DEL LLANO (--onedir)
echo ================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [1/6] Creando entorno virtual .venv...
    python -m venv .venv
    if errorlevel 1 exit /b 1
) else (
    echo [1/6] Usando entorno virtual .venv existente...
)

echo [2/6] Instalando dependencias y PyInstaller en .venv...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1

echo [3/6] Generando icono multi-resolucion empaquetado\icono_colegio.ico...
.venv\Scripts\python.exe empaquetado\generar_icono.py
if errorlevel 1 exit /b 1

echo [4/6] Compilando binario PyInstaller (--onedir)...
.venv\Scripts\pyinstaller.exe --noconfirm --clean empaquetado\windows.spec
if errorlevel 1 exit /b 1

echo [5/6] Generando paquete portable USB (dist\ColinasDelLlano_Windows_Portable.zip)...
if exist "dist\ColinasDelLlano_Windows_Portable.zip" del /f /q "dist\ColinasDelLlano_Windows_Portable.zip"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\ColinasDelLlano_Windows' -DestinationPath 'dist\ColinasDelLlano_Windows_Portable.zip' -Force"
if errorlevel 1 exit /b 1

echo [6/6] Buscando Inno Setup (ISCC.exe) para generar instalador...
set "ISCC_BIN="
where iscc >nul 2>&1
if %errorlevel%==0 (
    set "ISCC_BIN=iscc"
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC_BIN=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC_BIN=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if defined ISCC_BIN (
    echo Compilando instalador Inno Setup...
    "%ISCC_BIN%" empaquetado\instalar_windows.iss
    if errorlevel 1 exit /b 1
    echo Instalador generado en: dist\Instalar_ColinasDelLlano_Windows.exe
) else (
    echo Aviso: No se detecto ISCC.exe. Solo se genero el ZIP portable USB.
)

echo ================================================================
echo  COMPILACION WINDOWS COMPLETADA EXITOSAMENTE
echo ================================================================
exit /b 0
