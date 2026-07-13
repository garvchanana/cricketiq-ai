"""
Phase 10.2 — SQL Safety Tests

The most critical test suite in the project.
Validates that QueryValidator (Phase 6.4) blocks every category
of unsafe SQL, regardless of casing, formatting, or injection style.

If any test in this file fails, the SQL agent must not be considered
safe to expose to real users until fixed.
"""

import pytest

from app.agents.sql_agent.query_validator import QueryValidator


# ---------------------------------------------------------------------------
# Destructive statement blocking
# ---------------------------------------------------------------------------

class TestBlocksDestructiveStatements:

    @pytest.mark.parametrize("sql", [
        "DROP TABLE matches",
        "drop table matches",
        "DROP TABLE IF EXISTS matches",
        "DROP DATABASE cricketiq",
    ])
    def test_blocks_drop(self, sql):
        result = QueryValidator.validate(sql)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.parametrize("sql", [
        "DELETE FROM player_batting_stats",
        "delete from player_batting_stats where batsman = 'V Kohli'",
        "DELETE FROM player_batting_stats WHERE 1=1",
    ])
    def test_blocks_delete(self, sql):
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    @pytest.mark.parametrize("sql", [
        "UPDATE player_batting_stats SET total_runs = 0",
        "update player_batting_stats set total_runs = 99999",
    ])
    def test_blocks_update(self, sql):
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    @pytest.mark.parametrize("sql", [
        "INSERT INTO player_batting_stats VALUES (1, 'Fake', 99999)",
        "insert into player_rankings (player_name) values ('Hacker')",
    ])
    def test_blocks_insert(self, sql):
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    @pytest.mark.parametrize("sql", [
        "ALTER TABLE player_batting_stats ADD COLUMN hacked INT",
        "TRUNCATE TABLE matches",
        "CREATE TABLE evil (id INT)",
        "REPLACE INTO player_rankings VALUES (1, 'x', 0, 0, 0, 0, 0)",
        "CALL some_stored_procedure()",
        "EXEC xp_cmdshell('dir')",
        "GRANT ALL PRIVILEGES ON *.* TO 'hacker'@'%'",
        "REVOKE ALL ON cricketiq.* FROM 'app_user'",
        "RENAME TABLE matches TO matches_backup",
    ])
    def test_blocks_other_destructive_statements(self, sql):
        result = QueryValidator.validate(sql)
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# Injection pattern blocking
# ---------------------------------------------------------------------------

class TestBlocksInjectionPatterns:

    def test_blocks_multiple_statements(self):
        sql = "SELECT batsman FROM player_batting_stats; DROP TABLE matches"
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    def test_blocks_sql_comment_injection(self):
        sql = "SELECT batsman FROM player_batting_stats -- DROP TABLE matches"
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    def test_blocks_block_comment_injection(self):
        sql = "SELECT batsman FROM player_batting_stats /* malicious */"
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    def test_blocks_sleep_timing_attack(self):
        sql = "SELECT IF(1=1, SLEEP(10), 0) FROM player_batting_stats"
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    def test_blocks_benchmark_timing_attack(self):
        sql = "SELECT BENCHMARK(1000000, SHA1('x')) FROM player_batting_stats"
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    def test_blocks_information_schema_access(self):
        sql = "SELECT * FROM information_schema.tables"
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    def test_blocks_select_into_outfile(self):
        sql = "SELECT * FROM player_batting_stats INTO OUTFILE '/tmp/dump.csv'"
        result = QueryValidator.validate(sql)
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# Schema restriction enforcement
# ---------------------------------------------------------------------------

class TestEnforcesSchemaRestrictions:

    def test_blocks_unknown_table(self):
        sql = "SELECT * FROM users"
        result = QueryValidator.validate(sql)
        assert result["valid"] is False
        assert "users" in str(result["errors"]).lower() or \
               "unknown" in str(result["errors"]).lower()

    def test_blocks_unknown_table_even_with_valid_columns(self):
        sql = "SELECT password, email FROM admin_credentials"
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    def test_blocks_excluded_ball_by_ball_if_not_in_schema(self):
        """
        ball_by_ball is intentionally excluded from SQL agent access
        (see Phase 10.1 schema tests). Validator should still allow it
        at the SQL-syntax level since QueryValidator checks against
        SchemaLoader's allowed tables, which may or may not include it.
        This test documents current behavior — update if schema changes.
        """
        from app.agents.sql_agent.schema_loader import SchemaLoader
        allowed = SchemaLoader.get_allowed_tables()

        sql    = "SELECT * FROM ball_by_ball LIMIT 5"
        result = QueryValidator.validate(sql)

        if "ball_by_ball" not in allowed:
            assert result["valid"] is False, (
                "ball_by_ball is not in allowed tables — validator should block it"
            )


