"""
Phase 10.3 — SQL Generation Tests

Validates SQLGenerator (Phase 6.3) produces correct, schema-compliant
SQL for real cricket questions. These tests call the live Groq LLM,
so they are slower and marked accordingly.

Critical regressions this suite guards against:
- LLM adding non-existent "phase" column to player_bowling_stats
  (the bug fixed after Phase 9.2 testing)
- LLM joining batter_bowler_matchups with match_phase_stats
  (the wrong-JOIN bug fixed after Phase 9.2 testing)
- LLM generating non-SELECT statements
- LLM referencing tables outside the allowed schema
"""

import pytest

from app.agents.sql_agent.sql_generator import SQLGenerator
from app.agents.sql_agent.query_validator import QueryValidator
from app.agents.sql_agent.schema_loader import SchemaLoader


pytestmark = pytest.mark.requires_llm


# ---------------------------------------------------------------------------
# Helper — generate and validate in one step
# ---------------------------------------------------------------------------

def _generate_and_validate(question: str, limit: int = None) -> dict:
    """
    Runs the full generate → validate pipeline and returns both results
    so tests can assert on generation success AND safety in one call.
    """
    generation = SQLGenerator.generate(question=question, limit=limit)
    sql = generation.get("sql")

    validation = (
        QueryValidator.validate(sql) if sql
        else {"valid": False, "errors": ["No SQL generated"], "warnings": []}
    )

    return {
        "generation": generation,
        "validation": validation,
        "sql": sql,
    }


# ---------------------------------------------------------------------------
# Basic generation succeeds and is always safe
# ---------------------------------------------------------------------------

class TestBasicGenerationSucceeds:

    @pytest.mark.parametrize("question", [
        "Who scored the most runs in IPL?",
        "Top 10 wicket takers in IPL",
        "Which bowler has the best economy in IPL?",
        "Which venue has the highest average run rate?",
        "Top 10 all rounders by ranking",
    ])
    def test_generates_valid_sql(self, question):
        result = _generate_and_validate(question)

        assert result["sql"] is not None, (
            f"No SQL generated for: '{question}' — "
            f"raw response: {result['generation'].get('raw')}"
        )
        assert result["validation"]["valid"] is True, (
            f"Generated SQL failed validation for '{question}': "
            f"{result['validation']['errors']}"
        )

    @pytest.mark.parametrize("question", [
        "Who scored the most runs in IPL?",
        "Top 10 wicket takers in IPL",
        "Best economy bowlers in IPL",
    ])
    def test_generated_sql_is_select_only(self, question):
        """Defense in depth — generator should never produce non-SELECT,
        even though the validator would catch it anyway."""
        result = _generate_and_validate(question)
        sql = (result["sql"] or "").strip().lower()
        assert sql.startswith("select") or sql.startswith("with")


# ---------------------------------------------------------------------------
# Regression tests — these exact bugs were found and fixed during
# Phase 9.2 manual testing. They must never reappear.
# ---------------------------------------------------------------------------

class TestKnownRegressions:

    def test_phase_questions_never_use_phase_column_on_bowling_stats(self):
        """
        REGRESSION GUARD: The LLM previously generated
        "WHERE balls_bowled >= 120 AND phase = 'death overs'"
        against player_bowling_stats, which has no phase column.
        Fixed in Phase 9.2 via explicit CRITICAL TABLE RULES in the
        prompt. This test ensures the fix holds.
        """
        result = _generate_and_validate(
            "Best economy bowlers in death overs"
        )
        sql = (result["sql"] or "").lower()

        if "player_bowling_stats" in sql:
            assert "phase" not in sql, (
                f"Regression detected: player_bowling_stats query "
                f"references non-existent 'phase' column. SQL: {result['sql']}"
            )

        assert result["validation"]["valid"] is True

    def test_phase_questions_never_join_matchups_with_phase_stats(self):
        """
        REGRESSION GUARD: The LLM previously generated a JOIN between
        batter_bowler_matchups and match_phase_stats using a
        non-existent match_id column on batter_bowler_matchups.
        Fixed in Phase 9.2 via explicit "NEVER JOIN" rule.
        """
        result = _generate_and_validate(
            "Best bowlers in death overs by economy"
        )
        sql = (result["sql"] or "").lower()

        has_matchups_join = (
            "batter_bowler_matchups" in sql
            and "match_phase_stats" in sql
        )
        assert not has_matchups_join, (
            f"Regression detected: forbidden JOIN between "
            f"batter_bowler_matchups and match_phase_stats. "
            f"SQL: {result['sql']}"
        )

    def test_comparison_questions_use_single_table(self):
        """
        REGRESSION GUARD: Player comparison questions previously
        sometimes generated broken multi-table JOINs. The template
        rule specifies WHERE batsman IN (...) on ONE table.
        """
        result = _generate_and_validate(
            "Compare Rohit Sharma and Virat Kohli batting"
        )
        assert result["validation"]["valid"] is True
        sql = (result["sql"] or "").lower()
        assert "in (" in sql or "in(" in sql, (
            f"Expected WHERE...IN(...) pattern for comparison. SQL: {result['sql']}"
        )


# ---------------------------------------------------------------------------
# Schema compliance — generated SQL must only reference real tables
# ---------------------------------------------------------------------------

class TestSchemaCompliance:

    @pytest.mark.parametrize("question", [
        "Top 10 run scorers",
        "Best bowling economy in IPL",
        "Top venues by run rate",
        "Compare MS Dhoni and AB de Villiers",
    ])
    def test_only_references_allowed_tables(self, question):
        result = _generate_and_validate(question)
        allowed = SchemaLoader.get_allowed_tables()

        sql = (result["sql"] or "").lower()
        referenced = QueryValidator._extract_tables(result["sql"] or "")

        unknown = referenced - allowed
        assert not unknown, (
            f"Generated SQL for '{question}' references tables outside "
            f"the allowed schema: {unknown}. SQL: {result['sql']}"
        )


# ---------------------------------------------------------------------------
# Limit handling
# ---------------------------------------------------------------------------

class TestLimitHandling:

    def test_respects_custom_limit(self):
        result = _generate_and_validate(
            "Top run scorers in IPL", limit=3
        )
        sql = (result["sql"] or "").lower()
        assert "limit 3" in sql

    def test_uses_default_limit_when_none_specified(self):
        result = _generate_and_validate("Top wicket takers in IPL")
        sql = (result["sql"] or "").lower()
        assert "limit" in sql


# ---------------------------------------------------------------------------
# Failure handling — generator must fail gracefully, never crash
# ---------------------------------------------------------------------------

class TestGracefulFailureHandling:

    def test_handles_nonsensical_question_without_crashing(self):
        """
        A question with no cricket meaning should either generate
        a harmless query or fail cleanly with a message —
        never raise an unhandled exception.
        """
        try:
            result = SQLGenerator.generate(
                question="asdkjasldkj random gibberish text 12345"
            )
            assert "sql" in result
            assert "intent" in result
        except Exception as e:
            pytest.fail(
                f"SQLGenerator raised an unhandled exception "
                f"on gibberish input: {e}"
            )

    def test_handles_empty_question_without_crashing(self):
        try:
            result = SQLGenerator.generate(question="")
            assert "sql" in result
        except Exception as e:
            pytest.fail(
                f"SQLGenerator raised an unhandled exception "
                f"on empty input: {e}"
            )