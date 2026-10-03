"""SANVI Windows system administration toolkit.

The functions in this module are intentionally structured instead of exposing an
unrestricted shell to the planner. Read-only operations are available normally.
State-changing administrative operations require the caller to pass
allow_dangerous=True, unless the operation is explicitly marked safe.
"""

from __future__ import annotations

import ctypes
import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any


def _run_ps(command: str, timeout: int = 60, elevated: bool = False) -> str:
    if platform.system() != "Windows":
        raise RuntimeError("Windows administration tools are only available on Windows.")
    if elevated and not is_admin():
        raise PermissionError("This operation requires an elevated SANVI session. Start SANVI with start_sanvi_admin.bat.")
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    output = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode:
        raise RuntimeError(output or f"PowerShell failed with exit code {completed.returncode}.")
    return output or "Operation completed."


def is_admin() -> bool:
    if platform.system() != "Windows":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def privilege_status() -> str:
    return json.dumps({
        "platform": platform.platform(),
        "user": os.getenv("USERNAME") or os.getenv("USER") or "",
        "is_admin": is_admin(),
        "elevated_runtime": is_admin(),
    }, indent=2)


def system_overview() -> str:
    command = """
$os=Get-CimInstance Win32_OperatingSystem
$cs=Get-CimInstance Win32_ComputerSystem
$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1
[pscustomobject]@{
 Computer=$env:COMPUTERNAME
 User=$env:USERNAME
 OS=$os.Caption
 Version=$os.Version
 Build=$os.BuildNumber
 Architecture=$os.OSArchitecture
 Manufacturer=$cs.Manufacturer
 Model=$cs.Model
 RAM_GB=[math]::Round($cs.TotalPhysicalMemory/1GB,2)
 CPU=$cpu.Name
 Cores=$cpu.NumberOfCores
 Threads=$cpu.NumberOfLogicalProcessors
 BootTime=$os.LastBootUpTime
 Admin=(New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
} | ConvertTo-Json
"""
    return _run_ps(command)


def disk_usage() -> str:
    return _run_ps("Get-PSDrive -PSProvider FileSystem | Select-Object Name,Used,Free,@{N='UsedGB';E={[math]::Round($_.Used/1GB,2)}},@{N='FreeGB';E={[math]::Round($_.Free/1GB,2)}} | ConvertTo-Json")


def network_overview() -> str:
    command = """
[pscustomobject]@{
 Adapters=Get-NetAdapter | Select-Object Name,Status,LinkSpeed,MacAddress
 IP=Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias,IPAddress,PrefixLength
 Routes=Get-NetRoute -AddressFamily IPv4 | Select-Object DestinationPrefix,NextHop,InterfaceAlias,RouteMetric
 DNS=Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object InterfaceAlias,ServerAddresses
} | ConvertTo-Json -Depth 5
"""
    return _run_ps(command)


def listening_ports() -> str:
    return _run_ps("Get-NetTCPConnection -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess,@{N='Process';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} | Sort-Object LocalPort | ConvertTo-Json")


def services(filter_text: str = "") -> str:
    if filter_text:
        safe = filter_text.replace("'", "''")
        command = f"Get-Service -Name '*{safe}*' -ErrorAction SilentlyContinue | Select-Object Name,DisplayName,Status,StartType | ConvertTo-Json"
    else:
        command = "Get-Service | Sort-Object Status,DisplayName | Select-Object Name,DisplayName,Status,StartType | ConvertTo-Json"
    return _run_ps(command)


def start_service(name: str, allow_dangerous: bool = False) -> str:
    if not allow_dangerous:
        raise PermissionError("Starting/stopping Windows services requires confirmation. Use 'confirm service start <name>'.")
    safe = name.replace("'", "''")
    return _run_ps(f"Start-Service -Name '{safe}' -ErrorAction Stop; Get-Service -Name '{safe}' | Select-Object Name,Status | ConvertTo-Json", elevated=True)


def stop_service(name: str, allow_dangerous: bool = False) -> str:
    if not allow_dangerous:
        raise PermissionError("Starting/stopping Windows services requires confirmation. Use 'confirm service stop <name>'.")
    safe = name.replace("'", "''")
    return _run_ps(f"Stop-Service -Name '{safe}' -Force -ErrorAction Stop; Get-Service -Name '{safe}' | Select-Object Name,Status | ConvertTo-Json", elevated=True)


def processes(filter_text: str = "") -> str:
    if filter_text:
        safe = filter_text.replace("'", "''")
        command = f"Get-Process -Name '*{safe}*' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,WorkingSet,Path | ConvertTo-Json"
    else:
        command = "Get-Process | Select-Object Id,ProcessName,CPU,WorkingSet,Path | Sort-Object ProcessName | ConvertTo-Json"
    return _run_ps(command)


def kill_process(name_or_pid: str, allow_dangerous: bool = False) -> str:
    if not allow_dangerous:
        raise PermissionError("Terminating a process requires confirmation. Use 'confirm kill <name-or-pid>'.")
    target = name_or_pid.strip()
    if target.isdigit():
        command = f"Stop-Process -Id {int(target)} -Force -ErrorAction Stop"
    else:
        safe = target.replace("'", "''")
        command = f"Stop-Process -Name '{safe}' -Force -ErrorAction Stop"
    return _run_ps(command, elevated=True)


