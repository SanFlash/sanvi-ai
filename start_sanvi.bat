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

echo.
echo Starting SANVI Universal local controller...
echo Full system, desktop, browser, camera and Android controls are available.
echo.
.venv\Scripts\python.exe sanvi_universal.py
pause
