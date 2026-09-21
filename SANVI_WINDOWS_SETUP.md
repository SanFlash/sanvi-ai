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


## 12. Enable natural-language AI planning

The deterministic executor handles common commands directly. For complex requests, the optional vision planner can break a spoken request into actions, observe the desktop, and continue for several bounded rounds.

Examples:
- Open Chrome, go to my website, find Settings and take a screenshot.
- Open my project in VS Code, inspect the current screen and continue the task.
- On Android open WhatsApp and navigate to Settings.
- Find the file I was working on and show it.
- Do the same thing as the previous task, but for the other project.

### OpenAI planner
1. Copy `.env.agent.example` to `.env` in the SANVI repository root.
2. Set:

SANVI_AI_PROVIDER=openai
SANVI_AI_MODEL=gpt-5.6-luna
OPENAI_API_KEY=YOUR_KEY
SANVI_VOICE_LANGUAGE=en-IN

3. Save the file.
4. Run `start_sanvi.bat`.
The native runtime loads `.env` automatically.

The planner receives the spoken request and, when useful, a fresh desktop screenshot. It creates a strict action plan, SANVI executes it, captures another screenshot, and can plan another round. It stops after a bounded number of visual rounds.

### Local Ollama alternative
If you do not want an API key, install Ollama and a compatible vision model and configure:

SANVI_AI_PROVIDER=ollama
SANVI_AI_MODEL=YOUR_VISION_MODEL
SANVI_OLLAMA_URL=http://127.0.0.1:11434/api/chat

### Voice workflow
With `start_sanvi_background.bat` running:

You: Hey Sanvi, open Chrome and find the Playwright documentation.
SANVI: listens -> transcribes -> plans -> acts -> observes -> verifies -> speaks result

For a long task, SANVI can perform several action/observation rounds.

### Human-required operations
SANVI intentionally stops when a task requires an OTP, CAPTCHA, payment authorization, or another human-only approval.

### Security
Keep `SANVI_ALLOW_AUTOMATIC_DANGEROUS=false` unless you specifically want automatic destructive actions on a private machine.

## 13. Recommended first-time setup sequence
1. Clone or pull the repository.
2. Run `setup_sanvi.bat` once.
3. Open `.env`.
4. Set `OPENAI_API_KEY` if you want the AI planner and camera vision.
5. Keep `SANVI_ALLOW_AUTOMATIC_DANGEROUS=false` initially.
6. Connect the Android phone and verify `adb devices` if Android control is needed.
7. Check Windows Settings > Privacy & security > Camera and Microphone and allow access for desktop applications/Python as appropriate.
8. Run `start_sanvi.bat` for visible native mode.
9. Test `status`, `open Notepad`, `take screenshot`, `camera list`, and `android devices`.
10. Run `start_sanvi_background.bat` for hands-free voice mode.
11. Say `Hey Sanvi` followed by a complete task.

## 14. Example end-to-end voice commands
- `Hey Sanvi, open Chrome and search for Playwright automation.`
- `Hey Sanvi, open Notepad and type my test notes.`
- `Hey Sanvi, take a screenshot and tell me what is on the screen.`
- `Hey Sanvi, look through the camera and tell me what you see.`
- `Hey Sanvi, take a photo and save it in my Pictures folder.`
- `Hey Sanvi, open WhatsApp on Android and navigate to Settings.`
- `Hey Sanvi, show me the files in my project folder.`
- `Hey Sanvi, open my project and continue the current task.`
- `Hey Sanvi, pause.`
- `Hey Sanvi, resume.`
- `Hey Sanvi, stop.`

Natural-language planning is bounded by six visual planning rounds per request. If SANVI cannot verify completion, it reports that instead of claiming success.