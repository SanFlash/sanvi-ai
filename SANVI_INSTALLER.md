# SANVI Windows Application

SANVI can be built and installed as a local Windows application.

## Build

Run setup_sanvi.bat and then build_sanvi.bat.

The executable is created at:

dist\SANVI\SANVI.exe

## Install

Run PowerShell:

Set-ExecutionPolicy -Scope Process Bypass
.\install_sanvi.ps1

To start SANVI automatically when the current Windows user logs in:

.\install_sanvi.ps1 -Startup

The installer creates Start Menu and Desktop shortcuts. Startup registration runs SANVI with the normal interactive user token; it does not silently create a permanent elevated process.

## Administrator mode

Use start_sanvi_admin.bat.

Windows displays its normal UAC prompt. Approve it only when administrative operations are required.

## Configuration

Copy .env.agent.example to .env and configure:

SANVI_AI_PROVIDER
SANVI_AI_MODEL
OPENAI_API_KEY or Ollama settings
SANVI_AGENT_TOKEN for the optional hosted bridge
SANVI_ALLOW_AUTOMATIC_DANGEROUS=false

Do not commit .env or API keys.

## Control surface

SANVI combines Windows system inspection, services, processes, network diagnostics, environment variables, scheduled tasks, startup items, event logs, firewall inspection, power-plan inspection, file operations, keyboard/mouse/clipboard/screenshots, browser automation, camera operations, Android ADB operations, and natural-language planning.

State-changing administrative operations remain confirmation-gated by default.

## Example commands

system info
disk usage
network status
listening ports
services
processes chrome
installed software
startup items
scheduled tasks
event logs System 30
firewall rules
power plan
confirm start service Spooler
confirm kill process chrome
confirm set user env MY_APP=value
confirm clean temp
confirm restart

## Hosted mode

The Render service is a command queue/control plane only. The local SANVI application performs the actual machine operations. The local agent must be running and authenticated to the hosted service.

## Security model

SANVI does not bypass Windows security controls. It does not silently bypass UAC, passwords, MFA/OTP, CAPTCHA, antivirus/EDR, or application security prompts. Keep automatic dangerous execution disabled unless you understand the consequences and are operating on a machine you are authorized to control.
