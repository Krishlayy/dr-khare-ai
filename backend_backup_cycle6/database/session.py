"""Backward-compatible re-exports. Prefer importing from backend.database.database."""
from backend.database.database import Base, SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
