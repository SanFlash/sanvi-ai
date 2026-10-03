@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo SANVI AI - Playwright repair
echo ==========================================

if not exist ".venv\Scripts\python.exe" (
  echo SANVI virtual environment not found.
  echo Run setup_sanvi.bat first.
  pause
  exit /b 1
)

echo Python:
.venv\Scripts\python.exe --version

echo.
echo Playwright package:
.venv\Scripts\python.exe -m playwright --version
if errorlevel 1 (
  echo Playwright CLI is unavailable. Reinstalling...
  .venv\Scripts\python.exe -m pip install --force-reinstall --no-cache-dir "playwright>=1.55,<2"
  if errorlevel 1 (
    echo ERROR: Playwright reinstall failed.
    pause
    exit /b 1
  )
)

echo.
echo Installing Chromium...
.venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 (
  echo ERROR: Chromium installation failed.
  echo.
  echo Diagnostics:
  .venv\Scripts\python.exe -c "import playwright,sys; print('Python:',sys.executable); print('Playwright:',playwright.__file__)"
  where node
  where py
  pause
  exit /b 1
)

echo.
echo Verifying browser executable...
.venv\Scripts\python.exe -c "from pathlib import Path; from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.executable_path; print('Chromium:',b); print('Exists:',Path(b).exists()); assert Path(b).exists(); browser=p.chromium.launch(headless=True); print('Chromium launch: OK'); browser.close(); p.stop()"
if errorlevel 1 (
  echo ERROR: Chromium exists but could not launch.
  echo Check Windows security software and the Playwright cache.
  pause
  exit /b 1
)

echo.
echo Playwright repair completed successfully.
pause
