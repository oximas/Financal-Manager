"""
backend/main.py
---------------
FastAPI application entry point.

Run with:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

  --host 0.0.0.0   makes it reachable on your local network (phone on same WiFi)
  --reload         auto-restarts on code changes (dev only)

Interactive API docs:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers.auth import router as auth_router
from backend.routers.vaults import router as vaults_router
from backend.routers.transactions import router as transactions_router
from backend.routers.lookup import (
    categories_router,
    units_router,
    settings_router,
    summary_router,
)
from backend.routers.export import router as export_router

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=(
        "Personal Financial Manager API. "
        "All endpoints except /auth/login and /auth/signup require a Bearer JWT token."
    ),
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allows your React frontend (running on port 5173) to call this API.
# Also allows your phone browser when on the same WiFi.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(vaults_router)
app.include_router(transactions_router)
app.include_router(categories_router)
app.include_router(units_router)
app.include_router(settings_router)
app.include_router(summary_router)
app.include_router(export_router)


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/", tags=["meta"])
def root():
    return {
        "message": f"{settings.APP_TITLE} API",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }
