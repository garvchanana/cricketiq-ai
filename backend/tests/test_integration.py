"""
Phase 10.6 — Integration Tests

End-to-end pipeline validation through the real /ask endpoint.
Unlike Phase 10.1–10.5 which test components in isolation, these
tests exercise the FULL chain for each route:

  SQL:    Question → Rewrite → Extract → Route → Generate → Validate
          → Execute → Format → Answer

  RAG:    Question → Rewrite → Extract → Route → Retrieve → Prompt
          → Generate → Answer

  HYBRID: Question → Rewrite → Extract → Route → SQL pipeline
          + RAG pipeline → Fuse → Answer

These are the slowest tests in the suite (real DB + real LLM calls)
but give the highest confidence the system works as a whole.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

pytestmark = [pytest.mark.requires_db, pytest.mark.requires_llm, pytest.mark.slow]


# ---------------------------------------------------------------------------
# Phase 6.8 validation questions — the original controlled test set
# ---------------------------------------------------------------------------

class TestPhase68ValidationQuestions:
    """
    Re-runs the exact controlled questions specified in the original
    Phase 6.8 plan, now through the full /ask pipeline rather than
    the SQL agent in isolation. Confirms the original deliverable
    still holds after Phase 7 routing was added on top.
    """

    @pytest.mark.parametrize("question", [
        "Top 10 run scorers",
        "Top 10 wicket takers",
        "Best death overs batters",
        "Best powerplay bowlers",
        "Best venues for batting",
        "Best all-rounders",
    ])
    def test_question_returns_complete_answer(self, question):
        response = client.get("/ask", params={"question": question})
        assert response.status_code == 200

        data = response.json()
        assert data["error"] is None, (
            f"Question '{question}' returned an error: {data['error']}"
        )
        assert data["answer"], f"Empty answer for: '{question}'"
        assert data["route"] in ("SQL", "RAG", "HYBRID")

    def test_compare_two_named_players(self):
        response = client.get(
            "/ask",
            params={"question": "Compare Rohit Sharma and Virat Kohli"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["answer"]
        # Both player names (or canonical forms) should appear
        answer_lower = data["answer"].lower()
        assert "rohit" in answer_lower or "sharma" in answer_lower
        assert "kohli" in answer_lower or "virat" in answer_lower


# ---------------------------------------------------------------------------
# Route correctness — confirms each route type fires for the
# right kind of question, end to end through the real endpoint
# ---------------------------------------------------------------------------

class TestRouteCorrectnessEndToEnd:

    @pytest.mark.parametrize("question,expected_route", [
        ("Top 5 bowlers by wickets in IPL",                "SQL"),
        ("Best economy bowlers at Wankhede in death overs", "SQL"),
        ("Which venue has the highest average score",       "SQL"),
        ("Who is MS Dhoni as a player",                      "RAG"),
        ("Tell me about Jasprit Bumrah bowling style",       "RAG"),
        ("Is Rohit Sharma better than Virat Kohli overall",  "HYBRID"),
    ])
    def test_route_matches_expectation(self, question, expected_route):
        response = client.get("/ask", params={"question": question})
        assert response.status_code == 200
        data = response.json()
        assert data["route"] == expected_route, (
            f"Expected '{question}' to route to {expected_route}, "
            f"got {data['route']} (reasoning: {data.get('reasoning')})"
        )


# ---------------------------------------------------------------------------
# Canonicalization end-to-end — DB shortcodes must surface as
# full names in the final user-facing answer
# ---------------------------------------------------------------------------

class TestCanonicalizationEndToEnd:

    def test_sql_route_answer_uses_full_names_not_db_shortcodes(self):
        """
        REGRESSION GUARD: /agent/sql/execute intentionally returns raw
        DB shortcodes (e.g. "V Kohli") since it's a debug endpoint.
        But /ask (the user-facing endpoint) must always canonicalize
        names in the final answer via ResultFormatter (Phase 6.6).
        """
        response = client.get(
            "/ask", params={"question": "Top 5 run scorers in IPL"}
        )
        data = response.json()
        answer = data["answer"]

        # The narrative answer should contain full names, not shortcodes
        assert "V Kohli" not in answer, (
            "Raw DB shortcode 'V Kohli' leaked into user-facing answer "
            "— ResultFormatter canonicalization may have regressed."
        )


# ---------------------------------------------------------------------------
# Hybrid pipeline specifics — confirms both SQL and RAG context
# actually get used in the fused answer, not just one source
# ---------------------------------------------------------------------------

class TestHybridPipelineFusion:

    def test_hybrid_route_does_not_crash_on_rag_dict_leak(self):
        """
        REGRESSION GUARD: HybridComposer previously passed the
        QueryRewriter's dict output directly to RAGPipeline instead
        of extracting the string, causing:
        "Multimodal dict input contains unrecognized modality keys"
        Fixed in Phase 7.4 via explicit string coercion.
        """
        response = client.get(
            "/ask",
            params={
                "question": "Is Rohit Sharma better than Virat Kohli in IPL"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None, (
            f"Hybrid route failed: {data['error']}"
        )
        assert "multimodal" not in str(data.get("answer", "")).lower()
        assert "unrecognized modality" not in str(data).lower()

    def test_hybrid_answer_is_substantive_not_just_fallback(self):
        """
        A hybrid answer should be a real synthesized response,
        not just a one-line fallback or error message.
        """
        response = client.get(
            "/ask",
            params={
                "question": "Why is MS Dhoni so effective in death overs"
            }
        )
        data = response.json()
        assert data["route"] == "HYBRID"
        assert len(data["answer"]) > 100, (
            "Hybrid answer suspiciously short — may have fallen back "
            "to a minimal error response instead of full synthesis."
        )


# ---------------------------------------------------------------------------
# Consistency — same question asked twice should route the same way
# ---------------------------------------------------------------------------

class TestConsistency:

    def test_same_question_routes_consistently(self):
        """
        Routing (rewriter + entity extraction) is deterministic
        regex-based logic, not LLM-based, so the same question must
        always route to the same place across repeated calls.
        """
        question = "Top 10 run scorers in IPL"

        response1 = client.get("/ask/route", params={"question": question})
        response2 = client.get("/ask/route", params={"question": question})

        assert response1.json()["route"] == response2.json()["route"]
        assert response1.json()["entities"] == response2.json()["entities"]