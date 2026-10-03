$ErrorActionPreference = "SilentlyContinue"
Unregister-ScheduledTask -TaskName "SANVI Universal Agent" -Confirm:$false
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\SANVI" -Recurse -Force
Remove-Item "$([Environment]::GetFolderPath("Desktop"))\SANVI.lnk" -Force
Write-Host "SANVI shortcuts and startup task removed. Repository files were not deleted."
