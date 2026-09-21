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
import urllib.parse
import json
from pathlib import Path
from typing import Callable, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    import httpx
except Exception:
    httpx = None

try:
    import pyautogui
    pyautogui.FAILSAFE = True
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

try:
    import cv2
except Exception:
    cv2 = None

try:
    from sanvi_planner import plan as ai_plan
except Exception:
    ai_plan = None

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
PAUSE = threading.Event()
TASK_CONTEXT: list[dict[str, str]] = []


def wait_if_paused() -> None:
    while PAUSE.is_set() and not STOP.is_set():
        time.sleep(0.2)


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
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
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



def system_info() -> str:
    info = {
        "computer": platform.node(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "cwd": str(Path.cwd()),
    }
    return json.dumps(info, indent=2)


def list_processes(filter_text: str = "") -> str:
    command = "Get-Process | Select-Object Id,ProcessName,CPU,WorkingSet | Sort-Object ProcessName"
    if filter_text:
        escaped = filter_text.replace("'", "''")
        command = f"Get-Process -Name '*{escaped}*' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,WorkingSet"
    return powershell(command)


def list_files(path: str = ".") -> str:
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(str(target))
    if target.is_file():
        return str(target)
    rows = []
    for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        rows.append(f"{'[DIR]' if item.is_dir() else '[FILE]'} {item.name}")
    return "\n".join(rows) or "(empty)"


def read_file(path: str) -> str:
    target = Path(path.strip().strip('"')).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(str(target))
    data = target.read_text(encoding="utf-8", errors="replace")
    return data[:30000] + ("\n...[truncated]" if len(data) > 30000 else "")


def write_file(path: str, content: str) -> str:
    target = Path(path.strip().strip('"')).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {target}"


def delete_file(path: str, allow: bool = False) -> str:
    if not allow:
        raise PermissionError("Deletion requires explicit confirmation. Say 'confirm delete <path>' or set SANVI_ALLOW_AUTOMATIC_DANGEROUS=true.")
    target = Path(path.strip().strip('"')).expanduser().resolve()
    if target.is_dir():
        import shutil
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
    else:
        raise FileNotFoundError(str(target))
    return f"Deleted {target}"


def camera_indices(max_index: int = 10) -> list[int]:
    if not cv2:
        raise RuntimeError("OpenCV is not installed. Install requirements-local.txt.")
    found = []
    for index in range(max_index):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW if platform.system() == "Windows" else 0)
        ok = cap.isOpened()
        if ok:
            found.append(index)
        cap.release()
    return found


def camera_photo(index: int = 0, path: str = "") -> str:
    if not cv2:
        raise RuntimeError("OpenCV is not installed. Install requirements-local.txt.")
    backend = cv2.CAP_DSHOW if platform.system() == "Windows" else 0
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera {index}. Check Windows camera permission and that no other app is using it.")
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("Camera opened but did not return a frame.")
    target = Path(path).expanduser().resolve() if path else Path.cwd() / "runtime" / "camera" / f"photo_{int(time.time())}.jpg"
    target.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(target), frame)
    return f"Camera photo saved to {target}"


