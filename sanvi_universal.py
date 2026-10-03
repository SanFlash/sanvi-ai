"""SANVI Universal Windows runtime.

Adds structured administration commands to the existing SANVI desktop runtime.
Privileged state changes are confirmation-gated by default.
"""
from __future__ import annotations
import os
import shlex
import sanvi_desktop as desktop
import sanvi_system as system

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def _auto_allowed() -> bool:
    return os.getenv("SANVI_ALLOW_AUTOMATIC_DANGEROUS","").lower() in {"1","true","yes"}

def _confirmed(command: str) -> bool:
    return command.strip().lower().startswith("confirm ")

def _system(command: str) -> str | None:
    original = command.strip()
    low = original.lower()
    confirmed = _confirmed(original)
    body = original[8:].strip() if confirmed else original
    body_low = body.lower()
    allow = confirmed or _auto_allowed()

    if body_low in {"system info","computer info","pc info","system overview","system status","health check"}:
        return system.system_overview()
    if body_low in {"admin status","privilege status","am i admin","check admin"}:
        return system.privilege_status()
    if body_low in {"disk usage","disk space","storage status"}:
        return system.disk_usage()
    if body_low in {"network status","network overview","network info"}:
        return system.network_overview()
    if body_low in {"listening ports","open ports","show ports"}:
        return system.listening_ports()
    if body_low in {"services","list services","show services"}:
        return system.services()
    if body_low in {"installed software","installed applications","installed apps"}:
        return system.installed_software()
    if body_low in {"environment","environment variables","env variables"}:
        return system.environment_variables()
    if body_low in {"startup apps","startup items"}:
        return system.startup_items()
    if body_low in {"scheduled tasks","task scheduler"}:
        return system.scheduled_tasks()
    if body_low in {"firewall","firewall rules","show firewall"}:
        return system.firewall_rules()
    if body_low in {"power plan","power status"}:
        return system.power_plan()

    words = shlex.split(body)
    if len(words) >= 3 and words[0].lower() in {"start","stop"} and words[1].lower() in {"service","services"}:
        if not allow:
            raise PermissionError("Service changes require confirmation. Use 'confirm start service NAME' or 'confirm stop service NAME'.")
        name = " ".join(words[2:])
        return system.start_service(name, True) if words[0].lower() == "start" else system.stop_service(name, True)

    if len(words) >= 3 and words[0].lower() in {"kill","terminate"} and words[1].lower() == "process":
        if not allow:
            raise PermissionError("Process termination requires confirmation. Use 'confirm kill process NAME'.")
        return system.kill_process(" ".join(words[2:]), True)

    if body_low.startswith("processes ") or body_low.startswith("process list "):
        return system.processes(body.split(" ", 1)[1])

    if body_low == "processes" or body_low == "process list" or body_low == "running processes":
        return system.processes()

    if body_low.startswith("event logs"):
        parts = body.split()
        log_name = "System"
        count = 30
        for item in parts[2:]:
            if item.lower() in {"system","application","security"}:
                log_name = item.title()
            elif item.isdigit():
                count = int(item)
        return system.event_logs(log_name, count)

    if body_low.startswith("set user env ") or body_low.startswith("set machine env ") or body_low.startswith("set process env "):
        if not allow:
            raise PermissionError("Changing environment variables requires confirmation.")
        parts = body.split(" ", 3)
        scope = parts[1].title()
        pair = parts[3]
        if "=" not in pair:
            raise ValueError("Use: set user env NAME=value")
        name, value = pair.split("=", 1)
        return system.set_environment_variable(name, value, scope, True)

    if body_low.startswith("set power plan "):
        if not allow:
            raise PermissionError("Changing the power plan requires confirmation.")
        return system.set_power_plan(body[15:].strip(), True)

    if body_low in {"clean temp","clean temporary files","temp cleanup"}:
        return system.clear_temp(dry_run=not allow, allow_dangerous=allow)

    if body_low in {"shutdown","shut down","turn off computer"}:
        if not allow:
            raise PermissionError("Shutdown requires confirmation. Use 'confirm shutdown'.")
        return system.shutdown(False, True)

    if body_low in {"restart","reboot","restart computer","reboot computer"}:
        if not allow:
            raise PermissionError("Restart requires confirmation. Use 'confirm restart'.")
        return system.shutdown(True, True)

    return None

def execute(command: str, on_step=None, allow_dangerous: bool=False) -> str:
    desktop.STOP.clear()
    normalized = desktop.normalize_hinglish(command)
    steps = desktop.split_steps(normalized)
    results = []
    for index, step in enumerate(steps, 1):
        desktop.wait_if_paused()
        if desktop.STOP.is_set():
            raise RuntimeError("Task stopped.")
        if on_step:
            on_step(index, len(steps), step)
        result = _system(step)
        if result is None:
            result = desktop.execute_one(step, allow_dangerous=allow_dangerous)
        results.append(result)
    return "\n".join(results)

def run_command(command: str) -> bool:
    try:
        allow = _auto_allowed()
        result = execute(command, allow_dangerous=allow)
        desktop.TASK_CONTEXT.append({"user":command,"assistant":str(result)[:3000]})
        desktop.TASK_CONTEXT[:] = desktop.TASK_CONTEXT[-20:]
        desktop.log(result)
        desktop.speak(result.splitlines()[-1][:250])
        desktop.relay_result("COMPLETED", result)
        return True
    except Exception as exc:
        message = str(exc) or "Unknown error"
        desktop.log("ERROR: Command failed: " + message)
        desktop.TASK_CONTEXT.append({"user":command,"assistant":"ERROR: "+message})
        desktop.TASK_CONTEXT[:] = desktop.TASK_CONTEXT[-20:]
        desktop.speak("Command failed. Retry.")
        desktop.relay_result("FAILED", message)
        return False

desktop.run_command = run_command

if __name__ == "__main__":
    if os.name != "nt":
        raise SystemExit("SANVI Universal is currently designed for Windows.")
    desktop.interactive()
