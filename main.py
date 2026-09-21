from contextlib import asynccontextmanager
from pathlib import Path
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "dashboard" / "templates"
STATIC_DIR = BASE_DIR / "dashboard" / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="SANVI AI", version="0.1.2", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")

@app.get("/api/status")
async def status():
    return {"status": "online", "mode": os.getenv("SANVI_MODE", "development")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("SANVI_HOST","127.0.0.1"), port=int(os.getenv("PORT","8000")))
