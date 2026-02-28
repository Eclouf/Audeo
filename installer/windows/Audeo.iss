#define MyAppName "Audeo"
#define MyAppExeName "Audeo.exe"

; Update these 2 lines for each release (or generate this file during CI)
#define MyAppVersion "0.6.0"
#define MyAppPublisher "Eclouf - Audeo Developer"

; Repo root relative paths
#define DistDir "..\..\dist"
#define OutputDir "..\..\dist"

[Setup]
AppId={{C0E4A9A1-9E86-4B0B-8A74-9E3B0E0B6D6E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/Eclouf/Audeo
AppSupportURL=https://github.com/Eclouf/Audeo/issues
AppUpdatesURL=https://github.com/Eclouf/Audeo/releases
AppCopyright=Copyright © 2026 Eclouf
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename={#MyAppName}-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
