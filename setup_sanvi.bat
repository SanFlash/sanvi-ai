@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo SANVI AI - Windows setup
echo ==========================================

where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher was not found.
  echo Install Python 3.11 from python.org and run this again.
  pause
  exit /b 1
)

py -3.11 -m venv .venv
if errorlevel 1 (
  echo Could not create Python 3.11 environment.
  pause
  exit /b 1
)

.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements-local.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)

.venv\Scripts\python.exe -m playwright install chromium

if not exist ".env" (
  copy /Y ".env.agent.example" ".env" >nul
  echo Created .env from .env.agent.example.
)

echo.
echo SANVI setup is complete.
echo Edit .env and set OPENAI_API_KEY if you want natural-language AI planning and camera vision.
echo Then run start_sanvi.bat or start_sanvi_background.bat.
echo.
pause
