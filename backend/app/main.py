"""
Personal Financial Manager — FastAPI Backend
Entry point: registers all routers, configures CORS, adds health check.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth_router import router as auth_router
from app.routers.vaults import router as vaults_router
from app.routers.transactions import router as transactions_router
from app.routers.bulk import router as bulk_router
from app.routers.misc_routers import (
    categories_router,
    units_router,
    tags_router,
    settings_router,
    dashboard_router,
    users_router,
    analytics_router,
)
VERSION="0.3.5"

app = FastAPI(
    title="Personal Financial Manager API",
    description="FastAPI backend for the PFM app — vaults, transactions, bulk entry, and more.",
    version=VERSION,
    docs_url="/docs",      # Swagger UI at /docs
    redoc_url="/redoc",    # ReDoc at /redoc
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allows the React frontend (running on a different port) to call the API.
# In production, replace "*" with your actual frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # Tighten this in production: ["http://192.168.x.x:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router,         prefix=API_PREFIX)
app.include_router(dashboard_router,    prefix=API_PREFIX)
app.include_router(vaults_router,       prefix=API_PREFIX)
app.include_router(transactions_router, prefix=API_PREFIX)
app.include_router(bulk_router,         prefix=API_PREFIX)
app.include_router(categories_router,   prefix=API_PREFIX)
app.include_router(units_router,        prefix=API_PREFIX)
app.include_router(tags_router,         prefix=API_PREFIX)
app.include_router(users_router,        prefix=API_PREFIX)
app.include_router(analytics_router,    prefix=API_PREFIX)
app.include_router(settings_router,     prefix=API_PREFIX)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    """Simple liveness probe — useful for Docker health checks."""
    return {"status": "ok", "version": VERSION}


@app.get("/", tags=["Health"])
def root():
    return {"message": "PFM API is running. Visit /docs for the interactive API explorer."}
