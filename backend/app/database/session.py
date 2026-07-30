"""
Phase 12.2 (final) — SQLite-based session for deployment

Uses a pre-built SQLite file (cricketiq.db) committed to git.
This solves the free-tier persistence problem — since the file
is part of the repository, it survives every redeploy on Render's
free tier, unlike a runtime-generated database on ephemeral disk.

Local development can still use MySQL by setting USE_SQLITE=false
in .env — this file supports both modes.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# ---------------------------------------------------------------------------
# Determine which database to use
# ---------------------------------------------------------------------------

USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    # SQLite — used for deployment (Render free tier)
    #
    # Path differs between local dev and Docker/Render:
    #   Local:  backend/app/database/session.py -> 4 parents -> project root
    #           (cricketiq.db lives in project root locally)
    #   Docker: /app/app/database/session.py -> cricketiq.db copied to /app
    #           via "COPY cricketiq.db ." in the Dockerfile (2 parents up
    #           from this file's Docker location reaches /app)
    #
    # Try the Docker-flattened location first (2 parents), fall back
    # to the local dev nested location (4 parents) if not found.
    _docker_path = Path(__file__).resolve().parent.parent / "cricketiq.db"
    _local_path  = Path(__file__).resolve().parent.parent.parent.parent / "cricketiq.db"

    DB_PATH = _docker_path if _docker_path.exists() else _local_path
    DATABASE_URL = f"sqlite:///{DB_PATH}"

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

else:
    # MySQL — used for local development
    DATABASE_URL = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
        f"/{settings.MYSQL_DATABASE}"
    )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()