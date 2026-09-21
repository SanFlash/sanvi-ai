"""SANVI Windows local execution agent."""
import os,re,time,subprocess,platform
from pathlib import Path
import httpx
SERVER=os.getenv("SANVI_SERVER_URL","").rstrip("/")
TOKEN=os.getenv("SANVI_AGENT_TOKEN","").strip()
def h(): return {"X-SANVI-Agent-Token":TOKEN}
def report(tid,status,msg):
    with httpx.Client(timeout=10) as c:
        c.post(f"{SERVER}/api/agent/result",headers=h(),json={"task_id":tid,"status":status,"message":msg,"current_step":1,"total_steps":1,"current_description":msg})
def execute(cmd):
    x=cmd.lower().strip()
    if re.search(r"\b(open|launch|start)\b.*\bnotepad(?:\.exe)?\b",x):
        subprocess.Popen(["notepad.exe"]); return "Notepad opened."
    if re.search(r"\b(open|launch|start)\b.*\b(calculator|calc)\b",x):
        subprocess.Popen(["calc.exe"]); return "Calculator opened."
    if re.search(r"\b(open|launch|start)\b.*\bpaint\b",x):
        subprocess.Popen(["mspaint.exe"]); return "Paint opened."
    if "open chrome" in x or "launch chrome" in x:
        candidates=[os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe")]
        for e in candidates:
            if Path(e).exists(): subprocess.Popen([e]); return "Chrome opened."
        subprocess.Popen(["cmd","/c","start","","https://www.google.com"]); return "Default browser opened."
    if "open edge" in x or "launch edge" in x:
        subprocess.Popen(["cmd","/c","start","","msedge"]); return "Edge opened."
    if x in {"hello","hi","hey sanvi","status"}: return f"Local SANVI agent online on {platform.node()}."
    raise ValueError("Unsupported safe command. Try: open Notepad, Calculator, Paint, Chrome, or Edge.")
def main():
    if not SERVER or not TOKEN: raise SystemExit("Set SANVI_SERVER_URL and SANVI_AGENT_TOKEN first.")
    print("SANVI local agent connected:",SERVER)
    with httpx.Client(timeout=5) as c:
        while True:
            try:
                r=c.get(f"{SERVER}/api/agent/next",headers=h(),timeout=3); r.raise_for_status()
                task=r.json().get("task")
                if not task: time.sleep(.5); continue
                try: msg=execute(task["command"]); report(task["task_id"],"COMPLETED",msg)
                except Exception as e: report(task["task_id"],"FAILED",str(e))
            except KeyboardInterrupt: break
            except Exception as e: print("Connection:",e); time.sleep(2)
if __name__=="__main__": main()
