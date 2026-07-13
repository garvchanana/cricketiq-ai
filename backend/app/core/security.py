"""
Phase 11.6 — Security configuration
core/security.py

Provides:
- CORS middleware configuration
- Rate limiting setup
- Trusted host configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware


# ---------------------------------------------------------------------------
# Rate limiter — shared instance imported by routes
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# CORS origins
# ---------------------------------------------------------------------------

ALLOWED_ORIGINS = [
    "http://localhost:8501",    # Streamlit frontend
    "http://127.0.0.1:8501",   # Streamlit frontend (alternate)
    "http://localhost:3000",    # React frontend (future)
    "http://127.0.0.1:3000",   # React frontend (alternate)
]


def configure_security(app: FastAPI) -> None:
    """
    Apply all security middleware to the FastAPI app.
    Call this once during app creation.

    Phase 11.6 — adds:
    1. CORS middleware — allows Streamlit frontend to call the API
    2. Rate limiting middleware — prevents abuse of LLM endpoints
    """

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins     = ALLOWED_ORIGINS,
        allow_credentials = True,
        allow_methods     = ["GET", "POST"],
        allow_headers     = ["*"],
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)