@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup_sanvi.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install "pyinstaller>=6.11,<7"
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --name SANVI --console sanvi_universal.py
if errorlevel 1 (
  echo SANVI build failed.
  pause
  exit /b 1
)
echo Build complete: dist\SANVI\SANVI.exe
pause
