; Script de Instalador Inno Setup 6 — Sistema de Asistencia Colinas del Llano
; Instalación sin privilegios de administrador en Documentos del usuario.

[Setup]
AppName=Sistema de Asistencia Colinas del Llano
AppVersion=1.0.0
AppPublisher=Complejo Educativo Colinas del Llano
DefaultDirName={userdocs}\Sistema_Asistencia_Colinas
DefaultGroupName=Sistema de Asistencia Colinas del Llano
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Instalar_ColinasDelLlano_Windows
SetupIconFile=icono_colegio.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Copia aplicación y dependencias preservando intactos BD, fotos y respaldo JSON si existen en destino
Source: "..\dist\ColinasDelLlano_Windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "sistema_escolar.db,sistema_escolar.db-wal,sistema_escolar.db-shm,fotos\*,memoria_emergencia.json"

[Icons]
Name: "{group}\Sistema de Asistencia Colinas del Llano"; Filename: "{app}\sistema_escolar.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Sistema de Asistencia Colinas del Llano"; Filename: "{app}\sistema_escolar.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\sistema_escolar.exe"; Description: "{cm:LaunchProgram,Sistema de Asistencia Colinas del Llano}"; Flags: nowait postinstall skipifsilent
