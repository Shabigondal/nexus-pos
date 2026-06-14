; ============================================================
;  Nexus POS & Inventory Control Workspace - Installer Script
;  Build with Inno Setup (https://jrsoftware.org/isinfo.php)
;
;  1. Run build_exe.bat first to generate dist\NexusPOS\
;  2. Open this file in Inno Setup Compiler (or right-click -> Compile)
;  3. Output: Output\NexusPOS_Setup.exe
; ============================================================

#define MyAppName "Nexus POS"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Nexus Industrial"
#define MyAppExeName "NexusPOS.exe"
#define MyAppURL "https://github.com/Shabigondal/nexus-pos"

[Setup]
AppId={{B6C2E7A1-8F3D-4C2E-9A1B-NEXUSPOS0001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Allow installing without admin rights (installs to user's local app data if needed)
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=NexusPOS_Setup
SetupIconFile=assets\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
; Copy everything PyInstaller produced
Source: "dist\NexusPOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove user-generated data when uninstalling is NOT done by default,
; so the user's database/backups survive a reinstall/update.
; (Uncomment below ONLY if you want a full clean wipe on uninstall.)
; Type: filesandordirs; Name: "{app}\database"
; Type: files; Name: "{app}\billing_system.db"
; Type: files; Name: "{app}\products.xlsx"
; Type: files; Name: "{app}\khata.xlsx"
