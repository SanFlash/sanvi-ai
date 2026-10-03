@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
  call "%~dp0start_sanvi.bat"
  exit /b
)

echo Starting SANVI background voice service...
start "" "%~dp0start_sanvi_hidden.vbs"
