; Inno Setup script for Philosopher's Quest
; Build: open this file in Inno Setup Compiler and click Compile (F9),
;        or run:  ISCC.exe installer\setup.iss
; Output: installer\PhilosophersQuest_Setup.exe

#define AppName      "Philosopher's Quest"
#define AppVersion   "1.9.1"
#define AppPublisher "Dad"
#define AppExeName   "PhilosophersQuest.exe"
#define BundleDir    "..\dist\PhilosophersQuest"
#define IconFile     "..\assets\icon.ico"

[Setup]
; AppId must stay constant across versions — Inno uses it to detect existing installs
AppId={{A7C3F2E1-8D4B-4A9F-B2E6-1C3D5F7A9B0E}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=

; Install destination
DefaultDirName={autopf}\PhilosophersQuest
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; Output
OutputDir=.
OutputBaseFilename=PhilosophersQuest_Setup
SetupIconFile={#IconFile}

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; Appearance
WizardStyle=modern
WizardImageFile=compiler:WizClassicImage.bmp
WizardSmallImageFile=compiler:WizClassicSmallImage.bmp

; Silent upgrade behaviour:
;   - Detect the running exe and offer to close it automatically
;   - Uninstall previous version silently before installing new files
;   - Never require a manual uninstall step
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no
UninstallDisplayName={#AppName}
CreateUninstallRegKey=yes

; Require Windows 10 or later
MinVersion=10.0

; Version info embedded in Setup.exe
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} Installer
VersionInfoProductName={#AppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy everything from the PyInstaller one-folder bundle.
; ignoreversion lets the installer overwrite files from an older version
; without comparing version numbers (safe for our non-versioned asset files).
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Leave save files wherever the game writes them so progress survives uninstall
Type: filesandordirs; Name: "{app}"
