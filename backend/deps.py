"""
backend/deps.py
---------------
FastAPI dependency that provides a Database instance.
Using a simple per-request connection for SQLite (thread-safe enough for personal use).
"""

from typing import Generator
from backend.db import Database
from backend.config import settings


def get_db() -> Generator[Database, None, None]:
    db = Database(settings.DB_PATH)
    try:
        yield db
    finally:
        db.close()
