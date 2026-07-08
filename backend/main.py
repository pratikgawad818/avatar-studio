"""
Avatar Studio — Backend Main Application
Modular FastAPI architecture with clean routing
"""

import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# ─── Setup ──────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent
STATIC_DIR = BASE / "static"
OUTPUT_DIR = BASE / "outputs"
AVATARS_DIR = BASE / "avatars"
BG_DIR = BASE / "backgrounds"
VOICES_DIR = BASE / "voices"
TEMP_DIR = BASE / "temp"

for d in [OUTPUT_DIR, AVATARS_DIR, BG_DIR, VOICES_DIR, TEMP_DIR, STATIC_DIR]:
    d.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("studio")

# ─── FastAPI App ────────────────────────────────────────────────────
app = FastAPI(
    title="Avatar Studio API",
    version="4.0.0",
    description="Enterprise-grade AI video generation platform",
)

# ─── Middleware ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static Files ───────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")
app.mount("/avatars_img", StaticFiles(directory=AVATARS_DIR), name="avatars_img")
app.mount("/backgrounds_img", StaticFiles(directory=BG_DIR), name="backgrounds_img")

# ─── Routes ─────────────────────────────────────────────────────────
from backend.routers import voice, avatar, background, generation, video

app.include_router(voice.router)
app.include_router(avatar.router)
app.include_router(background.router)
app.include_router(generation.router)
app.include_router(video.router)

# ─── Root ───────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve frontend."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return index_file.read_text()
    return "<h1>Avatar Studio</h1><p>Frontend not built. Run: cd frontend && npm run build</p>"


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "4.0.0"}


if __name__ == "__main__":
    import uvicorn
    print("\n  🎬 Avatar Studio Backend  →  http://localhost:8002\n")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8002, reload=False)
