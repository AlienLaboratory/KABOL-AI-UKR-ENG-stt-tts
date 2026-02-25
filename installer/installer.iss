; Inno Setup Script for KA-BOL-AI
; Creates a Windows installer: download -> install -> run

[Setup]
AppName=KA-BOL-AI
AppVersion=0.1.0
AppPublisher=AlienLaboratory
AppPublisherURL=https://github.com/AlienLaboratory/KABOL-AI-UKR-ENG-stt-tts
DefaultDirName={autopf}\KA-BOL-AI
DefaultGroupName=KA-BOL-AI
OutputDir=..\dist
OutputBaseFilename=KA-BOL-AI-Setup
; No admin rights required
PrivilegesRequired=lowest
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

; Uncomment when icon exists:
; SetupIconFile=..\assets\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy everything from PyInstaller output
Source: "..\dist\KA-BOL-AI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\KA-BOL-AI"; Filename: "{app}\KA-BOL-AI.exe"
Name: "{group}\{cm:UninstallProgram,KA-BOL-AI}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\KA-BOL-AI"; Filename: "{app}\KA-BOL-AI.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\KA-BOL-AI.exe"; Description: "{cm:LaunchProgram,KA-BOL-AI}"; Flags: nowait postinstall skipifsilent
