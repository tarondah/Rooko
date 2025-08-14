[Setup]
AppName=Rooko
AppVersion=1.0
DefaultDirName={pf}\Rooko
DefaultGroupName=Rooko
OutputBaseFilename=RookoInstaller
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: desktopicon; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\Rooko.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.jsonc"; DestDir: "{app}"; Flags: ignoreversion
Source: "playtime.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\Rooko Launcher"; Filename: "{app}\Rooko.exe"; IconFilename: "{app}\logo.ico"

; Optional desktop shortcut
Name: "{userdesktop}\Rooko Launcher"; Filename: "{app}\Rooko.exe"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon
