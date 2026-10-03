"""
SANVI hosted-bridge worker.

Executes hosted commands through the Universal local runtime so the hosted
dashboard can use the same structured Windows/system capabilities as the
desktop application.
"""
from __future__ import annotations
import os
import time
import httpx
from sanvi_universal import execute
from sanvi_desktop import log, speak, STOP, PAUSE

SERVER = os.getenv("SANVI_SERVER_URL", "").rstrip("/")
TOKEN = os.getenv("SANVI_AGENT_TOKEN", "").strip()

def headers() -> dict[str,str]:
    return {"X-SANVI-Agent-Token": TOKEN}

def report(task_id: str, status: str, message: str, step: int = 1, total: int = 1, description: str = "") -> None:
    with httpx.Client(timeout=15) as client:
        client.post(
            f"{SERVER}/api/agent/result",
            headers=headers(),
            json={"task_id":task_id,"status":status,"message":message,
                  "current_step":step,"total_steps":total,
                  "current_description":description or message[:500]},
        )

def main() -> None:
    if not SERVER or not TOKEN:
        raise SystemExit("Set SANVI_SERVER_URL and SANVI_AGENT_TOKEN first.")
    log(f"Universal hosted bridge connected: {SERVER}")
    with httpx.Client(timeout=10) as client:
        while True:
            try:
                client.post(f"{SERVER}/api/agent/heartbeat",headers=headers(),timeout=5)
                response=client.get(f"{SERVER}/api/agent/next",headers=headers(),timeout=5)
                response.raise_for_status()
                task=response.json().get("task")
                if not task:
                    time.sleep(0.35)
                    continue
                task_id=task["task_id"]
                command=task["command"]
                os.environ["SANVI_CURRENT_TASK_ID"]=task_id
                log(f"REMOTE TASK {task_id}: {command}")

                def progress(step:int,total:int,description:str)->None:
                    try:
                        state=client.get(f"{SERVER}/api/tasks/{task_id}",timeout=5).json().get("status")
                        if state=="CANCELLED":
                            STOP.set()
                            PAUSE.clear()
                            raise RuntimeError("Task cancelled by user.")
                        if state=="PAUSED":
                            PAUSE.set()
                        else:
                            PAUSE.clear()
                        report(task_id,"PAUSED" if state=="PAUSED" else "RUNNING",
                               f"Executing step {step}/{total}: {description}",step,total,description)
                    except RuntimeError:
                        raise
                    except Exception:
                        pass

                try:
                    allow=os.getenv("SANVI_ALLOW_AUTOMATIC_DANGEROUS","").lower() in {"1","true","yes"}
                    result=execute(command,on_step=progress,allow_dangerous=allow)
                    report(task_id,"COMPLETED",result,1,1,result[:500])
                    speak(result.splitlines()[-1][:250])
                except Exception as exc:
                    report(task_id,"FAILED",str(exc),1,1,str(exc)[:500])
                    speak("Command failed. Retry.")
                finally:
                    os.environ.pop("SANVI_CURRENT_TASK_ID",None)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                log(f"Universal bridge connection: {exc}")
                time.sleep(2)

if __name__=="__main__":
    main()
