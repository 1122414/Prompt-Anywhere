[Setup]
AppId={{PromptAnywhere}
AppName=Prompt Anywhere
AppVersion=0.1.0
AppPublisher=Prompt Anywhere Team
DefaultDirName={autopf}\PromptAnywhere
DefaultGroupName=Prompt Anywhere
OutputDir=installer\output
OutputBaseFilename=PromptAnywhereSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "开机自启"; GroupDescription: "其他选项:"

[Files]
Source: "dist\PromptAnywhere\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Prompt Anywhere"; Filename: "{app}\PromptAnywhere.exe"
Name: "{group}\{cm:UninstallProgram,Prompt Anywhere}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Prompt Anywhere"; Filename: "{app}\PromptAnywhere.exe"; Tasks: desktopicon
Name: "{userstartup}\PromptAnywhere"; Filename: "{app}\PromptAnywhere.exe"; Tasks: startupicon

[Run]
Filename: "{app}\PromptAnywhere.exe"; Description: "{cm:LaunchProgram,Prompt Anywhere}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  DataDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    DataDir := ExpandConstant('{userappdata}\PromptAnywhere');
    if not DirExists(DataDir) then
      CreateDir(DataDir);
    if not DirExists(DataDir + '\data') then
      CreateDir(DataDir + '\data');
    if not DirExists(DataDir + '\exports') then
      CreateDir(DataDir + '\exports');
    if not DirExists(DataDir + '\backups') then
      CreateDir(DataDir + '\backups');
    if not DirExists(DataDir + '\logs') then
      CreateDir(DataDir + '\logs');
  end;
end;
