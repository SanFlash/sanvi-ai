from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parents[1]
app = FastAPI(title="SANVI AI", version="0.1.2")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "dashboard" / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return (BASE_DIR / "dashboard" / "templates" / "index.html").read_text(encoding="utf-8")

@app.get("/api/status")
async def status():
    return {"status":"online","mode":"hosted","automation":"local-agent-required"}
