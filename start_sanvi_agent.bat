@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.11 -m venv .venv
  if errorlevel 1 exit /b 1
  .venv\Scripts\python.exe -m pip install -r requirements-local.txt
)
.venv\Scripts\python.exe local_agent.py
pause
