import requests
 
# ---------------------------------------------------------------------------
# Base configuration
# Change BASE_URL to your deployed backend URL in production
# ---------------------------------------------------------------------------
 
BASE_URL = "http://localhost:8000"
 
TIMEOUT  = 30  # seconds
 
 
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
            "error": "Cannot connect to backend. Is the server running?",
            "connected": False
        }
    except requests.exceptions.Timeout:
        return {
            "error": "Request timed out. The backend took too long to respond.",
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
    """
    Send any cricket question to the unified /ask endpoint.
    Returns route, answer, rows, chart_suggestion.
    """
    params = {"question": question}
    if limit:
        params["limit"] = limit
    return _get("/ask", params)
 
 
def inspect_route(question: str) -> dict:
    """
    Debug — show routing decision without executing pipeline.
    """
    return _get("/ask/route", {"question": question})
 
 
# ---------------------------------------------------------------------------
# SQL Agent endpoints
# ---------------------------------------------------------------------------
 
def sql_ask(question: str, limit: int = None) -> dict:
    """
    Send a question directly to SQL agent.
    """
    params = {"question": question}
    if limit:
        params["limit"] = limit
    return _get("/agent/sql/ask", params)
 
 
def sql_generate(question: str) -> dict:
    """
    Generate SQL from a question without executing.
    """
    return _get("/agent/sql/generate", {"question": question})
 
 
def sql_validate(sql: str) -> dict:
    """
    Validate SQL safety.
    """
    return _get("/agent/sql/validate", {"sql": sql})
 
 
def sql_execute(sql: str) -> dict:
    """
    Execute validated SQL directly.
    """
    return _get("/agent/sql/execute", {"sql": sql})
 
 
def sql_schema() -> dict:
    """
    Fetch full DB schema exposed to SQL agent.
    """
    return _get("/agent/sql/schema")
 
 
# ---------------------------------------------------------------------------
# RAG endpoints
# ---------------------------------------------------------------------------
 
def rag_ask(query: str) -> dict:
    """
    Send a query directly to RAG pipeline.
    """
    return _get("/rag/ask", {"query": query})
 
 
def rag_search(query: str) -> dict:
    """
    Semantic search — retrieve player intelligence docs.
    """
    return _get("/rag/search", {"query": query})
 
 
# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------
 
def health_check() -> dict:
    """
    Check backend is running.
    """
    return _get("/")
 
 
def sql_health() -> dict:
    """
    Check SQL agent is running.
    """
    return _get("/agent/sql/health")
 
 
def ask_health() -> dict:
    """
    Check unified ask endpoint is running.
    """
    return _get("/ask/health")