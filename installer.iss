; Bidwinners Tracker — Inno Setup Installer Script
; To compile: open this file in Inno Setup Compiler and click Build > Compile

#define MyAppName "Bidwinners Tracker"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "BidEnterprise"
#define MyAppExeName "BidwinnersTracker.exe"

[Setup]
AppId={{8F3B1A2C-D4E5-4F6A-B7C8-9D0E1F2A3B4C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={commonpf64}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=BidwinnersTracker_Setup_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Run silently in background after install
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; The main bundled executable (built by PyInstaller)
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Code]
// Custom page to collect the API domain from the user during installation
var
  DomainPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  DomainPage := CreateInputQueryPage(
    wpWelcome,
    'Server Configuration',
    'Enter your Bidwinners server domain',
    'Please enter the base URL of your Bidwinners server (e.g. https://my-company.com). This can be changed later by editing config.json in the install folder.'
  );
  DomainPage.Add('Server URL:', False);
  DomainPage.Values[0] := 'https://enterprise.bidwinners.net';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigContent: string;
  ConfigFile: string;
  DataDir: string;
begin
  if CurStep = ssPostInstall then
  begin
    // Write config.json with the user's domain
    DataDir := ExpandConstant('{app}\data');
    ForceDirectories(DataDir);

    ConfigFile := ExpandConstant('{app}\config.json');
    ConfigContent := '{"api_base_url": "' + DomainPage.Values[0] + '", "admin_password": "bidwinners#12", "screenshot_interval": 300, "allowed_ips": []}';
    SaveStringToFile(ConfigFile, ConfigContent, False);
  end;
end;

[Run]
; Launch the app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
