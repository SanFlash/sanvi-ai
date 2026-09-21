# SANVI AI — Native Windows + Android Runtime

SANVI is now local-first. The Render/Vercel dashboard is optional; it is not the component that controls the PC.

## Install
1. Windows 10/11 + Python 3.11.
2. Run `start_sanvi.bat`.
3. For Playwright: `.venv\Scripts\python.exe -m playwright install chromium`.
4. For Android: install Android Platform Tools and verify `adb devices`.

## Native mode
Run `.venv\Scripts\python.exe sanvi_desktop.py`.
No browser is required.
For operations that need Windows Administrator rights, use `start_sanvi_admin.bat`; Windows will show a normal UAC prompt.

Examples:
- `open Chrome`
- `open Chrome and search for Playwright`
- `open Notepad`
- `type Hello from SANVI`
- `press ctrl+l`
- `take screenshot`
- `system info`
- `list files C:\Users`
- `list processes chrome`
- `go to github.com`
- `run powershell: Get-Process`

## Background voice
Run `start_sanvi_background.bat` and say `Hey Sanvi, open Chrome`.
Set `SANVI_VOICE_LANGUAGE=en-IN` for English/Hinglish or `hi-IN` for Hindi.

## Camera
Commands: `camera list`, `camera photo`, `camera photo 0 C:\Users\YOUR_NAME\Pictures\sanvi.jpg`, `camera preview`.
Windows camera privacy permissions must allow the Python/desktop application. SANVI does not bypass Windows privacy controls.

## Android
Connect the phone, enable Developer Options and USB debugging, and approve the USB debugging prompt.
Commands: `android devices`, `android open app whatsapp`, `android open app com.example.myapp`, `android tap 500 800`, `android tap text Settings`, `android type hello`, `android key BACK`, `android screenshot`, `android ui dump`.

## System access
Windows apps, keyboard, mouse, files, processes and explicit PowerShell/CMD commands are supported.
Destructive operations such as delete/restart/shutdown require explicit confirmation by default.
Use `confirm delete PATH`, `confirm restart`, or `confirm shutdown`.
For a trusted private machine, `SANVI_ALLOW_AUTOMATIC_DANGEROUS=true` can enable automatic destructive actions.

## Optional hosted bridge
Set `SANVI_SERVER_URL` and `SANVI_AGENT_TOKEN` locally and the same token in Render, then run `local_agent.py`.
Render queues commands; the Windows machine executes them. Render cannot directly access your local camera, USB Android phone, keyboard, mouse or desktop.

## Emergency stop
Move the mouse to the top-left corner for PyAutoGUI fail-safe, or issue `stop`, `stop sanvi`, or `emergency stop`.

## Architecture
Microphone/keyboard -> SANVI Windows runtime -> Windows/Browser/Android/Camera/System tools.
Optional Render bridge -> authenticated queue -> same local executor.
