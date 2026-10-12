; ============================================================
;  Internet Doctor - Windows installer script (Inno Setup 6)
;  Build:  ISCC.exe installer.iss   ->  dist\InternetDoctor-Setup-1.1.0.exe
;  Requires dist\InternetDoctor.exe (built by build-exe.bat or GitHub Actions)
; ============================================================

#define MyAppName "Internet Doctor"
#define MyAppVersion "1.1.0"
#define MyAppExeName "InternetDoctor.exe"

[Setup]
AppId={{7C1B6E9A-4F2D-4B8E-9A61-D0C7155BEEF1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=021hk
DefaultDirName={autopf}\Internet Doctor
DefaultGroupName=Internet Doctor
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=InternetDoctor-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=assets\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; \
    GroupDescription: "Shortcuts:"
Name: "autostart"; Description: "Start Internet Doctor when Windows starts"; \
    GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Internet Doctor"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall Internet Doctor"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Internet Doctor"; Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "InternetDoctor"; \
    ValueData: """{app}\{#MyAppExeName}"""; \
    Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,Internet Doctor}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\InternetDoctor"
