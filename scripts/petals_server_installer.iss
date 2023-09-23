; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "petals-server"
#define MyAppVersion "6.5"
#define MyAppPublisher "ParisNeo"
#define MyAppURL "https://www.lollms.com/"
#define MyAppExeName "petals_server.bat"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".myp"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{9B72D9BA-A2B5-472F-9FF3-A2481897E814}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userappdata}\{#MyAppName}
ChangesAssociations=yes
DisableProgramGroupPage=yes
LicenseFile=../LICENSE
InfoBeforeFile=./explainer.md.
InfoAfterFile=./README.md
; Remove the following line to run in administrative install mode (install for all users.)
PrivilegesRequired=lowest
OutputBaseFilename=petals-server
SetupIconFile=../assets\petals.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked

[Files]
Source: "{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_script.sh"; DestDir: "{app}"; Flags: ignoreversion
Source: "wsl_installer.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "ubuntu_installer.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements_installer.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "ubuntu.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "petals_server.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "petals_server.sh"; DestDir: "{app}"; Flags: ignoreversion
Source: "uninstall.bat"; DestDir: "{app}"; Flags: ignoreversion

Source: "../assets\ubuntu.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "../assets\petals.ico"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Run]
Filename: "{app}\wsl_installer.bat"; Flags: shellexec  waituntilterminated
Filename: "{app}\ubuntu_installer.bat"; Flags: shellexec  waituntilterminated
Filename: "{app}\requirements_installer.bat"; Flags: shellexec  waituntilterminated

Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: shellexec postinstall skipifsilent

[UninstallRun]
Filename: "{app}\uninstall.bat"; Flags: shellexec; RunOnceId: 1

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"
Name: "{autodesktop}\ubuntu.bat"; Filename: "{app}\ubuntu.bat"; Tasks: desktopicon; IconFilename: "{app}\ubuntu.ico"    
Name: "{autodesktop}\petals_server.bat"; Filename: "{app}\petals_server.bat"; Tasks: desktopicon; IconFilename: "{app}\petals.ico"
