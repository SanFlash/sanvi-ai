@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  call "%~dp0start_sanvi.bat"
  exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~dp0.venv\Scripts\python.exe' -ArgumentList '"%~dp0sanvi_desktop.py"' -WorkingDirectory '%~dp0' -Verb RunAs"
