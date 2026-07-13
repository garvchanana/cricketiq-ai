"""
Phase 10.1 — Sanity check tests.

These confirm the test infrastructure itself works correctly
before we write any real validation tests in 10.2 onward.
"""

import pytest


def test_pytest_is_working():
    """Most basic possible test — confirms pytest runs at all."""
    assert 1 + 1 == 2


def test_can_import_app_modules():
    """Confirms the app package is importable from the tests folder."""
    from app.agents.sql_agent.schema_loader import SchemaLoader
    from app.agents.sql_agent.query_validator import QueryValidator
    from app.agents.intent_router import IntentRouter
    assert SchemaLoader is not None
    assert QueryValidator is not None
    assert IntentRouter is not None


@pytest.mark.requires_db
def test_db_fixture_provides_working_session(db):
    """
    Confirms the db fixture from conftest.py provides a real,
    working SQLAlchemy session connected to MySQL.
    """
    from sqlalchemy import text
    result = db.execute(text("SELECT 1 AS value")).fetchone()
    assert result is not None
    assert result[0] == 1


@pytest.mark.requires_db
def test_known_players_fixture_data_exists(db, known_players):
    """
    Confirms the known_players fixture data actually matches
    real records in the database — catches drift if data changes.
    """
    from app.database.models.player_batting_stats import PlayerBattingStats

    kohli = known_players["kohli"]
    record = db.query(PlayerBattingStats).filter(
        PlayerBattingStats.batsman == kohli["db_name"]
    ).first()

    assert record is not None, (
        f"Expected player '{kohli['db_name']}' not found in DB. "
        "Test fixture data may be stale."
    )
    assert record.total_runs >= kohli["min_runs"]


def test_known_tables_fixture_matches_schema_loader(known_tables):
    """
    Confirms SchemaLoader exposes all tables the SQL agent needs.
    Catches accidental table removal from schema_loader.py.
    """
    from app.agents.sql_agent.schema_loader import SchemaLoader

    allowed  = SchemaLoader.get_allowed_tables()
    missing  = known_tables - allowed

    assert not missing, (
        f"SchemaLoader is missing expected SQL-agent tables: {missing}"
    )


def test_schema_loader_intentionally_excludes_unsafe_tables(all_database_tables):
    """
    Confirms SchemaLoader does NOT expose tables that should stay
    out of the natural-language SQL agent's reach (ball_by_ball is
    too granular for LLM-generated aggregate queries; players and
    player_intelligence belong to the RAG layer, not SQL).

    If this test fails, someone added one of these tables to
    ALLOWED_SCHEMA — confirm that was intentional before proceeding.
    """
    from app.agents.sql_agent.schema_loader import SchemaLoader

    intentionally_excluded = {
        "ball_by_ball",
        "players",
        "player_intelligence",
        "match_momentum_stats",
    }

    allowed = SchemaLoader.get_allowed_tables()
    leaked  = intentionally_excluded & allowed

    assert not leaked, (
        f"These tables should NOT be SQL-agent accessible but are: {leaked}. "
        "If this is intentional, update both schema_loader.py docs and "
        "this test's expectations together."
    )