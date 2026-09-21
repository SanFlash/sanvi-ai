"""
SANVI AI - native Windows controller.

This is the primary local runtime. It does NOT use the Render iframe/dashboard.
Run this on the Windows PC that SANVI is supposed to control.

Design:
- stdin command loop for complete commands
- optional global hotkey Ctrl+Alt+S for one-shot voice input
- Windows app/process control
- browser navigation/search
- keyboard/mouse automation
- Android ADB control
- explicit PowerShell/CMD execution when the user prefixes it with "run powershell:" / "run cmd:"
- optional Render bridge so the hosted page can submit commands to this same executor

The executor intentionally keeps destructive shell execution explicit rather than
silently interpreting ordinary conversational text as arbitrary shell code.
"""

from __future__ import annotations

import base64
import os
import platform
import re
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Callable, Optional

try:
    import httpx
except Exception:
    httpx = None

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import pyperclip
except Exception:
    pyperclip = None

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

APP_ALIASES = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "powershell": ["powershell.exe"],
    "cmd": ["cmd.exe"],
    "terminal": ["wt.exe"],
    "task manager": ["taskmgr.exe"],
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
}

ANDROID_ALIASES = {
    "whatsapp": "com.whatsapp",
    "chrome": "com.android.chrome",
    "youtube": "com.google.android.youtube",
    "instagram": "com.instagram.android",
    "telegram": "org.telegram.messenger",
    "gmail": "com.google.android.gm",
}

STOP = threading.Event()


def log(message: str) -> None:
    print(f"[SANVI] {message}", flush=True)


def speak(message: str) -> None:
    if not pyttsx3:
        return
    try:
        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()
        engine.stop()
    except Exception:
        pass


def powershell(command: str, timeout: int = 60) -> str:
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode:
        raise RuntimeError((completed.stderr or completed.stdout or "PowerShell failed").strip())
    return (completed.stdout or "PowerShell completed.").strip()


def cmd(command: str, timeout: int = 60) -> str:
    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", command],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode:
        raise RuntimeError((completed.stderr or completed.stdout or "CMD failed").strip())
    return (completed.stdout or "CMD completed.").strip()


