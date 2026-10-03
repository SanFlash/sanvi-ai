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
    from sanvi_planner import plan as ai_plan
except Exception:
    ai_plan = None

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
            try:
                result = desktop.execute_one(step, allow_dangerous=allow_dangerous)
            except Exception as direct_error:
                # Natural-language fallback: when deterministic routing cannot
                # identify the request, let the AI planner map it to safe tools.
                if ai_plan is None:
                    raise
                try:
                    result = desktop.execute_ai_task(step, allow_dangerous=allow_dangerous)
                except Exception:
                    raise direct_error
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

def system_action(tool, args, confirmed=False):
    allow = confirmed or _auto_allowed()
    table = {
        "system_overview": lambda: system.system_overview(),
        "privilege_status": lambda: system.privilege_status(),
        "disk_usage": lambda: system.disk_usage(),
        "network_overview": lambda: system.network_overview(),
        "listening_ports": lambda: system.listening_ports(),
        "services": lambda: system.services(str(args.get("filter_text",""))),
        "start_service": lambda: system.start_service(str(args.get("name","")), allow),
        "stop_service": lambda: system.stop_service(str(args.get("name","")), allow),
        "processes": lambda: system.processes(str(args.get("filter_text",""))),
        "kill_process": lambda: system.kill_process(str(args.get("name_or_pid","")), allow),
        "installed_software": lambda: system.installed_software(),
        "environment_variables": lambda: system.environment_variables(),
        "set_environment_variable": lambda: system.set_environment_variable(str(args.get("name","")), str(args.get("value","")), str(args.get("scope","User")), allow),
        "scheduled_tasks": lambda: system.scheduled_tasks(str(args.get("filter_text",""))),
        "startup_items": lambda: system.startup_items(),
        "event_logs": lambda: system.event_logs(str(args.get("log_name","System")), int(args.get("count",30))),
        "firewall_rules": lambda: system.firewall_rules(),
        "set_firewall_rule": lambda: system.set_firewall_rule(str(args.get("name","")), bool(args.get("enabled",True)), allow),
        "power_plan": lambda: system.power_plan(),
        "set_power_plan": lambda: system.set_power_plan(str(args.get("plan","")), allow),
        "clear_temp": lambda: system.clear_temp(bool(args.get("dry_run",True)), allow),
        "shutdown": lambda: system.shutdown(False, allow),
        "restart": lambda: system.shutdown(True, allow),
    }
    handler = table.get(tool)
    return handler() if handler else None

_desktop_ai_action = desktop.execute_ai_action

def _universal_ai_action(tool, args, original_command, allow_dangerous=False):
    result = system_action(tool, args if isinstance(args, dict) else {}, allow_dangerous)
    if result is not None:
        return result
    return _desktop_ai_action(tool, args, original_command, allow_dangerous)

desktop.execute_ai_action = _universal_ai_action

desktop.run_command = run_command

if __name__ == "__main__":
    if os.name != "nt":
        raise SystemExit("SANVI Universal is currently designed for Windows.")
    desktop.interactive()
