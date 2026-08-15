#define MyAppName "Nutri Clinic Pro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Nutri Clinic Pro"
#define MyAppExeName "Nutri Clinic Pro.exe"

[Setup]
AppId={{8F6D7614-4A52-4E20-9D35-6D58A9AD4B24}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Nutri Clinic Pro
DefaultGroupName={#MyAppName}
OutputDir=..\dist\installer
OutputBaseFilename=Nutri_Clinic_Pro_Setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\icone.png
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\Nutri Clinic Pro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName}"; Flags: nowait postinstall skipifsilent
