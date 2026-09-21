"""Vercel-compatible FastAPI entry point."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "dashboard" / "static"
TEMPLATES_DIR = BASE_DIR / "dashboard" / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="SANVI AI", version="0.1.3")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    index = TEMPLATES_DIR / "index.html"
    if not index.exists():
        return "<h1>SANVI AI</h1><p>Dashboard template is not deployed yet.</p>"
    return index.read_text(encoding="utf-8")

@app.get("/api/health")
async def health():
    return {"ok": True, "name": "SANVI AI", "mode": "hosted", "automation": "local-agent-required"}

@app.get("/api/status")
async def status():
    return await health()
