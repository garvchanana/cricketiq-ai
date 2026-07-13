"""
Phase 10.1 — pytest configuration and shared fixtures

This file is automatically discovered by pytest.
All fixtures defined here are available to every test file
without explicit imports.
"""

from typing import Generator

import pytest
from sqlalchemy.orm import Session

from app.database.session import SessionLocal


# ---------------------------------------------------------------------------
# Database session fixture — READ ONLY
# ---------------------------------------------------------------------------

@pytest.fixture
def db() -> Generator[Session, None, None]:
    """
    Provides a database session for tests.

    SAFETY: This fixture is for READ-ONLY use only.
    Tests must never call INSERT/UPDATE/DELETE/DROP through this session.
    The QueryValidator (Phase 6.4) already blocks unsafe SQL at the
    application layer — this fixture relies on that protection plus
    test discipline to never call write methods directly.

    Session is rolled back and closed after every test,
    so even accidental writes within a test never persist.
    """

    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()  # undo any accidental writes
        session.close()


# ---------------------------------------------------------------------------
# Marker registration
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """
    Register custom markers so pytest doesn't warn about unknown markers.
    """
    config.addinivalue_line(
        "markers",
        "requires_db: test requires a live MySQL connection"
    )
    config.addinivalue_line(
        "markers",
        "requires_llm: test requires a live Groq API call (slower, costs tokens)"
    )
    config.addinivalue_line(
        "markers",
        "slow: test takes more than a few seconds to run"
    )


# ---------------------------------------------------------------------------
# Skip DB tests gracefully if MySQL is not reachable
# ---------------------------------------------------------------------------

def pytest_collection_modifyitems(config, items):
    """
    Auto-skip tests marked @pytest.mark.requires_db if the
    database connection fails. Prevents the whole test run from
    crashing if MySQL isn't running on this machine.
    """

    db_available = True
    try:
        session = SessionLocal()
        from sqlalchemy import text
        session.execute(text("SELECT 1"))
        session.close()
    except Exception:
        db_available = False

    if not db_available:
        skip_db = pytest.mark.skip(
            reason="MySQL database not reachable — skipping DB-dependent tests"
        )
        for item in items:
            if "requires_db" in item.keywords:
                item.add_marker(skip_db)


# ---------------------------------------------------------------------------
# Sample test data — known-good players for assertions
# ---------------------------------------------------------------------------

@pytest.fixture
def known_players() -> dict:
    """
    Players verified to exist in the DB with known stats,
    used across multiple test files for consistent assertions.
    """
    return {
        "kohli": {
            "db_name":   "V Kohli",
            "canonical": "Virat Kohli",
            "min_runs":  9000,
        },
        "dhoni": {
            "db_name":   "MS Dhoni",
            "canonical": "Mahendra Singh Dhoni",
            "min_runs":  5000,
        },
        "rohit": {
            "db_name":   "RG Sharma",
            "canonical": "Rohit Sharma",
            "min_runs":  7000,
        },
    }


@pytest.fixture
def known_tables() -> set:
    """
    Tables that must always be in the SQL agent's allowed schema.

    NOTE: This is intentionally a SUBSET of all database tables.
    Some tables are excluded from SQL agent access by design:
      - ball_by_ball         → too granular/risky for LLM-generated SQL
      - players              → used by RAG/canonicalization, not SQL agent
      - player_intelligence  → RAG-only table (narrative summaries)
      - match_momentum_stats → used by MatchupAnalyst (Phase 8.3) directly,
                                not exposed to the natural-language SQL agent
    This fixture validates the SQL agent's *intended* safe surface area,
    not the full database schema.
    """
    return {
        "player_batting_stats",
        "player_bowling_stats",
        "advanced_batting_stats",
        "match_phase_stats",
        "batter_bowler_matchups",
        "venue_stats",
        "team_stats",
        "player_rankings",
    }


@pytest.fixture
def all_database_tables() -> set:
    """
    Every table that exists in the database, including ones
    intentionally excluded from the SQL agent's natural-language
    interface. Used to test RAG/agent-layer code paths that access
    these tables directly (e.g. PlayerAnalyst, MatchupAnalyst).
    """
    return {
        "matches",
        "ball_by_ball",
        "players",
        "player_intelligence",
        "player_batting_stats",
        "player_bowling_stats",
        "advanced_batting_stats",
        "match_phase_stats",
        "match_momentum_stats",
        "batter_bowler_matchups",
        "venue_stats",
        "team_stats",
        "player_rankings",
    }