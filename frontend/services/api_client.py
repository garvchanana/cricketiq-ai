import os
import requests

# ---------------------------------------------------------------------------
# Base configuration
# Phase 12.4 — reads from environment variable so the same code works
# locally (localhost:8000) and on Streamlit Cloud (Render live URL)
# without any manual code changes between environments.
# ---------------------------------------------------------------------------

BASE_URL = os.getenv(
    "BACKEND_URL",
    "https://cricketiq-ai.onrender.com"  # default — live production backend
)

TIMEOUT = 60  # Render free tier can be slow to wake from sleep


# ---------------------------------------------------------------------------
# Core request helper
# ---------------------------------------------------------------------------

def _get(endpoint: str, params: dict = None) -> dict:
    """
    Make a GET request to the backend API.
    Returns parsed JSON or an error dict.
    """
    try:
        response = requests.get(
            url     = f"{BASE_URL}{endpoint}",
            params  = params or {},
            timeout = TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        return {
            "error": "Cannot connect to backend. It may be waking up from sleep — please try again in 30 seconds.",
            "connected": False
        }
    except requests.exceptions.Timeout:
        return {
            "error": "Request timed out. The backend may be waking up from sleep (free tier) — please try again.",
            "connected": False
        }
    except requests.exceptions.HTTPError as e:
        return {
            "error": f"Backend returned an error: {str(e)}",
            "connected": False
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "connected": False
        }


# ---------------------------------------------------------------------------
# Unified ask — Phase 7.5 /ask endpoint
# ---------------------------------------------------------------------------

def ask(question: str, limit: int = None) -> dict:
    params = {"question": question}
    if limit:
        params["limit"] = limit
    return _get("/ask", params)


def inspect_route(question: str) -> dict:
    return _get("/ask/route", {"question": question})


# ---------------------------------------------------------------------------
# SQL Agent endpoints
# ---------------------------------------------------------------------------

def sql_ask(question: str, limit: int = None) -> dict:
    params = {"question": question}
    if limit:
        params["limit"] = limit
    return _get("/agent/sql/ask", params)


def sql_generate(question: str) -> dict:
    return _get("/agent/sql/generate", {"question": question})


def sql_validate(sql: str) -> dict:
    return _get("/agent/sql/validate", {"sql": sql})


def sql_execute(sql: str) -> dict:
    return _get("/agent/sql/execute", {"sql": sql})


def sql_schema() -> dict:
    return _get("/agent/sql/schema")


# ---------------------------------------------------------------------------
# RAG endpoints
# ---------------------------------------------------------------------------

def rag_ask(query: str) -> dict:
    return _get("/rag/ask", {"query": query})


def rag_search(query: str) -> dict:
    return _get("/rag/search", {"query": query})


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

def health_check() -> dict:
    return _get("/")


def sql_health() -> dict:
    return _get("/agent/sql/health")


def ask_health() -> dict:
    return _get("/ask/health")