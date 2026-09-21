# SANVI AI

**SANVI AI** is a local-first Windows + Android AI assistant designed to understand voice or text commands, plan multi-step tasks, control the local computer, automate browsers, interact with Android devices, use the camera, and report execution progress.

Repository: https://github.com/SanFlash/sanvi-ai

> **Important:** SANVI is designed to execute actions on the machine where the native runtime is installed. A hosted Render/Vercel dashboard cannot directly control your physical Windows desktop, microphone, camera, keyboard, mouse, or USB Android phone. The optional hosted architecture uses an authenticated queue and a local Windows agent.

---

## Table of Contents

1. [What SANVI Does](#what-sanvi-does)
2. [Core Architecture](#core-architecture)
3. [Main Capabilities](#main-capabilities)
4. [Project Structure](#project-structure)
5. [System Requirements](#system-requirements)
6. [Quick Start - Windows](#quick-start---windows)
7. [Environment Configuration](#environment-configuration)
8. [Starting SANVI](#starting-sanvi)
9. [Voice Mode](#voice-mode)
10. [Natural-Language AI Planner](#natural-language-ai-planner)
11. [Camera and Vision](#camera-and-vision)
12. [Windows Automation](#windows-automation)
13. [Browser Automation](#browser-automation)
14. [Android Automation](#android-automation)
15. [Files and System Operations](#files-and-system-operations)
16. [Pause, Resume, Stop, Undo and Redo](#pause-resume-stop-undo-and-redo)
17. [Hosted Render Bridge](#hosted-render-bridge)
18. [Render Deployment](#render-deployment)
19. [Security and Permissions](#security-and-permissions)
20. [Human-in-the-Loop Operations](#human-in-the-loop-operations)
21. [Troubleshooting](#troubleshooting)
22. [Development and Testing](#development-and-testing)
23. [Example Tasks](#example-tasks)
24. [Current Limitations](#current-limitations)
25. [Recommended Roadmap](#recommended-roadmap)
26. [License / Project Status](#license--project-status)

---

# What SANVI Does

SANVI is intended to behave like a computer-use assistant rather than a simple chatbot.

A request can start as:

- typed text
- a voice command
- a wake phrase such as **"Hey Sanvi"**
- a command received from the optional hosted dashboard

The runtime can then:

1. understand the request;
2. use recent task context;
3. decide whether the request can be handled deterministically or needs AI planning;
4. inspect the current desktop when visual planning is required;
5. execute local actions;
6. observe the result;
7. verify whether the requested state was reached;
8. continue with another bounded planning round when appropriate;
9. report success or failure without pretending an action happened.

SANVI also understands common Hindi/Hinglish command patterns through its command normalization and AI planner.

Examples:

> Hey Sanvi, open Chrome and search for Playwright documentation.

> Hey Sanvi, open my project and continue the current task.

> Hey Sanvi, take a screenshot and tell me what is visible.

> Hey Sanvi, look through the camera and tell me what you see.

> Hey Sanvi, open WhatsApp on Android and navigate to Settings.

---

# Core Architecture

## Local-first architecture

The recommended architecture is:

```text
Microphone / Keyboard
        |
        v
+-----------------------+
|   SANVI Windows App   |
|-----------------------|
| Voice / Text          |
| Command Manager       |
| Context               |
| AI Planner            |
| Permission Checks     |
| Tool Router           |
| Observation           |
| Verification          |
| Recovery              |
+-----------+-----------+
            |
     +------+-------+------------------+
     |              |                  |
     v              v                  v
 Windows         Browser            Android
 tools           Playwright         ADB/Appium
     |              |                  |
     +--------------+------------------+
                    |
                    v
              Camera / Files /
              Processes / System
```

## Optional hosted architecture

```text
Browser Dashboard
       |
       v
Render API / Queue
       |
 authenticated
       |
       v
Local SANVI Agent
       |
       v
Windows / Browser / Android / Camera
```

The hosted service is a command queue and dashboard layer. The local agent is what actually operates the physical machine.

---

# Main Capabilities

## Windows

SANVI can work with:

- applications
- keyboard
- mouse
- screenshots
- files
- processes
- system information
- PowerShell
- CMD
- PyAutoGUI
- Windows-related Python integrations
- optional Administrator execution through normal Windows UAC

## Browser

The project includes Playwright for browser automation.

Supported workflows can include:

- opening a browser
- opening URLs
- searching
- typing
- keyboard shortcuts
- visual interaction
- browser-driven QA workflows

## Android

The local runtime can work with Android through ADB and includes Appium client dependencies for further automation.

Examples include:

- list connected devices
- open applications
- tap coordinates
- tap visible UI text
- type text
- send Android keys
- capture screenshots
- dump Android UI

## Camera

The local runtime can:

- enumerate camera devices
- capture photographs
- save photographs to a specified path
- start camera preview
- capture a camera image and send it to the configured visual model for description

## AI planning

The AI planner can:

- interpret natural language;
- understand English/Hindi/Hinglish requests;
- use recent task context;
- inspect a screenshot;
- choose from SANVI's available tools;
- return structured JSON actions;
- let the local executor perform the actions;
- observe the result;
- continue for additional bounded rounds.

---

# Project Structure

Important files:

```text
sanvi-ai/
|
|-- main.py
|       Hosted FastAPI application / command queue / dashboard API
|
|-- sanvi_desktop.py
|       Main native Windows executor
|
|-- sanvi_planner.py
|       Natural-language and visual AI planner
|
|-- local_agent.py
|       Optional Render -> Windows execution bridge
|
|-- sanvi_background.py
|       Background voice runtime
|
|-- requirements.txt
|       Hosted/Render dependencies
|
|-- requirements-local.txt
|       Windows native runtime dependencies
|
|-- setup_sanvi.bat
|       Windows setup script
|
|-- start_sanvi.bat
|       Normal native runtime launcher
|
|-- start_sanvi_background.bat
|       Background voice launcher
|
|-- start_sanvi_admin.bat
|       Native runtime launcher with UAC
|
|-- start_sanvi_hidden.vbs
|       Background/hidden launcher helper
|
|-- .env.agent.example
|       Environment variable template
|
|-- SANVI_WINDOWS_SETUP.md
|       Native Windows setup notes
|
|-- render.yaml
|       Render deployment configuration
|
|-- dashboard/
|       Hosted dashboard assets
|
|-- api/
|       Hosted API entrypoint
|
|-- tests/
|       Syntax and project checks
|
|-- .github/workflows/
|       GitHub Actions checks
```

---

# System Requirements

## Windows

Recommended:

- Windows 10 or Windows 11
- Python 3.11
- PowerShell
- Internet connection for package installation and hosted AI APIs
- microphone for voice mode
- speakers/headphones for spoken responses
- camera for camera features
- Android Platform Tools for Android automation

Python 3.11 is the supported local runtime for the provided setup script.

---

# Quick Start - Windows

## Step 1 - Clone the repository

Open PowerShell or Command Prompt:

```powershell
git clone https://github.com/SanFlash/sanvi-ai.git
cd sanvi-ai
```

If the repository already exists:

```powershell
git pull origin main
```

## Step 2 - Run the automatic setup

Double-click:

```text
setup_sanvi.bat
```

Or run:

```powershell
.\setup_sanvi.bat
```

The script:

1. checks for the Python launcher;
2. creates `.venv` using Python 3.11;
3. upgrades pip;
4. installs `requirements-local.txt`;
5. installs the Playwright Chromium browser;
6. creates `.env` from `.env.agent.example` when needed.

## Step 3 - Configure .env

Open:

```text
.env
```

At minimum, for AI planning:

```env
SANVI_AI_PROVIDER=openai
SANVI_AI_MODEL=gpt-5.6-luna
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
SANVI_VOICE_LANGUAGE=en-IN
SANVI_ALLOW_AUTOMATIC_DANGEROUS=false
```

Do not commit your real `.env` file.

The repository ignores `.env` and other local secret files.

## Step 4 - Start SANVI

For normal visible mode:

```text
start_sanvi.bat
```

For background voice mode:

```text
start_sanvi_background.bat
```

For operations that require Administrator privileges:

```text
start_sanvi_admin.bat
```

Windows will still display its normal UAC prompt.

---

# Environment Configuration

The template is:

```env
# Optional hosted bridge
SANVI_SERVER_URL=https://YOUR-RENDER-SERVICE.onrender.com
SANVI_AGENT_TOKEN=CHANGE_ME_TO_A_LONG_RANDOM_SECRET

# Voice
SANVI_VOICE_LANGUAGE=en-IN

# Dangerous operation policy
SANVI_ALLOW_AUTOMATIC_DANGEROUS=false

# Android
ANDROID_ADB=

# AI planner
SANVI_AI_PROVIDER=openai
SANVI_AI_MODEL=gpt-5.6-luna
OPENAI_API_KEY=

# Optional local Ollama planner
# SANVI_AI_PROVIDER=ollama
# SANVI_AI_MODEL=llama3.2-vision
# SANVI_OLLAMA_URL=http://127.0.0.1:11434/api/chat
```

## Voice language

For English/Hinglish:

```env
SANVI_VOICE_LANGUAGE=en-IN
```

For Hindi:

```env
SANVI_VOICE_LANGUAGE=hi-IN
```

---

# Starting SANVI

## Visible native mode

```text
start_sanvi.bat
```

This is recommended during development because logs and errors are visible.

## Background voice mode

```text
start_sanvi_background.bat
```

Then say:

```text
Hey Sanvi, open Chrome
```

## Administrator mode

```text
start_sanvi_admin.bat
```

Use this only when an operation genuinely requires elevated Windows permissions.

SANVI does not bypass Windows security or UAC.

---

# Voice Mode

SANVI's voice workflow is conceptually:

```text
Microphone
   |
   v
Speech recognition
   |
   v
Command normalization
   |
   v
Context + planner
   |
   v
Local execution
   |
   v
Result
   |
   v
Text-to-speech
```

Example:

```text
Hey Sanvi, open Chrome and search for Playwright automation.
```

SANVI can also handle Hindi/Hinglish style requests such as:

```text
Hey Sanvi, Chrome kholo aur Playwright search karo.
```

The exact success of a natural-language command depends on the available tools, current desktop state, permissions, and planner configuration.

---

# Natural-Language AI Planner

The deterministic command executor handles known operations directly.

For more complex requests, `sanvi_planner.py` can create structured actions.

## Enable OpenAI planner

Set:

```env
SANVI_AI_PROVIDER=openai
SANVI_AI_MODEL=gpt-5.6-luna
OPENAI_API_KEY=YOUR_KEY
```

Then restart SANVI.

## Planner workflow

For a complex command:

```text
User request
     |
     v
Recent task context
     |
     v
Desktop screenshot when useful
     |
     v
AI planner
     |
     v
Structured JSON actions
     |
     v
SANVI executor
     |
     v
New screenshot / observation
     |
     v
Verification
     |
     +----> completed
     |
     +----> another bounded planning round
```

The planner is intentionally bounded and does not run forever.

The current implementation allows up to six visual planning rounds for a complex request.

## Available planner actions

The current planner exposes actions including:

```text
open_app
close_app
browser_open
browser_search
type_text
press_keys
click_xy
screenshot
camera_photo
camera_preview
system_info
list_files
read_file
write_file
delete_file
list_processes
android_devices
android_open
android_tap
android_tap_text
android_type
android_key
android_screenshot
run_powershell
run_cmd
```

The executor decides whether an action is allowed and how it is performed locally.

## Shell commands

PowerShell/CMD execution is deliberately restricted.

SANVI does not treat every natural-language sentence as permission to execute arbitrary shell commands.

Explicit requests containing command/shell/PowerShell/CMD/script intent can be routed to the corresponding tool, subject to the executor's safety rules.

---

# Local Ollama Alternative

The planner can also be configured for a local Ollama endpoint.

Example:

```env
SANVI_AI_PROVIDER=ollama
SANVI_AI_MODEL=YOUR_VISION_MODEL
SANVI_OLLAMA_URL=http://127.0.0.1:11434/api/chat
```

A compatible local model must already be installed and available through Ollama.

This option can reduce dependence on a hosted model API, but model capabilities and hardware requirements depend on the selected local model.

---

# Camera and Vision

## Windows permissions

Open:

```text
Windows Settings
  -> Privacy & security
  -> Camera
```

Allow the required camera access.

Also check microphone permissions for voice mode.

SANVI does not bypass Windows privacy controls.

## List cameras

Command:

```text
camera list
```

## Take a photo

```text
camera photo
```

## Save a photo to a specific location

Example:

```text
camera photo 0 C:\Users\YOUR_NAME\Pictures\sanvi.jpg
```

## Camera preview

```text
camera preview
```

## AI camera vision

Examples:

```text
camera vision
```

or:

```text
look through camera
```

or:

```text
what do you see
```

The runtime captures an image and can send it to the configured vision-capable AI planner.

The visual module is instructed to describe only information actually visible in the image.

---

# Windows Automation

Common examples:

```text
open Chrome
```

```text
open Notepad
```

```text
open Calculator
```

```text
type Hello from SANVI
```

```text
press ctrl+l
```

```text
take screenshot
```

```text
system info
```

```text
list processes chrome
```

```text
list files C:\Users
```

## Application control

The runtime can launch/close supported applications and interact with the desktop through local automation tools.

For complex GUI workflows, the AI planner can inspect a screenshot before selecting coordinate-based interactions.

---

# Browser Automation

Playwright is installed for browser automation.

Install browsers manually if necessary:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

Examples:

```text
open Chrome and search for Playwright documentation
```

```text
go to github.com
```

```text
open my website and take a screenshot
```

The project can be extended with additional deterministic Playwright tools for QA workflows, test generation, assertions, traces, downloads, and reporting.

---

# Android Automation

## Step 1 - Install Android Platform Tools

Install Android SDK Platform Tools and make sure `adb` is available.

Verify:

```powershell
adb version
```

If `adb` is not on PATH, set:

```env
ANDROID_ADB=C:\path\to\adb.exe
```

## Step 2 - Enable Developer Options

On the Android phone:

1. Open Settings.
2. Open About phone.
3. Find Build number.
4. Tap Build number repeatedly until Developer Options are enabled.
5. Open Developer Options.
6. Enable USB debugging.

The exact menu names can vary by Android manufacturer.

## Step 3 - Connect the device

Connect the phone by USB.

Run:

```powershell
adb devices
```

Accept the RSA debugging authorization prompt on the phone.

Expected output is similar to:

```text
List of devices attached
XXXXXXXX    device
```

## SANVI Android commands

List devices:

```text
android devices
```

Open an application by package:

```text
android open app com.example.myapp
```

Tap coordinates:

```text
android tap 500 800
```

Tap UI text:

```text
android tap text Settings
```

Type text:

```text
android type hello
```

Android key:

```text
android key BACK
```

Screenshot:

```text
android screenshot
```

UI dump:

```text
android ui dump
```

## Android safety

Android control depends on:

- USB debugging;
- device authorization;
- ADB availability;
- application/package behavior;
- Android permissions;
- device state.

SANVI cannot bypass Android security controls.

---

# Files and System Operations

Examples:

```text
list files C:\Users
```

```text
read file C:\path\to\file.txt
```

```text
write file C:\path\to\file.txt
```

```text
list processes chrome
```

```text
system info
```

## Destructive operations

Delete/restart/shutdown operations require explicit confirmation by default.

Examples of explicit confirmation patterns:

```text
confirm delete PATH
```

```text
confirm restart
```

```text
confirm shutdown
```

There is also:

```env
SANVI_ALLOW_AUTOMATIC_DANGEROUS=true
```

This should only be enabled when the operator deliberately wants automatic destructive operations on a trusted private machine.

Recommended default:

```env
SANVI_ALLOW_AUTOMATIC_DANGEROUS=false
```

---

# Pause, Resume, Stop, Undo and Redo

SANVI includes runtime control commands.

Pause:

```text
pause
```

Resume:

```text
resume
```

Stop:

```text
stop
```

Emergency stop:

```text
emergency stop
```

Undo:

```text
undo
```

Redo:

```text
redo
```

For GUI automation, PyAutoGUI's fail-safe is also enabled so moving the mouse to the top-left corner can act as an emergency physical stop mechanism.

---

# Task Context

SANVI keeps recent task context in memory to support commands such as:

```text
do the same thing
```

```text
continue
```

```text
continue the project
```

```text
do this for now
```

```text
use the previous task
```

The AI planner receives recent context when planning complex requests.

Current context is in-memory and is not a permanent database.

Restarting the local runtime clears this in-memory context.

---

# Hosted Render Bridge

The hosted bridge is optional.

Use it when you want:

- a hosted dashboard;
- remote command submission;
- task status;
- an authenticated local executor connection.

## Important architecture rule

Render cannot directly access:

- your Windows desktop;
- your physical keyboard;
- your physical mouse;
- your local microphone;
- your local camera;
- your USB Android device;
- your local Playwright browser session.

The local agent must be running on the Windows computer.

## Configure local .env

Set:

```env
SANVI_SERVER_URL=https://YOUR-RENDER-SERVICE.onrender.com
SANVI_AGENT_TOKEN=YOUR_LONG_RANDOM_SECRET
```

Set the same token in the Render environment.

## Start the bridge

After local dependencies are installed:

```powershell
.\.venv\Scripts\python.exe local_agent.py
```

The bridge:

1. sends a heartbeat;
2. polls the hosted API for tasks;
3. receives a task;
4. executes it locally;
5. reports progress;
6. reports completion/failure;
7. honors hosted pause/cancel state.

---

# Render Deployment

The repository contains `render.yaml`.

Current service configuration uses:

```text
Runtime: Python
Start command:
uvicorn main:app --host 0.0.0.0 --port $PORT
Health check:
/api/health
Python:
3.11.9
```

## Deployment steps

1. Push the repository to GitHub.
2. Open Render.
3. Create a new Web Service from the GitHub repository.
4. Select `SanFlash/sanvi-ai`.
5. Render can use the included `render.yaml` configuration.
6. Add required environment variables.
7. Deploy.
8. Open the health endpoint.

Expected health endpoint:

```text
https://YOUR-RENDER-SERVICE.onrender.com/api/health
```

## Hosted environment variables

At minimum, configure the agent authentication token when using the local bridge.

Example:

```env
SANVI_AGENT_TOKEN=YOUR_LONG_RANDOM_SECRET
SANVI_MODE=production
LOG_LEVEL=INFO
```

Never put a real secret directly into source code.

---

# Hosted API Task Flow

The hosted API uses a task queue.

Conceptually:

```text
POST /api/command
       |
       v
create task
       |
       v
queue
       |
       v
local_agent.py
       |
       v
Windows executor
       |
       v
POST /api/agent/result
```

The local agent also reports heartbeats and checks task state so pause/cancel commands can be enforced locally.

The hosted queue is currently in-memory. A Render restart can therefore clear queued/in-memory task state.

For a production multi-user deployment, a persistent task store/queue should be added.

---

# Security and Permissions

SANVI has access to powerful local capabilities, so configuration should be treated seriously.

## Never commit secrets

Do not commit:

```text
.env
API keys
agent tokens
passwords
session cookies
private certificates
ADB private data
```

The repository's `.gitignore` is configured to keep local environment files out of Git.

## Use a strong agent token

Generate a long random secret for:

```env
SANVI_AGENT_TOKEN=
```

Use the same secret on Render and the Windows agent.

## Localhost principle

The local execution layer should remain local.

Do not expose an endpoint that accepts arbitrary PowerShell, CMD, or ADB commands to the public internet.

## Dangerous actions

Keep:

```env
SANVI_ALLOW_AUTOMATIC_DANGEROUS=false
```

unless automatic destructive actions are deliberately required.

## Camera privacy

Camera access requires operating-system permission.

## Android privacy

USB debugging and device authorization must be explicitly enabled.

---

# Human-in-the-Loop Operations

SANVI intentionally does not try to bypass human-only security controls.

Examples:

- OTP entry
- CAPTCHA
- payment authorization
- approval prompts
- account recovery verification
- other human-only authorization steps

When a workflow reaches such a step, SANVI should stop or ask the operator to take over rather than attempting to defeat the control.

Do not put passwords, OTPs, private keys, or payment secrets into source code or Git.

---

# Troubleshooting

## Python not found

Check:

```powershell
py --version
python --version
```

Install Python 3.11 if the Python launcher cannot find it.

Then run:

```text
setup_sanvi.bat
```

## Virtual environment not created

Delete a broken environment and recreate it:

```powershell
rmdir /s /q .venv
```

Then:

```text
setup_sanvi.bat
```

Run the delete command from Command Prompt, or remove `.venv` manually from Explorer.

## Playwright browser missing

Run:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

## OpenAI planner says no API key

Check `.env`:

```env
OPENAI_API_KEY=YOUR_KEY
```

Then restart SANVI.

Do not add quotes unless the value itself requires them.

## Camera is not detected

Check:

1. camera is connected;
2. another application is not exclusively using it;
3. Windows camera privacy permissions;
4. `camera list`;
5. Python/OpenCV installation.

## Microphone is not working

Check:

1. Windows microphone permissions;
2. default input device;
3. microphone hardware;
4. SpeechRecognition/PyAudio installation;
5. `SANVI_VOICE_LANGUAGE`.

## Android shows no devices

Run:

```powershell
adb devices
```

Then check:

1. USB cable;
2. USB debugging;
3. Android developer options;
4. RSA authorization prompt;
5. ADB installation;
6. device driver if required by the manufacturer.

## Render says local actions do not execute

Remember:

```text
Render != your Windows computer
```

You need:

1. deployed Render API;
2. matching `SANVI_AGENT_TOKEN`;
3. local Windows machine connected to the Render service;
4. `local_agent.py` running;
5. Windows tools/dependencies installed.

## Render task stays BUSY

Check the local agent terminal.

You should see a connection message similar to:

```text
Hosted bridge connected: https://YOUR-RENDER-SERVICE.onrender.com
```

Then submit a small task such as:

```text
open Notepad
```

## AI planner cannot complete a GUI task

Check:

- current desktop state;
- screenshot visibility;
- application permissions;
- whether a login/OTP/CAPTCHA is required;
- whether the task depends on a site layout the planner cannot reliably identify;
- whether the operation needs a deterministic tool instead of visual coordinate automation.

SANVI should report failure rather than claiming an unverified success.

---

# Development and Testing

## Compile/syntax check

The repository contains:

```text
tests/test_syntax.py
```

It checks the main Python runtime modules for syntax errors.

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

or, if pytest is not installed in the environment, compile individual files:

```powershell
.\.venv\Scripts\python.exe -m py_compile main.py sanvi_desktop.py local_agent.py sanvi_background.py
```

## GitHub Actions

The repository includes a syntax-check workflow under:

```text
.github/workflows/sanvi-syntax.yml
```

Every update should keep the core Python modules syntactically valid.

## Local development loop

Recommended:

```text
1. git pull
2. activate/use .venv
3. install/update requirements
4. run syntax tests
5. run SANVI visibly
6. test one deterministic command
7. test screenshot
8. test browser
9. test Android if connected
10. test AI planner
11. test pause/stop
12. commit
13. push
```

---

# Example Tasks

## Basic Windows

```text
Hey Sanvi, open Notepad.
```

```text
Hey Sanvi, type "SANVI AI test complete".
```

```text
Hey Sanvi, take a screenshot.
```

## Browser

```text
Hey Sanvi, open Chrome and search for Playwright.
```

```text
Hey Sanvi, open github.com.
```

## File operations

```text
Hey Sanvi, show files in C:\Users.
```

```text
Hey Sanvi, read this text file.
```

For writes/deletes, make sure the target path and intended operation are correct.

## Camera

```text
Hey Sanvi, list cameras.
```

```text
Hey Sanvi, take a photo.
```

```text
Hey Sanvi, look through the camera and describe what you see.
```

## Android

```text
Hey Sanvi, show Android devices.
```

```text
Hey Sanvi, open WhatsApp on Android.
```

```text
Hey Sanvi, navigate to Android Settings.
```

## Context

```text
Hey Sanvi, open my project.
```

Then:

```text
Hey Sanvi, continue the current task.
```

Or:

```text
Hey Sanvi, do the same thing for the other project.
```

Natural-language continuation depends on the available task context and current desktop state.

## Pause and stop

```text
Hey Sanvi, pause.
```

```text
Hey Sanvi, resume.
```

```text
Hey Sanvi, stop.
```

---

# Current Limitations

SANVI is a broad computer-use framework, but it should not be described as an unrestricted autonomous computer operator.

Current limitations include:

1. **Visual automation is not guaranteed for every application.** GUI layouts can change and some applications expose limited accessibility information.
2. **AI planning is bounded.** The current visual planning loop has a maximum of six planning rounds per request.
3. **Task context is in-memory.** It is currently lost when the native process restarts.
4. **Hosted task state is in-memory.** A Render restart can clear queued/in-memory tasks.
5. **The camera requires OS permissions.**
6. **Android requires ADB/device authorization.**
7. **Appium is included as a dependency, while the current Android executor primarily uses ADB/UiAutomator2-style operations.**
8. **OTP/CAPTCHA/payment and other human-only security steps require operator involvement.**
9. **A hosted service cannot directly operate physical local hardware without a local agent.**
10. **Natural-language interpretation depends on the configured AI model and available local tools.**
11. **Arbitrary destructive operations are not automatically allowed by default.**
12. **No system can guarantee successful execution of literally every possible task across every Windows application and website.**

---

# Recommended Roadmap

The project can be expanded in stages.

## Phase 1 - Core stability

- stronger structured tool validation;
- better error messages;
- more deterministic Windows tools;
- richer task history;
- better cancellation;
- persistent configuration.

## Phase 2 - Persistent agent state

Add:

- SQLite/PostgreSQL task history;
- resumable tasks;
- persistent context;
- execution history;
- audit logs.

## Phase 3 - Better computer vision

Add:

- OCR;
- accessibility-tree extraction;
- Windows UI Automation;
- richer screenshot understanding;
- region-based verification;
- application-specific adapters.

## Phase 4 - Browser QA

Add:

- Playwright test generation;
- assertions;
- test suites;
- trace collection;
- screenshots;
- videos;
- HTML reports;
- regression execution.

## Phase 5 - Android QA

Add:

- complete Appium session management;
- UiAutomator2 selectors;
- test generation;
- device farm support;
- screenshots and recordings;
- test reports.

## Phase 6 - Production hosted architecture

Add:

- Redis or another persistent queue;
- database-backed tasks;
- WebSocket event streaming;
- multi-user authentication;
- per-device authorization;
- rate limits;
- audit logs;
- encrypted secrets;
- reliable reconnect/retry handling.

## Phase 7 - Advanced local agent

Potential additions:

- Windows Service mode;
- startup integration;
- local dashboard;
- offline STT;
- local LLM/VLM;
- richer wake-word detection;
- scheduled tasks;
- specialized QA agents;
- project/workspace memory.

---

# Operational Safety Checklist

Before allowing SANVI to control an important machine:

- [ ] Windows updates and security controls are active.
- [ ] `SANVI_ALLOW_AUTOMATIC_DANGEROUS=false`.
- [ ] `.env` is not committed.
- [ ] API keys are stored only in environment variables.
- [ ] Agent token is long and random.
- [ ] Hosted API is authenticated.
- [ ] Local executor is not publicly exposed.
- [ ] Camera permissions are intentional.
- [ ] Android USB debugging is enabled only when needed.
- [ ] You have tested the emergency stop.
- [ ] You have tested pause/resume.
- [ ] You understand which commands can modify/delete files.
- [ ] You have tested SANVI in a safe environment before using it for important work.

---

# Quick Command Reference

| Purpose | Command |
|---|---|
| Setup | `setup_sanvi.bat` |
| Normal runtime | `start_sanvi.bat` |
| Background voice | `start_sanvi_background.bat` |
| Admin runtime | `start_sanvi_admin.bat` |
| Open app | `open Chrome` |
| Screenshot | `take screenshot` |
| System information | `system info` |
| Processes | `list processes chrome` |
| Files | `list files C:\\Users` |
| Camera list | `camera list` |
| Camera photo | `camera photo` |
| Camera preview | `camera preview` |
| Android devices | `android devices` |
| Android screenshot | `android screenshot` |
| Android UI | `android ui dump` |
| Pause | `pause` |
| Resume | `resume` |
| Stop | `stop` |
| Emergency stop | `emergency stop` |
| Undo | `undo` |
| Redo | `redo` |

---

# Contributing / Extending SANVI

When adding a new capability:

1. Add a small deterministic local function first.
2. Validate inputs.
3. Define the permission/risk level.
4. Add it to the planner's available tool list only after the executor supports it.
5. Add error handling.
6. Add verification where possible.
7. Add a test.
8. Update this README.
9. Update `SANVI_WINDOWS_SETUP.md` if setup changes.
10. Never commit secrets.
11. Keep public APIs from becoming arbitrary command-execution endpoints.

A useful new tool should follow:

```text
request
  -> validation
  -> permission/risk check
  -> execution
  -> observation
  -> verification
  -> result
```

---

# Project Philosophy

SANVI is intended to be:

- local-first;
- explicit about permissions;
- observable during execution;
- useful for Windows automation;
- useful for browser automation;
- useful for Android automation;
- useful for QA automation;
- capable of natural-language planning;
- able to use visual observations;
- honest about failures;
- extensible through typed tools;
- safe by default for destructive operations.

The goal is not to claim that every possible task is already solved. The goal is to provide a practical foundation for a progressively more capable computer-use agent.

---

# Status

SANVI currently contains:

- native Windows executor;
- voice/background runtime;
- natural-language AI planner;
- screenshot-based planning loop;
- camera capture and vision integration;
- Windows application/file/process tools;
- Playwright support;
- Android ADB/UI operations;
- pause/resume/stop controls;
- task context;
- optional Render hosted bridge;
- GitHub syntax checks;
- Windows setup scripts;
- security defaults for destructive operations.

For the most reliable operation, start with the local Windows runtime and add the hosted bridge only when remote/dashboard control is needed.

---

## Final First-Run Checklist

```text
1. Clone repository
2. Install Python 3.11
3. Run setup_sanvi.bat
4. Open .env
5. Add OPENAI_API_KEY if using AI planning
6. Keep SANVI_ALLOW_AUTOMATIC_DANGEROUS=false
7. Check microphone permission
8. Check camera permission if using camera
9. Install/configure ADB if using Android
10. Run start_sanvi.bat
11. Test: status
12. Test: open Notepad
13. Test: take screenshot
14. Test: camera list
15. Test: android devices
16. Start background voice mode
17. Say: "Hey Sanvi, open Chrome"
18. Test a small multi-step task
19. Test pause
20. Test resume
21. Test stop
22. Only then move to larger automation workflows
```

**SANVI AI — Local-first AI computer-use and QA automation foundation.**