def open_app(name: str) -> str:
    key = name.strip().lower()
    if key not in APP_ALIASES:
        # Let Windows resolve installed applications for explicitly requested app names.
        subprocess.Popen(["cmd.exe", "/d", "/c", "start", "", name], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return f"Opened {name}."
    subprocess.Popen(APP_ALIASES[key])
    return f"Opened {name}."


def close_app(name: str) -> str:
    key = name.strip().lower()
    exe = APP_ALIASES.get(key, [f"{name}.exe"])[0]
    result = powershell(f"Get-Process -Name '{Path(exe).stem}' -ErrorAction SilentlyContinue | Stop-Process -Force")
    return f"Closed {name}."


def browser_open(url: str) -> str:
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def browser_search(query: str) -> str:
    url = "https://www.google.com/search?q=" + __import__("urllib.parse").parse.quote_plus(query)
    return browser_open(url)


def browser_playwright(url: str, wait: float = 2.0) -> str:
    if not sync_playwright:
        return browser_open(url)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(wait)
        # Leave the browser running for the user.
        return f"Opened {page.url}"


def type_text(text: str) -> str:
    if not pyautogui:
        raise RuntimeError("Install pyautogui for keyboard/mouse control.")
    if pyperclip:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
    else:
        pyautogui.write(text, interval=0.01)
    return "Typed the requested text."


def press_keys(keys: str) -> str:
    if not pyautogui:
        raise RuntimeError("Install pyautogui for keyboard/mouse control.")
    parts = [p.strip().lower() for p in re.split(r"\s*\+\s*", keys) if p.strip()]
    if len(parts) == 1:
        pyautogui.press(parts[0])
    else:
        pyautogui.hotkey(*parts)
    return f"Pressed {keys}."


def click_xy(x: int, y: int) -> str:
    if not pyautogui:
        raise RuntimeError("Install pyautogui for keyboard/mouse control.")
    pyautogui.click(x, y)
    return f"Clicked {x}, {y}."


def screenshot(path: Optional[str] = None) -> str:
    if not pyautogui:
        raise RuntimeError("Install pyautogui for screenshots.")
    target = Path(path or (Path.cwd() / "runtime" / "screenshots" / "desktop.png"))
    target.parent.mkdir(parents=True, exist_ok=True)
    pyautogui.screenshot().save(target)
    upload_screenshot(target)
    return f"Screenshot saved to {target}"


def adb_path() -> str:
    value = os.getenv("ANDROID_ADB") or os.getenv("ADB")
    if value:
        return value
    return "adb"


def adb(*args: str, timeout: int = 30) -> str:
    completed = subprocess.run(
        [adb_path(), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode:
        raise RuntimeError((completed.stderr or completed.stdout or "ADB failed").strip())
    return (completed.stdout or "").strip()


def android_devices() -> str:
    return adb("devices")


def android_open(app: str) -> str:
    package = ANDROID_ALIASES.get(app.lower().strip(), app.strip())
    adb("shell", "monkey", "-p", package, "1")
    return f"Opened Android package {package}."


def android_tap(x: int, y: int) -> str:
    adb("shell", "input", "tap", str(x), str(y))
    return f"Tapped Android at {x}, {y}."


def android_type(text: str) -> str:
    # ADB input text needs spaces escaped.
    safe = text.replace(" ", "%s")
    adb("shell", "input", "text", safe)
    return "Typed text on Android."


def android_key(key: str) -> str:
    adb("shell", "input", "keyevent", key.upper().replace("KEYCODE_", ""))
    return f"Sent Android key {key}."


def android_screenshot() -> str:
    target = Path.cwd() / "runtime" / "screenshots" / "android.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [adb_path(), "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode(errors="replace"))
    target.write_bytes(completed.stdout)
    upload_screenshot(target)
    return f"Android screenshot saved to {target}"


def upload_screenshot(path: Path) -> None:
    server = os.getenv("SANVI_SERVER_URL", "").rstrip("/")
    token = os.getenv("SANVI_AGENT_TOKEN", "").strip()
    if not server or not token or not httpx:
        return
    try:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        with httpx.Client(timeout=10) as client:
            client.post(
                f"{server}/api/agent/screenshot",
                headers={"X-SANVI-Agent-Token": token},
                json={"filename": path.name, "data_b64": encoded},
            )
    except Exception as exc:
        log(f"Screenshot relay unavailable: {exc}")


def split_steps(command: str) -> list[str]:
    # Preserve common phrases such as "open Chrome and search for Playwright".
    normalized = command.strip()
    m = re.match(r"^(open|launch|start)\s+(chrome|edge|browser)\s+and\s+search\s+(?:for\s+)?(.+)$", normalized, re.I)
    if m:
        return [f"open {m.group(2)}", f"search for {m.group(3)}"]
    m = re.match(r"^(open|launch|start)\s+(.+?)\s+and\s+type\s+(.+)$", normalized, re.I)
    if m:
        return [f"open {m.group(2)}", f"type {m.group(3)}"]
    # Explicit step separator.
    return [s.strip() for s in re.split(r"\s+(?:then|after that)\s+", normalized, flags=re.I) if s.strip()]


def execute_one(command: str) -> str:
    x = command.strip()
    low = x.lower()

    if low in {"stop", "stop sanvi", "emergency stop"}:
        STOP.set()
        return "Stop requested."

    if re.fullmatch(r"(hello|hi|hey sanvi|status)", low):
        return f"SANVI is online on {platform.node()}."

    m = re.match(r"^(?:open|launch|start)\s+(.+?)\s*$", x, re.I)
    if m:
        target = m.group(1).strip()
        if target.lower() in {"chrome", "edge", "browser"}:
            return browser_open("https://www.google.com")
        return open_app(target)

    m = re.match(r"^(?:close|quit|exit)\s+(.+?)\s*$", x, re.I)
    if m:
        return close_app(m.group(1))

    m = re.match(r"^(?:search(?:\s+the\s+web)?\s+(?:for\s+)?)\s*(.+)$", x, re.I)
    if m:
        return browser_search(m.group(2))

    m = re.match(r"^(?:go\s+to|navigate\s+to)\s+(.+)$", x, re.I)
    if m:
        return browser_open(m.group(1))

    m = re.match(r"^type\s+(.+)$", x, re.I | re.S)
    if m:
        return type_text(m.group(1))

    m = re.match(r"^(?:press|hit)\s+(.+)$", x, re.I)
    if m:
        return press_keys(m.group(1))

    m = re.match(r"^click\s+(\d+)\s*,?\s*(\d+)$", x, re.I)
    if m:
        return click_xy(int(m.group(1)), int(m.group(2)))

    if low in {"take screenshot", "screenshot", "capture screen"}:
        return screenshot()

    if low.startswith("run powershell:"):
        return powershell(x.split(":", 1)[1].strip())

    if low.startswith("run cmd:"):
        return cmd(x.split(":", 1)[1].strip())

    if low in {"android devices", "list android devices", "adb devices"}:
        return android_devices()

    m = re.match(r"^(?:android\s+)?open\s+app\s+(.+)$", x, re.I)
    if m:
        return android_open(m.group(1))

    m = re.match(r"^android\s+tap\s+(\d+)\s+(\d+)$", x, re.I)
    if m:
        return android_tap(int(m.group(1)), int(m.group(2)))

    m = re.match(r"^android\s+type\s+(.+)$", x, re.I | re.S)
    if m:
        return android_type(m.group(1))

    m = re.match(r"^android\s+(?:key|press)\s+(.+)$", x, re.I)
    if m:
        return android_key(m.group(1))

    if low in {"android screenshot", "take android screenshot"}:
        return android_screenshot()

    # A URL can be supplied directly.
    if re.match(r"^https?://", x, re.I):
        return browser_open(x)

    raise ValueError(
        "I understand the command, but no executor matched it yet. "
        "Try a complete command such as: "
        "'open Chrome and search for Playwright', 'open Notepad', "
        "'type hello', 'press ctrl+l', 'android devices', or "
        "'run powershell: Get-Process'."
    )


def execute(command: str, on_step: Optional[Callable[[int, int, str], None]] = None) -> str:
    STOP.clear()
    steps = split_steps(command)
    results = []
    total = len(steps)
    for index, step in enumerate(steps, 1):
        if STOP.is_set():
            raise RuntimeError("Task stopped.")
        if on_step:
            on_step(index, total, step)
        log(f"{index}/{total}: {step}")
        results.append(execute_one(step))
    return "\n".join(results)


def voice_once() -> None:
    if not sr:
        log("Voice input is optional. Install SpeechRecognition + PyAudio to enable it.")
        return
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            log("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=20)
        text = recognizer.recognize_google(audio, language=os.getenv("SANVI_VOICE_LANGUAGE", "en-IN"))
        log(f"Heard: {text}")
        if re.match(r"^\s*(hey\s+sanvi|sanvi)\b", text, re.I):
            text = re.sub(r"^\s*(hey\s+sanvi|sanvi)\s*[,.:;-]?\s*", "", text, flags=re.I)
        if text.strip():
            run_command(text.strip())
    except Exception as exc:
        log(f"Voice input: {exc}")


def install_hotkey() -> None:
    try:
        import keyboard
        keyboard.add_hotkey("ctrl+alt+s", voice_once)
        log("Global voice hotkey: Ctrl+Alt+S")
    except Exception as exc:
        log(f"Global hotkey disabled: {exc}")


def run_command(command: str) -> None:
    log(f"> {command}")
    try:
        result = execute(command)
        log(result)
        speak(result.splitlines()[-1][:250])
        relay_result("COMPLETED", result)
    except Exception as exc:
        log(f"FAILED: {exc}")
        speak(f"Task failed. {str(exc)[:180]}")
        relay_result("FAILED", str(exc))


def relay_result(status: str, message: str) -> None:
    # This is only for commands submitted through the hosted bridge.
    task_id = os.getenv("SANVI_CURRENT_TASK_ID", "").strip()
    server = os.getenv("SANVI_SERVER_URL", "").rstrip("/")
    token = os.getenv("SANVI_AGENT_TOKEN", "").strip()
    if not (task_id and server and token and httpx):
        return
    try:
        with httpx.Client(timeout=10) as client:
            client.post(
                f"{server}/api/agent/result",
                headers={"X-SANVI-Agent-Token": token},
                json={
                    "task_id": task_id,
                    "status": status,
                    "message": message,
                    "current_step": 1,
                    "total_steps": 1,
                    "current_description": message[:500],
                },
            )
    except Exception:
        pass


def interactive() -> None:
    log("Native SANVI controller is running.")
    log("No browser/iframe is required. Type a command, or press Ctrl+Alt+S for voice.")
    log("Type 'exit' to close SANVI.")
    install_hotkey()
    while True:
        try:
            command = input("SANVI> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not command:
            continue
        if command.lower() in {"exit", "quit"}:
            break
        run_command(command)


if __name__ == "__main__":
    if platform.system() != "Windows":
        raise SystemExit("sanvi_desktop.py is currently a Windows local controller.")
    interactive()
