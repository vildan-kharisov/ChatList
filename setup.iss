; Скрипт Inno Setup для создания инсталлятора ChatList
; Использование: компилировать через Inno Setup Compiler
; Или использовать: iscc setup.iss

#define MyAppName "ChatList"
#define MyAppPublisher "ChatList"
#define MyAppURL "https://github.com"
#define MyAppExeName "ChatList.exe"

; Версия будет установлена через build-installer.ps1
; По умолчанию используется 1.0.0
#define MyAppVersion "1.0.0"

[Setup]
; Основные настройки
AppId={{A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
OutputDir=installer
OutputBaseFilename=ChatList-Setup-v{#MyAppVersion}
SetupIconFile=app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

; Информация для удаления
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\ChatList-v{#MyAppVersion}.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Удаление файлов базы данных (опционально, можно закомментировать)
; Type: files; Name: "{userappdata}\{#MyAppName}\chatlist.db"
; Type: files; Name: "{userappdata}\{#MyAppName}\*.db"
; Type: dirifempty; Name: "{userappdata}\{#MyAppName}"

; Удаление логов (опционально)
; Type: filesandordirs; Name: "{userappdata}\{#MyAppName}\logs"

[UninstallRun]
; Дополнительные действия при удалении
; Можно добавить команды для очистки реестра или других действий

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Дополнительные действия при удалении
    // Например, можно показать сообщение или выполнить дополнительные команды
  end;
  
  if CurUninstallStep = usPostUninstall then
  begin
    // Действия после удаления
    // Можно добавить очистку дополнительных файлов или папок
  end;
end;
