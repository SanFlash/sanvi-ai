param(
  [switch]$Startup
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Test-Path "$Root\dist\SANVI\SANVI.exe")) {
  Write-Host "SANVI executable not found. Building it now..."
  & "$Root\build_sanvi.bat"
  if ($LASTEXITCODE -ne 0) { throw "SANVI build failed." }
}

$Exe = "$Root\dist\SANVI\SANVI.exe"
$ShortcutDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\SANVI"
New-Item -ItemType Directory -Force -Path $ShortcutDir | Out-Null

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut((Join-Path $ShortcutDir "SANVI.lnk"))
$Shortcut.TargetPath = $Exe
$Shortcut.WorkingDirectory = "$Root\dist\SANVI"
$Shortcut.Description = "SANVI Universal AI Computer Agent"
$Shortcut.Save()

$DesktopShortcut = $Shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "SANVI.lnk"))
$DesktopShortcut.TargetPath = $Exe
$DesktopShortcut.WorkingDirectory = "$Root\dist\SANVI"
$DesktopShortcut.Description = "SANVI Universal AI Computer Agent"
$DesktopShortcut.Save()

if ($Startup) {
  $TaskName = "SANVI Universal Agent"
  $Action = New-ScheduledTaskAction -Execute $Exe -WorkingDirectory "$Root\dist\SANVI"
  $Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
  Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Force | Out-Null
  Write-Host "SANVI will start at user logon."
}

Write-Host "SANVI installed."
Write-Host "Start Menu: SANVI"
Write-Host "Desktop: SANVI.lnk"
Write-Host "Administrative operations use normal Windows UAC."
