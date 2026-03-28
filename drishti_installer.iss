; ─────────────────────────────────────────────
; Drishti Installer (Professional Setup)
; ─────────────────────────────────────────────

[Setup]
AppId={{D1A7F6C2-ABCD-4321-9999-DRISHTIAPP}}
AppName=Drishti Media Studio
AppVersion=1.0
AppPublisher=Drishti

DefaultDirName={pf}\Drishti
DefaultGroupName=Drishti

OutputDir=installer
OutputBaseFilename=DrishtiSetup

Compression=lzma
SolidCompression=yes

; ── ICON / BRANDING ──────────────────────────
SetupIconFile=assets\logo.ico
UninstallDisplayIcon={app}\Drishti.exe

; ── MODERN UI ────────────────────────────────
WizardStyle=modern

; ── BEHAVIOR ─────────────────────────────────
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=admin

; ── UNINSTALL SUPPORT ────────────────────────
UninstallDisplayName=Drishti Media Studio
Uninstallable=yes

; ─────────────────────────────────────────────


[Files]
Source: "dist\Drishti\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion


[Icons]
Name: "{group}\Drishti"; Filename: "{app}\Drishti.exe"
Name: "{commondesktop}\Drishti"; Filename: "{app}\Drishti.exe"


[Run]
Filename: "{app}\Drishti.exe"; Description: "Launch Drishti"; Flags: nowait postinstall skipifsilent


; ─────────────────────────────────────────────
; SMART REINSTALL / UPGRADE HANDLING
; ─────────────────────────────────────────────

[Code]

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;

  if RegKeyExists(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1') then
  begin
    if MsgBox('Drishti is already installed. Do you want to reinstall/upgrade it?',
       mbConfirmation, MB_YESNO) = IDYES then
    begin
      Exec(ExpandConstant('{uninstallexe}'), '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end
    else
    begin
      Result := False;
    end;
  end;
end;