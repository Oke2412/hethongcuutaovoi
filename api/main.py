"""
api/main.py — Lightweight FastAPI service.
Serves Health checks, Desktop App Adapter (/api), and Core Brain hooks.
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.desktop import router as desktop_router
from db.database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and FTS5 triggers on startup
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as exc:
        logger.warning(f"Database initialization encountered an error: {exc}")
    yield


app = FastAPI(
    title="Amazing Nobel API",
    version="0.2.0",
    description="Raphael Life OS API & Desktop Assistant Adapter",
    lifespan=lifespan,
)

# Enable CORS for Desktop Overlay (Electron, Next.js static, Tailscale)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Desktop Adapter routes
app.include_router(desktop_router, prefix="/api")


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "ts": datetime.now(timezone.utc).isoformat()})


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"message": "Amazing Nobel API is running with Desktop Adapter active."})
