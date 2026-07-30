"""
Phase 12.3 — Temporary debug endpoint
Add this router to main.py TEMPORARILY to diagnose the production
SQLite table issue. Remove after debugging is complete.
"""

from fastapi import APIRouter
from sqlalchemy import text
from app.database.session import SessionLocal, DATABASE_URL

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/db-info")
def db_info():
    """Shows exactly which SQLite file is being used and what tables exist."""

    db = SessionLocal()
    try:
        tables = db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ).fetchall()

        table_names = [t[0] for t in tables]

        # Also check row counts for key tables if they exist
        counts = {}
        for table in ["players", "player_batting_stats", "ball_by_ball"]:
            if table in table_names:
                count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                counts[table] = count
            else:
                counts[table] = "TABLE MISSING"

        return {
            "database_url": DATABASE_URL,
            "total_tables": len(table_names),
            "tables": table_names,
            "row_counts": counts
        }
    finally:
        db.close()