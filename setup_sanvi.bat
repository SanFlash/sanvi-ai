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

py -3.11 -c "import sys; print(sys.executable)"
if errorlevel 1 (
  echo Python 3.11 was not found.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  py -3.11 -m venv .venv
  if errorlevel 1 (
    echo Could not create Python 3.11 environment.
    pause
    exit /b 1
  )
)

.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
  echo pip upgrade failed.
  pause
  exit /b 1
)

.venv\Scripts\python.exe -m pip install -r requirements-local.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)

echo.
echo Verifying SpeechRecognition FLAC encoder...
.venv\Scripts\python.exe -c "import speech_recognition as sr; from pathlib import Path; p=Path(sr.__file__).parent / 'flac-win32.exe'; print('SpeechRecognition:', sr.__version__ if hasattr(sr,'__version__') else 'installed'); print('FLAC:', p); assert p.exists(), 'Missing bundled flac-win32.exe'"
if errorlevel 1 (
  echo FLAC encoder is missing from SpeechRecognition. Repairing SpeechRecognition...
  .venv\Scripts\python.exe -m pip install --force-reinstall --no-cache-dir "SpeechRecognition>=3.14,<4"
  if errorlevel 1 (
    echo ERROR: Could not repair SpeechRecognition.
    pause
    exit /b 1
  )
  .venv\Scripts\python.exe -c "import speech_recognition as sr; from pathlib import Path; p=Path(sr.__file__).parent / 'flac-win32.exe'; print('FLAC:', p); assert p.exists(), 'SpeechRecognition FLAC encoder is still missing'"
  if errorlevel 1 (
    echo ERROR: SpeechRecognition FLAC encoder is still unavailable.
    pause
    exit /b 1
  )
)
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)

echo.
echo Installing Playwright Chromium...
.venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 (
  echo.
  echo Playwright install failed. Repairing the Playwright package...
  .venv\Scripts\python.exe -m pip install --force-reinstall --no-cache-dir "playwright>=1.55,<2"
  if errorlevel 1 (
    echo ERROR: Could not reinstall Playwright.
    pause
    exit /b 1
  )
  .venv\Scripts\python.exe -m playwright install chromium
  if errorlevel 1 (
    echo ERROR: Playwright Chromium installation still failed.
    echo Run repair_playwright.bat and review its diagnostics.
    pause
    exit /b 1
  )
)

echo.
echo Verifying Playwright Chromium...
.venv\Scripts\python.exe -c "from pathlib import Path; from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.executable_path; print('Chromium:', b); assert Path(b).exists(), b; p.stop()"
if errorlevel 1 (
  echo ERROR: Playwright Chromium was not installed correctly.
  pause
  exit /b 1
)

if not exist ".env" (
  copy /Y ".env.agent.example" ".env" >nul
  echo Created .env from .env.agent.example.
)

echo.
echo SANVI setup is complete.
echo Edit .env and set OPENAI_API_KEY if you want natural-language AI planning and camera vision.
echo Then run .\start_sanvi.bat from PowerShell, or start_sanvi.bat from Command Prompt.
echo For background voice mode use .\start_sanvi_background.bat in PowerShell.
echo.
pause
