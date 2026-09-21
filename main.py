"""SANVI AI hosted real-time command bridge."""
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio, base64, logging, os, time, uuid
from typing import Any
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR=Path(__file__).resolve().parent
TEMPLATES_DIR=BASE_DIR/"dashboard"/"templates"
STATIC_DIR=BASE_DIR/"dashboard"/"static"
SCREENSHOT_DIR=BASE_DIR/"runtime"/"screenshots"
for d in (TEMPLATES_DIR,STATIC_DIR,SCREENSHOT_DIR): d.mkdir(parents=True,exist_ok=True)

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO").upper())
logger=logging.getLogger("sanvi")
AGENT_TOKEN=os.getenv("SANVI_AGENT_TOKEN","").strip()
tasks:dict[str,dict[str,Any]]={}
queue:asyncio.Queue[str]=asyncio.Queue()
last_agent_heartbeat:float=0.0

@asynccontextmanager
async def lifespan(app:FastAPI):
    logger.info("SANVI real-time bridge started")
    yield

app=FastAPI(title="SANVI AI",version="0.2.0",lifespan=lifespan)
app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

class CommandRequest(BaseModel):
    command:str
    source:str="text"

class ScreenshotRequest(BaseModel):
    filename:str="desktop.png"
    data_b64:str

class AgentResult(BaseModel):
    task_id:str
    status:str
    message:str=""
    current_step:int=0
    total_steps:int=1
    current_description:str=""

def auth(token:str|None):
    if not AGENT_TOKEN: raise HTTPException(503,"SANVI_AGENT_TOKEN is not configured")
    if token!=AGENT_TOKEN: raise HTTPException(401,"Invalid SANVI agent token")

@app.get("/",response_class=HTMLResponse)
async def root():
    return """<!doctype html><html><head><meta charset="utf-8"><title>SANVI AI</title></head>
    <body style="font-family:system-ui;background:#070b14;color:#e8eefc;padding:40px">
    <h1>SANVI AI local controller</h1><p>The Windows/Android executor runs on your PC, not inside this webpage.</p>
    <p>Start <code>start_sanvi.bat</code> on Windows and issue commands directly to SANVI.</p>
    <p>The web dashboard is optional: <a href="/dashboard" style="color:#7fb0ff">open dashboard</a>.</p>
    </body></html>"""

@app.get("/dashboard",response_class=HTMLResponse)
async def dashboard():
    p=TEMPLATES_DIR/"index.html"
    return p.read_text(encoding="utf-8") if p.exists() else "<h1>SANVI AI</h1>"

@app.get("/api/health")
async def health():
    connected = bool(last_agent_heartbeat and (time.time() - last_agent_heartbeat) < 10)
    return {"ok":True,"name":"SANVI AI","mode":os.getenv("SANVI_MODE","production"),"agent_required":True,"agent_connected":connected,"last_agent_heartbeat":last_agent_heartbeat}

@app.get("/api/status")
async def status(): return await health()

@app.post("/api/command")
async def command(r:CommandRequest):
    text=r.command.strip()
    if not text: raise HTTPException(400,"Command cannot be empty")
    tid=uuid.uuid4().hex
    tasks[tid]={"task_id":tid,"status":"PENDING","current_step":0,"total_steps":1,
      "current_description":"Waiting for local Windows agent","message":"Command queued",
      "command":text,"source":r.source,"created_at":time.time(),"updated_at":time.time()}
    await queue.put(tid)
    return {"task_id":tid,"status":"PENDING","message":"Command queued"}

@app.get("/api/tasks/{task_id}")
async def get_task(task_id:str):
    if task_id not in tasks: raise HTTPException(404,"Task not found")
    return tasks[task_id]

@app.get("/api/agent/next")
async def agent_next(x_sanvi_agent_token:str|None=Header(default=None)):
    auth(x_sanvi_agent_token)
    try: tid=await asyncio.wait_for(queue.get(),timeout=1)
    except asyncio.TimeoutError: return {"task":None}
    task=tasks.get(tid)
    if not task:return {"task":None}
    task.update(status="RUNNING",current_description="Executing on local Windows agent",updated_at=time.time())
    return {"task":task}

@app.post("/api/agent/result")
async def agent_result(r:AgentResult,x_sanvi_agent_token:str|None=Header(default=None)):
    auth(x_sanvi_agent_token)
    if r.task_id not in tasks: raise HTTPException(404,"Task not found")
    tasks[r.task_id].update(status=r.status,message=r.message,current_step=r.current_step,
      total_steps=r.total_steps,current_description=r.current_description,updated_at=time.time())
    return {"ok":True}

@app.post("/api/agent/heartbeat")
async def heartbeat(x_sanvi_agent_token:str|None=Header(default=None)):
    global last_agent_heartbeat
    auth(x_sanvi_agent_token)
    last_agent_heartbeat=time.time()
    return {"ok":True,"server_time":last_agent_heartbeat}

@app.post("/api/agent/screenshot")
async def agent_screenshot(r:ScreenshotRequest,x_sanvi_agent_token:str|None=Header(default=None)):
    auth(x_sanvi_agent_token)
    try:
        raw=base64.b64decode(r.data_b64,validate=True)
    except Exception:
        raise HTTPException(400,"Invalid screenshot data")
    safe_name=Path(r.filename).name
    if Path(safe_name).suffix.lower() not in {".png",".jpg",".jpeg",".webp"}:
        safe_name="desktop.png"
    target=SCREENSHOT_DIR/safe_name
    target.write_bytes(raw)
    return {"ok":True,"filename":safe_name,"bytes":len(raw)}

@app.get("/api/screenshot/latest")
async def screenshot():
    files=sorted(SCREENSHOT_DIR.glob("*"),key=lambda p:p.stat().st_mtime,reverse=True)
    for p in files:
        if p.suffix.lower() in {".png",".jpg",".jpeg",".webp"}: return FileResponse(p)
    raise HTTPException(404,"No screenshot available")

@app.post("/api/tasks/{task_id}/stop")
async def stop(task_id:str):
    if task_id not in tasks: raise HTTPException(404,"Task not found")
    tasks[task_id].update(status="CANCELLED",current_description="Stop requested",updated_at=time.time())
    return tasks[task_id]

@app.post("/api/tasks/{task_id}/pause")
async def pause(task_id:str):
    if task_id not in tasks: raise HTTPException(404,"Task not found")
    tasks[task_id].update(status="PAUSED",updated_at=time.time()); return tasks[task_id]

@app.post("/api/tasks/{task_id}/resume")
async def resume(task_id:str):
    if task_id not in tasks: raise HTTPException(404,"Task not found")
    tasks[task_id].update(status="RUNNING",updated_at=time.time()); return tasks[task_id]

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=int(os.getenv("PORT","8000")))
