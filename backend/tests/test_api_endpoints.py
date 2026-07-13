"""
Phase 10.5 — API Endpoint Tests

Validates every FastAPI route returns the correct status code and
response shape. Uses TestClient, which calls the app directly in
memory — no running uvicorn server required.

Critical regressions this suite guards against:
- /agent/sql/execute route missing from sql_agent_routes.py
  (found and fixed during Phase 6.5 testing)
- get_db import path mismatch causing ImportError on startup
  (found and fixed during Phase 6.5 testing)
- /ask response missing expected fields for any route (SQL/RAG/HYBRID)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Root and health endpoints
# ---------------------------------------------------------------------------

class TestHealthEndpoints:

    def test_root_endpoint_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_sql_agent_health_returns_200(self):
        response = client.get("/agent/sql/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy" or "message" in data

    def test_unified_ask_health_returns_200(self):
        response = client.get("/ask/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert set(data.get("routes", [])) >= {"SQL", "RAG", "HYBRID"}

    def test_rag_health_returns_200(self):
        response = client.get("/rag/health")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# SQL Agent endpoints — all 6 must exist (regression guard for Phase 6.5)
# ---------------------------------------------------------------------------

class TestSQLAgentEndpointsExist:
    """
    REGRESSION GUARD: /agent/sql/execute was missing from the router
    entirely during Phase 6.5 — endpoint was never registered.
    This test class ensures all expected SQL agent routes respond
    (not 404), even if the underlying query itself fails.
    """

    @pytest.mark.requires_db
    def test_generate_endpoint_exists(self):
        response = client.get(
            "/agent/sql/generate",
            params={"question": "Top 5 run scorers"}
        )
        assert response.status_code != 404

    def test_validate_endpoint_exists(self):
        response = client.get(
            "/agent/sql/validate",
            params={"sql": "SELECT 1"}
        )
        assert response.status_code != 404

    @pytest.mark.requires_db
    def test_execute_endpoint_exists(self):
        """The endpoint that was missing in the original Phase 6.5 stub."""
        response = client.get(
            "/agent/sql/execute",
            params={"sql": "SELECT batsman FROM player_batting_stats LIMIT 1"}
        )
        assert response.status_code != 404

    @pytest.mark.requires_db
    def test_ask_endpoint_exists(self):
        response = client.get(
            "/agent/sql/ask",
            params={"question": "Top 5 run scorers"}
        )
        assert response.status_code != 404

    def test_schema_endpoint_exists(self):
        response = client.get("/agent/sql/schema")
        assert response.status_code != 404

    def test_schema_relevant_endpoint_exists(self):
        response = client.get(
            "/agent/sql/schema/relevant",
            params={"question": "Top run scorers"}
        )
        assert response.status_code != 404


# ---------------------------------------------------------------------------
# SQL Agent execute — validation gate behaviour
# ---------------------------------------------------------------------------

class TestSQLAgentExecuteValidation:

    @pytest.mark.requires_db
    def test_blocked_sql_returns_clean_error_not_500(self):
        """
        Unsafe SQL sent to /execute should never crash the server —
        it should return a structured error response.
        """
        response = client.get(
            "/agent/sql/execute",
            params={"sql": "DROP TABLE matches"}
        )
        assert response.status_code == 200  # endpoint handles it gracefully
        data = response.json()
        assert data.get("valid") is False
        assert len(data.get("errors", [])) > 0

    @pytest.mark.requires_db
    def test_valid_sql_returns_rows(self):
        response = client.get(
            "/agent/sql/execute",
            params={
                "sql": "SELECT batsman, total_runs FROM "
                       "player_batting_stats ORDER BY total_runs "
                       "DESC LIMIT 3"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") is True
        assert len(data.get("rows", [])) > 0


# ---------------------------------------------------------------------------
# Unified /ask endpoint — response shape consistency
# ---------------------------------------------------------------------------

class TestUnifiedAskEndpoint:
    """
    REQUIRED_FIELDS must be present regardless of which internal
    route (SQL/RAG/HYBRID) the question gets dispatched to.
    The frontend (Phase 9) depends on this consistent shape.
    """

    REQUIRED_FIELDS = {
        "question", "rewritten", "route", "reasoning",
        "entities", "answer", "rows", "row_count",
        "chart_suggestion", "error"
    }

    @pytest.mark.requires_db
    @pytest.mark.requires_llm
    def test_sql_route_returns_required_fields(self):
        response = client.get(
            "/ask", params={"question": "Top 5 run scorers in IPL"}
        )
        assert response.status_code == 200
        data = response.json()
        missing = self.REQUIRED_FIELDS - set(data.keys())
        assert not missing, f"Missing fields in SQL route response: {missing}"
        assert data["route"] == "SQL"

    @pytest.mark.requires_db
    @pytest.mark.requires_llm
    def test_rag_route_returns_required_fields(self):
        response = client.get(
            "/ask", params={"question": "Who is MS Dhoni as a player"}
        )
        assert response.status_code == 200
        data = response.json()
        missing = self.REQUIRED_FIELDS - set(data.keys())
        assert not missing, f"Missing fields in RAG route response: {missing}"
        assert data["route"] == "RAG"

    def test_route_debug_endpoint_does_not_execute_pipeline(self):
        """
        /ask/route should return routing decision without running
        SQL or RAG — should be fast and not require LLM calls for
        intent extraction (entity extraction is regex-based, no LLM).
        """
        response = client.get(
            "/ask/route", params={"question": "Top 5 run scorers in IPL"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "route" in data
        assert "reasoning" in data
        assert "entities" in data
        # Should NOT contain execution results
        assert "rows" not in data


# ---------------------------------------------------------------------------
# Error handling — malformed requests
# ---------------------------------------------------------------------------

class TestMalformedRequests:

    def test_missing_required_query_param_returns_422(self):
        """FastAPI should reject requests missing required params."""
        response = client.get("/ask")  # missing required "question" param
        assert response.status_code == 422

    def test_missing_question_on_generate_returns_422(self):
        response = client.get("/agent/sql/generate")
        assert response.status_code == 422

    def test_empty_question_string_does_not_crash(self):
        response = client.get("/ask/route", params={"question": ""})
        assert response.status_code in (200, 422)