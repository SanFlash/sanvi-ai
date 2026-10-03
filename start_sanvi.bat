@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating SANVI Windows environment...
  py -3.11 -m venv .venv
  if errorlevel 1 (
    echo Python 3.11 was not found. Install Python 3.11 and run this again.
    pause
    exit /b 1
  )
)

echo Installing/updating SANVI local dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements-local.txt

echo.
echo Starting SANVI Universal local controller...
echo Full system, desktop, browser, camera and Android controls are available.
echo.
.venv\Scripts\python.exe sanvi_universal.py
pause
