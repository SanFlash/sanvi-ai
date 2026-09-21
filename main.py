"""SANVI AI hosted dashboard/API entry point.

Render hosts the web dashboard and API. Desktop/Android automation is performed
by the local SANVI agent; the hosted service never attempts to access Render's
nonexistent desktop, microphone, USB, or Android devices.
"""

from contextlib import asynccontextmanager
from pathlib import Path
import os
import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
TEMPLATES_DIR = DASHBOARD_DIR / "templates"
STATIC_DIR = DASHBOARD_DIR / "static"
SCREENSHOT_DIR = BASE_DIR / "runtime" / "screenshots"

TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("sanvi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SANVI AI hosted service starting")
    yield
    logger.info("SANVI AI hosted service stopped")


app = FastAPI(
    title="SANVI AI",
    version="0.1.3",
    description="SANVI AI hosted dashboard/API",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class CommandRequest(BaseModel):
    command: str
    source: str = "text"


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> str:
    index = TEMPLATES_DIR / "index.html"
    if not index.exists():
        return "<h1>SANVI AI</h1><p>Dashboard template is not deployed yet.</p>"
    return index.read_text(encoding="utf-8")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "name": "SANVI AI",
        "mode": os.getenv("SANVI_MODE", "production"),
        "automation": "local-agent-required",
    }


@app.get("/api/status")
async def status() -> dict[str, Any]:
    return await health()


@app.post("/api/command")
async def command(request: CommandRequest) -> dict[str, Any]:
    command_text = request.command.strip()
    if not command_text:
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    # Hosted Render cannot safely execute arbitrary Windows/PowerShell/ADB
    # commands. Return an explicit handoff state rather than pretending the
    # physical-device task was executed.
    return {
        "task_id": None,
        "status": "LOCAL_AGENT_REQUIRED",
        "message": "Command received. Connect the local SANVI agent to execute it.",
        "command": command_text,
        "source": request.source,
    }


@app.get("/api/screenshot/latest")
async def latest_screenshot():
    candidates = sorted(
        SCREENSHOT_DIR.glob("*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and path.is_file():
            return FileResponse(path)
    raise HTTPException(status_code=404, detail="No local-agent screenshot available")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("SANVI_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