# ---------------------------------------------------------------------------
# Valid queries must still pass — safety must not be over-aggressive
# ---------------------------------------------------------------------------

class TestAllowsValidQueries:

    @pytest.mark.parametrize("sql", [
        "SELECT batsman, total_runs FROM player_batting_stats "
        "ORDER BY total_runs DESC LIMIT 10",

        "SELECT bowler, wickets, economy_rate FROM player_bowling_stats "
        "WHERE balls_bowled >= 120 ORDER BY economy_rate ASC LIMIT 5",

        "SELECT batsman, total_runs FROM player_batting_stats "
        "WHERE batsman IN ('V Kohli', 'RG Sharma')",

        "SELECT venue, average_run_rate FROM venue_stats "
        "ORDER BY average_run_rate DESC LIMIT 10",

        "SELECT player_name, ranking_score, role FROM player_rankings "
        "WHERE role = 'All-Rounder' ORDER BY ranking_score DESC LIMIT 10",
    ])
    def test_allows_valid_select_queries(self, sql):
        result = QueryValidator.validate(sql)
        assert result["valid"] is True, (
            f"Valid query was incorrectly blocked: {result['errors']}"
        )

    def test_with_clause_cte_alias_not_misidentified_as_unknown_table(self):
        """
        Phase 11.3 fix — CTE alias names are now correctly excluded
        from the unknown-table check in _extract_tables().

        "top_batters" in WITH top_batters AS (...) is a CTE alias,
        not a real database table. The validator now extracts CTE alias
        names and removes them from the referenced-tables set before
        checking against the allowed schema.

        This test was updated in Phase 11.3 from asserting valid=False
        (old blocking behavior) to asserting valid=True (correct behavior
        after CTE-awareness was added to QueryValidator._extract_tables).
        """
        sql = (
            "WITH top_batters AS ("
            "SELECT batsman, total_runs FROM player_batting_stats "
            "ORDER BY total_runs DESC LIMIT 5"
            ") SELECT * FROM top_batters"
        )
        result = QueryValidator.validate(sql)

        # Phase 11.3: CTE aliases are no longer misidentified as unknown
        # tables — the query is now correctly validated as safe
        assert result["valid"] is True, (
            f"CTE query should be valid after Phase 11.3 fix. "
            f"Errors: {result['errors']}"
        )
        assert result["errors"] == []

    def test_allows_joins_between_allowed_tables(self):
        sql = (
            "SELECT pb.batsman, pb.total_runs, pr.ranking_score "
            "FROM player_batting_stats pb "
            "JOIN player_rankings pr ON pb.batsman = pr.player_name "
            "LIMIT 10"
        )
        result = QueryValidator.validate(sql)
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Edge cases — empty, whitespace, case sensitivity
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_blocks_empty_string(self):
        result = QueryValidator.validate("")
        assert result["valid"] is False

    def test_blocks_whitespace_only(self):
        result = QueryValidator.validate("   \n\t  ")
        assert result["valid"] is False

    def test_blocks_non_select_starter(self):
        sql = "WITH x AS (SELECT 1) DROP TABLE matches"
        result = QueryValidator.validate(sql)
        assert result["valid"] is False

    def test_case_insensitive_keyword_blocking(self):
        """Blocked keywords must be caught regardless of casing."""
        variants = ["DROP", "Drop", "drop", "DrOp"]
        for keyword in variants:
            sql = f"{keyword} TABLE matches"
            result = QueryValidator.validate(sql)
            assert result["valid"] is False, f"Failed to block: {sql}"

    def test_warns_but_allows_select_star(self):
        """SELECT * is discouraged but not unsafe — should warn not block."""
        sql = "SELECT * FROM player_batting_stats LIMIT 5"
        result = QueryValidator.validate(sql)
        assert result["valid"] is True
        assert len(result.get("warnings", [])) > 0

    def test_warns_on_missing_limit_broad_query(self):
        """Broad query with no WHERE and no LIMIT should warn."""
        sql = "SELECT batsman, total_runs FROM player_batting_stats"
        result = QueryValidator.validate(sql)
        assert result["valid"] is True
        assert len(result.get("warnings", [])) > 0