def installed_software() -> str:
    command = r"""
$paths=@(
 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
 'HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
Get-ItemProperty $paths -ErrorAction SilentlyContinue |
Where-Object DisplayName |
Select-Object DisplayName,DisplayVersion,Publisher,InstallDate |
Sort-Object DisplayName |
ConvertTo-Json
"""
    return _run_ps(command, timeout=90)


def environment_variables() -> str:
    return _run_ps("Get-ChildItem Env: | Sort-Object Name | Select-Object Name,Value | ConvertTo-Json")


def set_environment_variable(name: str, value: str, scope: str = "User", allow_dangerous: bool = False) -> str:
    if not allow_dangerous:
        raise PermissionError("Changing environment variables requires confirmation. Use 'confirm env set ...'.")
    if not name or any(c in name for c in "\\/:"):
        raise ValueError("Invalid environment variable name.")
    scope = scope.title()
    if scope not in {"User", "Machine", "Process"}:
        raise ValueError("Scope must be User, Machine, or Process.")
    if scope == "Machine" and not is_admin():
        raise PermissionError("Machine environment changes require an elevated SANVI session.")
    # Process scope is handled locally; User/Machine use .NET environment APIs.
    if scope == "Process":
        os.environ[name] = value
        return f"Set process environment variable {name}."
    escaped_name = name.replace("'", "''")
    escaped_value = value.replace("'", "''")
    return _run_ps(f"[Environment]::SetEnvironmentVariable('{escaped_name}','{escaped_value}','{scope}'); 'Set {scope} environment variable {escaped_name}.'", elevated=(scope == "Machine"))


def scheduled_tasks(filter_text: str = "") -> str:
    command = "Get-ScheduledTask | Select-Object TaskName,TaskPath,State | Sort-Object TaskPath,TaskName"
    if filter_text:
        safe = filter_text.replace("'", "''")
        command = f"Get-ScheduledTask | Where-Object {{$_.TaskName -like '*{safe}*' -or $_.TaskPath -like '*{safe}*'}} | Select-Object TaskName,TaskPath,State | Sort-Object TaskPath,TaskName"
    return _run_ps(command + " | ConvertTo-Json")


def startup_items() -> str:
    command = r"""
$items=@()
$items += Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location,User
$items += Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue | Select-Object PSObject.Properties.Name,PSObject.Properties.Value
$items | ConvertTo-Json -Depth 4
"""
    return _run_ps(command)


def event_logs(log_name: str = "System", count: int = 30) -> str:
    allowed = {"System", "Application", "Security"}
    if log_name not in allowed:
        raise ValueError(f"log_name must be one of {sorted(allowed)}")
    count = max(1, min(int(count), 200))
    return _run_ps(f"Get-WinEvent -LogName '{log_name}' -MaxEvents {count} -ErrorAction Stop | Select-Object TimeCreated,Id,LevelDisplayName,ProviderName,Message | ConvertTo-Json -Depth 4", timeout=90)


def firewall_rules() -> str:
    return _run_ps("Get-NetFirewallRule | Select-Object DisplayName,Enabled,Direction,Action,Profile | Sort-Object DisplayName | ConvertTo-Json")


def set_firewall_rule(name: str, enabled: bool, allow_dangerous: bool = False) -> str:
    if not allow_dangerous:
        raise PermissionError("Firewall changes require confirmation. Use 'confirm firewall ...'.")
    safe = name.replace("'", "''")
    action = "Enable-NetFirewallRule" if enabled else "Disable-NetFirewallRule"
    return _run_ps(f"{action} -DisplayName '{safe}' -ErrorAction Stop; Get-NetFirewallRule -DisplayName '{safe}' | Select-Object DisplayName,Enabled,Direction,Action | ConvertTo-Json", elevated=True)


def power_plan() -> str:
    return _run_ps("powercfg /getactivescheme")


def set_power_plan(plan: str, allow_dangerous: bool = False) -> str:
    if not allow_dangerous:
        raise PermissionError("Changing the power plan requires confirmation.")
    choices = {
        "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
        "high performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "power saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
    }
    key = plan.strip().lower()
    if key not in choices:
        raise ValueError("Supported plans: balanced, high performance, power saver.")
    return _run_ps(f"powercfg /setactive {choices[key]}")


def clear_temp(dry_run: bool = True, allow_dangerous: bool = False) -> str:
    if dry_run:
        return _run_ps("$targets=@($env:TEMP,$env:WINDIR+'\\Temp'); $targets | ForEach-Object { Get-ChildItem $_ -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum } | ConvertTo-Json")
    if not allow_dangerous:
        raise PermissionError("Cleaning temporary files requires confirmation.")
    command = """
$targets=@($env:TEMP,$env:WINDIR+'\\Temp')
foreach($target in $targets){ Get-ChildItem $target -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue }
'Temporary-file cleanup completed.'
"""
    return _run_ps(command, elevated=True)


def shutdown(restart: bool = False, allow_dangerous: bool = False) -> str:
    if not allow_dangerous:
        raise PermissionError("Power operations require confirmation.")
    command = "Restart-Computer -Force" if restart else "Stop-Computer -Force"
    return _run_ps(command, elevated=True)
