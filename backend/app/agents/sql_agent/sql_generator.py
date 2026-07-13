import re

from app.agents.sql_agent.schema_loader import SchemaLoader
from app.llm.groq_client import GroqClient
from app.nlp.canonicalization.player_registry import CANONICAL_TO_ALIAS


class SQLGenerator:

    DEFAULT_LIMIT = 10
    MAX_LIMIT = 50

    # ---------------------------------------------------------------------------
    # Limit helper
    # ---------------------------------------------------------------------------

    @classmethod
    def _resolve_limit(cls, limit) -> int:

        if limit is None:
            return cls.DEFAULT_LIMIT

        return max(1, min(int(limit), cls.MAX_LIMIT))

    # ---------------------------------------------------------------------------
    # Prompt builder
    # ---------------------------------------------------------------------------

    @classmethod
    def _build_prompt(
        cls,
        question: str,
        limit: int
    ) -> str:

        guidance     = SchemaLoader.get_query_guidance(question)
        schema_lines = SchemaLoader.get_schema_context()
        relationships = SchemaLoader.get_relationships()

        relationship_lines = "\n".join(
            f"  - {r['left_table']}.{r['left_column']} "
            f"-> {r['right_table']}.{r['right_column']} "
            f"({r['relationship']})"
            for r in relationships
        )

        relevant_tables = guidance.get("relevant_tables", [])
        relevant_note   = (
            f"Most relevant tables for this question: "
            f"{', '.join(relevant_tables)}"
            if relevant_tables
            else ""
        )

        prompt = f"""You are a cricket SQL expert for an IPL analytics system.
Convert the user's question into a single safe read-only MySQL SELECT query.

=== ALLOWED TABLES AND COLUMNS ===
{schema_lines}

=== TABLE RELATIONSHIPS ===
{relationship_lines}

=== STRICT RULES — follow exactly ===
1. Output ONLY raw SQL — no markdown, no backticks, no explanation.
2. Only use SELECT statements. Never INSERT, UPDATE, DELETE, DROP, ALTER.
3. Only use tables and columns listed above. Never invent column names.
4. Always add LIMIT {limit} unless the question asks for a specific player.
5. Prefer summary tables over raw ball_by_ball for ranking/aggregate questions.
6. Column name for a batter is "batsman", for a bowler is "bowler".
7. Use ORDER BY DESC for runs/wickets, ASC for economy/average rankings.

=== CRITICAL TABLE RULES — never break these ===
A. player_bowling_stats has NO "phase" column. NEVER write
   "AND phase = '...'" when querying player_bowling_stats.
B. player_batting_stats has NO "phase" column. NEVER write
   "AND phase = '...'" when querying player_batting_stats.
C. match_phase_stats has NO player-level data — use it ONLY for overall phase stats.
D. NEVER JOIN batter_bowler_matchups with match_phase_stats — no shared key exists.
E. For player comparison, use WHERE batsman IN ('name1', 'name2') on one table only.

=== WRONG vs RIGHT — phase + bowler/batter questions ===
This applies to ALL phase phrasing: "powerplay", "death overs", "middle overs",
"power play", "slog overs", "first 6 overs", "last 4 overs" — every variant.

WRONG (player_bowling_stats has no phase column):
SELECT bowler, economy_rate FROM player_bowling_stats
WHERE balls_bowled >= 120 AND phase = 'Powerplay' ORDER BY economy_rate ASC

RIGHT (phase word is dropped — table itself has no per-phase split):
SELECT bowler, economy_rate, wickets, balls_bowled
FROM player_bowling_stats
WHERE balls_bowled >= 120
ORDER BY economy_rate ASC LIMIT {limit}

This rule applies identically to ALL of these question phrasings:
"Best powerplay bowlers", "Best bowlers in powerplay", "Top death overs bowlers",
"Best economy in death overs", "Best bowlers in middle overs",
"Powerplay bowling stats", "Death overs economy leaders" — ALL of them
must produce the SAME query shown above, with the phase word completely
dropped from the WHERE clause, regardless of how the question is phrased.

=== EXACT SQL TEMPLATES — use these for common questions ===

Q: Best bowlers by economy in death overs / powerplay / any phase wording:
SQL: SELECT bowler, economy_rate, wickets, balls_bowled
     FROM player_bowling_stats
     WHERE balls_bowled >= 120
     ORDER BY economy_rate ASC LIMIT {limit}

Q: Best powerplay bowlers (phase word always dropped from WHERE):
SQL: SELECT bowler, economy_rate, wickets, balls_bowled
     FROM player_bowling_stats
     WHERE balls_bowled >= 120
     ORDER BY economy_rate ASC LIMIT {limit}

Q: Top run scorers:
SQL: SELECT batsman, total_runs, strike_rate
     FROM player_batting_stats
     ORDER BY total_runs DESC LIMIT {limit}

Q: Compare two players batting:
SQL: SELECT batsman, total_runs, strike_rate, batting_average
     FROM player_batting_stats
     WHERE batsman IN ('Player1', 'Player2')

Q: Top wicket takers:
SQL: SELECT bowler, wickets, economy_rate
     FROM player_bowling_stats
     ORDER BY wickets DESC LIMIT {limit}

Q: Best economy bowlers overall:
SQL: SELECT bowler, economy_rate, wickets
     FROM player_bowling_stats
     WHERE balls_bowled >= 120
     ORDER BY economy_rate ASC LIMIT {limit}

Q: Phase stats (powerplay/death overs overall):
SQL: SELECT phase, run_rate, wickets, boundaries
     FROM match_phase_stats
     WHERE phase = 'Powerplay'

Q: Top venues by run rate:
SQL: SELECT venue, average_run_rate, total_matches
     FROM venue_stats
     ORDER BY average_run_rate DESC LIMIT {limit}

{relevant_note}

=== USER QUESTION ===
{question}

SQL:"""

        return prompt

    # ---------------------------------------------------------------------------
    # SQL extraction
    # ---------------------------------------------------------------------------

    @staticmethod
    def _extract_sql(raw: str) -> str | None:

        if not raw:
            return None

        # Strip markdown fences if model returns them
        cleaned = re.sub(
            r"```(?:sql)?",
            "",
            raw,
            flags=re.IGNORECASE
        ).replace("```", "").strip()

        # Take only the first statement if multiple are returned
        statements = [
            s.strip()
            for s in cleaned.split(";")
            if s.strip()
        ]

        if not statements:
            return None

        sql = statements[0]

        # Must start with SELECT or WITH
        if not re.match(r"^\s*(select|with)\b", sql, re.IGNORECASE):
            return None

        return sql

    # ---------------------------------------------------------------------------
    # Public generate method
    # ---------------------------------------------------------------------------

    @classmethod
    def _resolve_player_names(cls, question: str) -> str:
        """
        Phase 11.3 fix — Replace canonical player names in the question
        with their DB shortcode equivalents before SQL generation.

        The DB stores names as Cricsheet shortcodes (e.g. "V Kohli"),
        not canonical names (e.g. "Virat Kohli"). When the intent router
        or entity extractor has already canonicalized player names,
        the SQL generator must convert them back to DB format so the
        generated WHERE IN clause actually matches DB records.

        Example:
          "Compare Virat Kohli and Rohit Sharma"
          -> "Compare V Kohli and RG Sharma"
        """
        result = question
        # Sort by length descending to match longer names first
        # "AB de Villiers" must match before "Villiers"
        for canonical, alias in sorted(
            CANONICAL_TO_ALIAS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        ):
            if canonical in result:
                result = result.replace(canonical, alias)
        return result

    @classmethod
    def generate(
        cls,
        question: str,
        limit=None
    ) -> dict:

        limit    = cls._resolve_limit(limit)

        # Phase 11.3 fix — for comparison questions, convert any
        # canonical player names back to DB shortcodes before
        # building the SQL prompt. The LLM must use DB shortcodes
        # in WHERE IN clauses since that is what the DB stores.
        # e.g. "Virat Kohli" -> "V Kohli", "Rohit Sharma" -> "RG Sharma"
        processed_question = cls._resolve_player_names(question)

        prompt   = cls._build_prompt(processed_question, limit)

        try:
            raw_response = GroqClient.complete(
                system_prompt=(
                    "You are a MySQL expert. "
                    "Output only raw SQL with no explanation, "
                    "no markdown, and no backticks."
                ),
                user_prompt=prompt
            )

            sql = cls._extract_sql(raw_response)

            if not sql:
                return {
                    "sql":     None,
                    "intent":  "generation_failed",
                    "message": (
                        "The LLM did not return a valid SELECT query. "
                        "Please rephrase your question."
                    ),
                    "raw":     raw_response
                }

            return {
                "sql":    sql,
                "intent": cls._infer_intent(question),
                "raw":    raw_response
            }

        except Exception as error:

            return {
                "sql":     None,
                "intent":  "error",
                "message": f"SQL generation failed: {str(error)}"
            }

    # ---------------------------------------------------------------------------
    # Intent inference (used by formatter for labels and chart suggestions)
    # ---------------------------------------------------------------------------

    @staticmethod
    def _infer_intent(question: str) -> str:

        normalized = (question or "").lower()

        if any(p in normalized for p in ["most runs", "top run", "run scorer", "best batter", "best batsman"]):
            return "top_batters_by_runs"

        if any(p in normalized for p in ["most wickets", "top wicket", "wicket taker", "best bowler"]):
            return "top_bowlers_by_wickets"

        if "economy" in normalized:
            return "best_bowlers_by_economy"

        if any(p in normalized for p in ["venue", "ground", "stadium"]):
            return "top_batting_venues"

        if any(p in normalized for p in ["all rounder", "all-rounder", "ranking", "best player", "top player"]):
            return "top_players_by_ranking"

        if any(p in normalized for p in ["team", "teams", "franchise"]):
            return "top_teams_by_runs"

        if any(p in normalized for p in ["powerplay", "power play"]):
            return "powerplay_stats"

        if any(p in normalized for p in ["death over", "death overs"]):
            return "death_over_stats"

        if any(p in normalized for p in ["vs", "versus", "compare", "comparison"]):
            return "player_comparison"

        if any(p in normalized for p in ["strike rate"]):
            return "strike_rate_leaders"

        return "general_analytics"