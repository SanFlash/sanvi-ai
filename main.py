"""SANVI AI application entry point.

The application uses FastAPI's lifespan API for startup/shutdown and runs
Uvicorn when this file is executed directly.
"""

from contextlib import asynccontextmanager
from pathlib import Path
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.routes import register
from android.adb import list_devices
from browser.playwright_agent import browser_search
from config.settings import settings
from core.agent import SanviAgent
from core.executor import Executor
from core.tool_router import ToolRouter
from database.database import init_db
from windows.applications import open_application
from windows.screenshots import take_screenshot

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = BASE_DIR / "dashboard"
TEMPLATES_DIR = DASHBOARD_DIR / "templates"
STATIC_DIR = DASHBOARD_DIR / "static"

# Render/Git checkouts can omit empty directories. Create the runtime
# directories before mounting/reading them so startup never fails because
# dashboard/static or dashboard/templates is missing.
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("sanvi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and clean up application resources."""
    logger.info("Starting SANVI AI")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("SANVI AI shutdown complete")


app = FastAPI(
    title="SANVI AI",
    version="0.1.2",
    description="Local-first Windows and Android automation assistant",
    lifespan=lifespan,
)

state: dict = {}
router = ToolRouter()
router.register("open_application", open_application)
router.register("take_screenshot", take_screenshot)
router.register("list_devices", list_devices)
router.register("browser_search", browser_search)
router.register("explain", lambda message: {"success": True, "message": message})

executor = Executor(router, state)
agent = SanviAgent(executor)
app.include_router(register(agent, state, executor))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> str:
    return (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "name": "SANVI AI", "mode": settings.sanvi_mode}


def run() -> None:
    """Start the local Uvicorn server."""
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