def camera_preview(index: int = 0) -> str:
    if not cv2:
        raise RuntimeError("OpenCV is not installed. Install requirements-local.txt.")
    backend = cv2.CAP_DSHOW if platform.system() == "Windows" else 0
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera {index}. Check Windows camera permission.")
    log("Camera preview active. Press Q in the preview window to close it.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        cv2.imshow("SANVI Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
    return "Camera preview closed."


def android_ui_dump() -> str:
    raw = adb("shell", "uiautomator", "dump", "/sdcard/window.xml")
    xml = adb("shell", "cat", "/sdcard/window.xml")
    return xml[:30000] if xml else raw


def android_tap_text(text: str) -> str:
    xml = android_ui_dump()
    needle = text.strip().lower()
    # Parse bounds from UiAutomator XML without requiring a full XML dependency.
    pattern = re.compile(r'<node[^>]*text="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*/?>')
    for label, x1, y1, x2, y2 in pattern.findall(xml):
        if needle in label.lower():
            x = (int(x1) + int(x2)) // 2
            y = (int(y1) + int(y2)) // 2
            return android_tap(x, y)
    raise ValueError(f"Android UI text not found: {text}")


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



def normalize_hinglish(command: str) -> str:
    """Map common Hindi/Hinglish voice phrases to canonical executor commands."""
    x = command.strip()
    low = x.lower().strip()
    replacements = [
        (r"^(?:chrome|google chrome)\s+(?:khol|kholo|open karo|chalao)$", "open Chrome"),
        (r"^(?:notepad)\s+(?:khol|kholo|open karo)$", "open Notepad"),
        (r"^(?:calculator|calc)\s+(?:khol|kholo|open karo)$", "open Calculator"),
        (r"^(?:paint)\s+(?:khol|kholo|open karo)$", "open Paint"),
        (r"^(?:whatsapp)\s+(?:khol|kholo|open karo)$", "android open app whatsapp"),
        (r"^(?:camera)\s+(?:photo lo|photo le|photo kheecho|photo khicho)$", "camera photo"),
        (r"^(?:screenshot)\s+(?:lo|le lo|kheecho|le)$", "take screenshot"),
        (r"^(?:screen|computer)\s+(?:dikhao|dikhाओ|show karo)$", "take screenshot"),
        (r"^(?:search|google)\s+(?:karo|karna|karo for)\s+(.+)$", r"search for \1"),
        (r"^(.+?)\s+(?:search karo|search karो)$", r"search for \1"),
        (r"^(?:app)\s+(.+?)\s+(?:khol|kholo|open karo)$", r"android open app \1"),
        (r"^(?:file|folder)\s+(.+?)\s+(?:dikhao|dikhाओ|show karo)$", r"list files \1"),
    ]
    for pattern, replacement in replacements:
        m = re.match(pattern, low, re.I)
        if m:
            return re.sub(pattern, replacement, x, flags=re.I)
    return x


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



def execute_ai_action(tool: str, args: dict, original_command: str, allow_dangerous: bool = False) -> str:
    tool_map = {
        "open_app": lambda: open_app(str(args.get("name", ""))),
        "close_app": lambda: close_app(str(args.get("name", ""))),
        "browser_open": lambda: browser_open(str(args.get("url", ""))),
        "browser_search": lambda: browser_search(str(args.get("query", ""))),
        "type_text": lambda: type_text(str(args.get("text", ""))),
        "press_keys": lambda: press_keys(str(args.get("keys", ""))),
        "click_xy": lambda: click_xy(int(args.get("x", 0)), int(args.get("y", 0))),
        "screenshot": lambda: screenshot(),
        "camera_photo": lambda: camera_photo(int(args.get("index", 0)), str(args.get("path", ""))),
        "camera_preview": lambda: camera_preview(int(args.get("index", 0))),
        "system_info": lambda: system_info(),
        "list_files": lambda: list_files(str(args.get("path", "."))),
        "read_file": lambda: read_file(str(args.get("path", ""))),
        "write_file": lambda: write_file(str(args.get("path", "")), str(args.get("content", ""))),
        "delete_file": lambda: delete_file(str(args.get("path", "")), allow=allow_dangerous),
        "list_processes": lambda: list_processes(str(args.get("filter_text", ""))),
        "android_devices": lambda: android_devices(),
        "android_open": lambda: android_open(str(args.get("app", ""))),
        "android_tap": lambda: android_tap(int(args.get("x", 0)), int(args.get("y", 0))),
        "android_tap_text": lambda: android_tap_text(str(args.get("text", ""))),
        "android_type": lambda: android_type(str(args.get("text", ""))),
        "android_key": lambda: android_key(str(args.get("key", ""))),
        "android_screenshot": lambda: android_screenshot(),
    }
    if tool in {"run_powershell", "run_cmd"}:
        if not re.search(r"\b(powershell|cmd|command|terminal|shell|script)\b", original_command, re.I):
            raise PermissionError("AI planner cannot invent a shell command for an ordinary request.")
        command = str(args.get("command", "")).strip()
        if not command:
            raise ValueError("Empty shell command.")
        return powershell(command) if tool == "run_powershell" else cmd(command)
    if tool not in tool_map:
        raise ValueError(f"Unknown AI tool: {tool}")
    return tool_map[tool]()


def execute_ai_task(command: str, allow_dangerous: bool = False) -> str:
    if not ai_plan:
        raise RuntimeError("AI planner is unavailable. Check sanvi_planner.py and httpx.")
    context: list[dict[str, str]] = list(TASK_CONTEXT[-12:])
    last_screenshot = Path.cwd() / "runtime" / "screenshots" / "desktop.png"
    for round_no in range(1, 7):
        # Fresh visual state before every planning round.
        try:
            screenshot(str(last_screenshot))
        except Exception:
            last_screenshot = None
        decision = ai_plan(command, str(last_screenshot) if last_screenshot and last_screenshot.exists() else None, context)
        reply = str(decision.get("reply", "")).strip()
        actions = decision.get("actions") or []
        if not isinstance(actions, list):
            raise ValueError("AI planner returned invalid actions.")
        if decision.get("done") and not actions:
            return reply or "Task completed."
        for action in actions:
            wait_if_paused()
            if not isinstance(action, dict):
                continue
            tool = str(action.get("tool", "")).strip()
            args = action.get("args") or {}
            if not isinstance(args, dict):
                args = {}
            log(f"AI {round_no}: {tool} {args}")
            result = execute_ai_action(tool, args, command, allow_dangerous=allow_dangerous)
            context.append({"action": tool, "result": str(result)[:1200]})
            if STOP.is_set():
                raise RuntimeError("Task stopped.")
        # Capture the result of the action before the next planning round.
        try:
            screenshot(str(last_screenshot))
            context.append({"observation": "fresh desktop screenshot captured"})
        except Exception as exc:
            context.append({"observation": f"screenshot unavailable: {exc}"})
        if reply:
            context.append({"assistant": reply})
    raise RuntimeError("SANVI reached the maximum visual planning rounds without verified completion.")


def execute_one(command: str, allow_dangerous: bool = False) -> str:
    x = command.strip()
    low = x.lower()

    if low in {"stop", "stop sanvi", "emergency stop"}:
        STOP.set()
        PAUSE.clear()
        return "Stop requested."

    if low in {"pause", "pause sanvi", "wait"}:
        PAUSE.set()
        return "SANVI paused. Say resume when you want me to continue."

    if low in {"resume", "resume sanvi", "continue"}:
        PAUSE.clear()
        return "SANVI resumed."

    if low in {"undo", "undo last action"}:
        return press_keys("ctrl+z")

    if low in {"redo", "redo last action"}:
        return press_keys("ctrl+y")

    m = re.match(r"^(?:confirm\s+)?delete\s+(?:file\s+)?(.+)$", x, re.I | re.S)
    if m:
        confirmed = low.startswith("confirm delete") or allow_dangerous
        return delete_file(m.group(1), allow=confirmed)

    m = re.match(r"^(?:create|write)\s+(?:file\s+)?(.+?)\s+(?:with|content)\s*:\s*(.*)$", x, re.I | re.S)
    if m:
        return write_file(m.group(1), m.group(2))

    m = re.match(r"^(?:read|show|cat)\s+(?:file\s+)?(.+)$", x, re.I | re.S)
    if m:
        return read_file(m.group(1))

    m = re.match(r"^(?:list|show)\s+(?:files|folder|directory)(?:\s+(.+))?$", x, re.I)
    if m:
        return list_files(m.group(1) or ".")

    if low in {"system info", "computer info", "pc info", "system status"}:
        return system_info()

    m = re.match(r"^(?:list|show)\s+process(?:es)?(?:\s+(.+))?$", x, re.I)
    if m:
        return list_processes(m.group(1) or "")

    if low in {"camera list", "list cameras", "show cameras"}:
        return json.dumps(camera_indices())

    m = re.match(r"^camera\s+(?:photo|capture)(?:\s+(\d+))?(?:\s+(.+))?$", x, re.I)
    if m:
        return camera_photo(int(m.group(1) or 0), m.group(2) or "")

    m = re.match(r"^camera\s+(?:preview|start)(?:\s+(\d+))?$", x, re.I)
    if m:
        return camera_preview(int(m.group(1) or 0))

    if low in {"camera stop", "stop camera"}:
        return "Camera preview can be closed with Q in the preview window."

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

    if low in {"android ui", "android ui dump", "android screen xml"}:
        return android_ui_dump()

    m = re.match(r"^android\s+(?:tap|click)\s+text\s+(.+)$", x, re.I)
    if m:
        return android_tap_text(m.group(1))

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

    if low in {"shutdown", "shut down", "turn off computer"}:
        if not allow_dangerous:
            raise PermissionError("Shutdown requires explicit confirmation. Say 'confirm shutdown'.")
        return powershell("Stop-Computer -Force")

    if low in {"restart", "restart computer", "reboot computer"}:
        if not allow_dangerous:
            raise PermissionError("Restart requires explicit confirmation. Say 'confirm restart'.")
        return powershell("Restart-Computer -Force")

    m = re.match(r"^confirm\s+(shutdown|restart)$", low)
    if m:
        return execute_one(m.group(1), allow_dangerous=True)

    if ai_plan:
        try:
            return execute_ai_task(x, allow_dangerous=allow_dangerous)
        except RuntimeError as exc:
            if "AI planner is unavailable" not in str(exc):
                raise

    raise ValueError(
        "I understand the command, but no executor matched it yet. "
        "Try a complete command such as: "
        "'open Chrome and search for Playwright', 'open Notepad', "
        "'type hello', 'press ctrl+l', 'android devices', or "
        "'run powershell: Get-Process'."
    )


def execute(command: str, on_step: Optional[Callable[[int, int, str], None]] = None, allow_dangerous: bool = False) -> str:
    STOP.clear()
    command = normalize_hinglish(command)
    steps = split_steps(command)
    results = []
    total = len(steps)
    for index, step in enumerate(steps, 1):
        wait_if_paused()
        if STOP.is_set():
            raise RuntimeError("Task stopped.")
        if on_step:
            on_step(index, total, step)
        wait_if_paused()
        if STOP.is_set():
            raise RuntimeError("Task stopped.")
        log(f"{index}/{total}: {step}")
        results.append(execute_one(step, allow_dangerous=allow_dangerous))
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
    global TASK_CONTEXT
    log(f"> {command}")
    try:
        allow_dangerous = os.getenv("SANVI_ALLOW_AUTOMATIC_DANGEROUS", "").lower() in {"1","true","yes"}
        result = execute(command, allow_dangerous=allow_dangerous)
        TASK_CONTEXT.append({"user": command, "assistant": str(result)[:3000]})
        TASK_CONTEXT = TASK_CONTEXT[-20:]
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
