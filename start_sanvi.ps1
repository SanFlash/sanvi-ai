# Start SANVI in a new PowerShell window.
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv\Scripts\python.exe")) {
  py -3.11 -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements-local.txt
}
Start-Process -FilePath "$PSScriptRoot\.venv\Scripts\python.exe" -ArgumentList "$PSScriptRoot\sanvi_desktop.py" -WorkingDirectory $PSScriptRoot
