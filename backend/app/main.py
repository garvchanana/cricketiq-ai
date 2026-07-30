"""
Phase 11.6 — Updated main.py

Fixes:
- Migrated from deprecated @app.on_event to lifespan context manager
- Added structured logging setup on startup
- Added security middleware (CORS + rate limiting)
- Eliminates MovedIn20Warning from startup
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.core.logging_config import setup_logging
from app.core.security      import configure_security
from app.database.init_db   import init_db
from app.database.session   import SessionLocal

from app.api.routes.ingestion            import router as ingestion_router
from app.api.routes.historical_ingestion import router as historical_router
from app.api.routes.feature_engineering  import router as feature_router
from app.api.routes.rag_routes           import router as rag_router
from app.api.routes.sql_agent_routes     import router as sql_agent_router
from app.api.routes.hybrid_routes        import router as hybrid_router
from app.api.routes.debug_routes import router as debug_router

from app.rag.vectorstore.vector_indexing_service import VectorIndexingService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase 11.6 — lifespan replaces deprecated @app.on_event("startup")
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Replaces the deprecated @app.on_event("startup") pattern.
    Runs setup on startup, cleanup on shutdown.
    """

    # ── Startup ──────────────────────────────────────────────────────────
    setup_logging(log_level="INFO")
    logger.info("CricketIQ AI starting up...")

    # Initialise database tables
    init_db()
    logger.info("Database initialised.")

    # Load or build FAISS index
    db = SessionLocal()
    try:
        result = VectorIndexingService.build_player_index(db=db)
        logger.info(
            "FAISS index ready — %d players, source: %s",
            result["players_indexed"],
            result["source"]
        )
    finally:
        db.close()

    logger.info("CricketIQ AI startup complete.")

    yield  # application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("CricketIQ AI shutting down.")


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title       = "CricketIQ AI",
    version     = "1.0.0",
    description = "Cricket Intelligence Platform — RAG + SQL Agent + Hybrid",
    lifespan    = lifespan
)

# Phase 11.6 — security middleware
configure_security(app)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(ingestion_router)
app.include_router(historical_router)
app.include_router(feature_router)
app.include_router(rag_router)
app.include_router(sql_agent_router)
app.include_router(hybrid_router)
app.include_router(debug_router)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "CricketIQ AI Backend Running",
        "version": "1.0.0",
        "phase":   "11.6 — Production Hardening",
        "docs":    "/docs"
    }