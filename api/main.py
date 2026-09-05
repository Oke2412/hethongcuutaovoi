"""
api/main.py � Lightweight FastAPI service.
Handles health checks and future extensions (calendar webhooks, dashboard).
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI(title="Amazing Nobel API", version="0.1.0")


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "ts": datetime.utcnow().isoformat()})


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"message": "Amazing Nobel API is running."})
