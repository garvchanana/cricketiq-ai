from app.database.models.player_intelligence import PlayerIntelligence
from app.database.models.player_rankings import PlayerRankings
from app.database.models.player_batting_stats import PlayerBattingStats
from app.database.models.player_bowling_stats import PlayerBowlingStats
from app.llm.groq_client import GroqClient
from app.nlp.canonicalization.canonicalizer import Canonicalizer


class PlayerAnalyst:
    """
    Phase 8.1 — Player Analyst Agent

    Specialized agent that owns player intelligence.
    Sits on top of existing services and adds reasoning.

    Responsibilities:
    - Fetch full player profile from player_intelligence table
    - Fetch detailed stats from batting/bowling stats tables
    - Fetch ranking score and role classification
    - Generate an AI-powered player analysis narrative
    - Return structured profile for use by FinalAnswerAgent

    Called by:
    - FinalAnswerAgent (Phase 8.4) for complex questions
    - /ask endpoint directly for profile questions
    """

    # ---------------------------------------------------------------------------
    # Primary method — full player profile
    # ---------------------------------------------------------------------------

    @classmethod
    def get_player_profile(
        cls,
        player_name: str,
        db
    ) -> dict:
        """
        Build a complete player profile from all available data sources.

        Parameters
        ----------
        player_name : canonical player name
        db          : SQLAlchemy session

        Returns
        -------
        {
            "player_name":    str,
            "canonical_name": str,
            "role":           str,
            "batting":        dict,
            "bowling":        dict,
            "ranking":        dict,
            "intelligence":   dict,
            "narrative":      str,
            "found":          bool
        }
        """

        # ── Step 1: Resolve canonical name ───────────────────────────────────
        canonical = Canonicalizer.canonicalize(
            player_name=player_name,
            db=db
        )

        # ── Step 2: Build name variants to try ──────────────────────────────
        # DB stores Cricsheet shortcodes (e.g. "MS Dhoni", "V Kohli")
        # Canonicalizer returns full names ("Mahendra Singh Dhoni")
        # CANONICAL_TO_ALIAS maps full names back to DB shortcodes
        # We try ALL variants so lookups succeed regardless of DB format
        from app.nlp.canonicalization.player_registry import CANONICAL_TO_ALIAS

        db_alias = CANONICAL_TO_ALIAS.get(canonical)

        name_variants = list(dict.fromkeys(filter(None, [
            player_name,   # original input e.g. "Rohit Sharma"
            canonical,     # canonical full name e.g. "Rohit Sharma"
            db_alias,      # DB shortcode e.g. "RG Sharma"
        ])))

        # ── Step 3: Fetch intelligence record ────────────────────────────────
        intelligence = cls._fetch_intelligence_multi(
            name_variants=name_variants,
            db=db
        )

        # ── Step 4: Fetch batting stats ───────────────────────────────────────
        batting = cls._fetch_batting_stats_multi(
            name_variants=name_variants,
            db=db
        )

        # ── Step 5: Fetch bowling stats ───────────────────────────────────────
        bowling = cls._fetch_bowling_stats_multi(
            name_variants=name_variants,
            db=db
        )

        # ── Step 6: Fetch ranking ─────────────────────────────────────────────
        ranking = cls._fetch_ranking_multi(
            name_variants=name_variants,
            db=db
        )

        # ── Step 7: Check if player was found ────────────────────────────────
        found = (
            intelligence is not None
            or batting is not None
            or ranking is not None
        )

        if not found:
            return cls._not_found(
                player_name=player_name,
                canonical=canonical
            )

        # ── Step 8: Generate AI narrative ────────────────────────────────────
        narrative = cls._generate_narrative(
            canonical=canonical,
            intelligence=intelligence,
            batting=batting,
            bowling=bowling,
            ranking=ranking
        )

        return {
            "player_name":    player_name,
            "canonical_name": canonical,
            "role":           intelligence.get("role") if intelligence else ranking.get("role") if ranking else "Unknown",
            "batting":        batting,
            "bowling":        bowling,
            "ranking":        ranking,
            "intelligence":   intelligence,
            "narrative":      narrative,
            "found":          True
        }

    # ---------------------------------------------------------------------------
    # Comparison method — two players side by side
    # ---------------------------------------------------------------------------

    @classmethod
    def compare_players(
        cls,
        player_one: str,
        player_two: str,
        db
    ) -> dict:
        """
        Build side-by-side profiles for two players.
        Used by FinalAnswerAgent for comparison questions.
        """

        profile_one = cls.get_player_profile(
            player_name=player_one,
            db=db
        )

        profile_two = cls.get_player_profile(
            player_name=player_two,
            db=db
        )

        comparison_narrative = cls._generate_comparison_narrative(
            profile_one=profile_one,
            profile_two=profile_two
        )

        return {
            "player_one":             profile_one,
            "player_two":             profile_two,
            "comparison_narrative":   comparison_narrative,
            "both_found":             profile_one["found"] and profile_two["found"]
        }

    # ---------------------------------------------------------------------------
    # Top players method — leaderboard style
    # ---------------------------------------------------------------------------

    @classmethod
    def get_top_players(
        cls,
        role: str = None,
        limit: int = 10,
        db = None
    ) -> dict:
        """
        Fetch top ranked players, optionally filtered by role.
        Roles: "Batter", "Bowler", "All-Rounder"
        """

        query = db.query(PlayerRankings).order_by(
            PlayerRankings.ranking_score.desc()
        )

        if role:
            query = query.filter(PlayerRankings.role == role)

        records = query.limit(limit).all()

        players = [
            {
                "player_name":    Canonicalizer.canonicalize(
                                      player_name=r.player_name,
                                      db=db
                                  ),
                "raw_name":       r.player_name,
                "role":           r.role,
                "ranking_score":  round(float(r.ranking_score or 0), 2),
                "total_runs":     int(r.total_runs or 0),
                "strike_rate":    round(float(r.strike_rate or 0), 2),
                "total_wickets":  int(r.total_wickets or 0),
                "economy_rate":   round(float(r.economy_rate or 0), 2)
            }
            for r in records
        ]

        return {
            "role":       role or "All",
            "limit":      limit,
            "players":    players,
            "count":      len(players)
        }

    # ---------------------------------------------------------------------------
    # Private — multi-variant fetch methods
    # Tries each name variant until a DB record is found
    # Handles both shortcodes ("MS Dhoni") and full names ("Mahendra Singh Dhoni")
    # ---------------------------------------------------------------------------

    @staticmethod
    def _fetch_intelligence_multi(
        name_variants: list,
        db
    ) -> dict | None:

        for name in name_variants:
            record = db.query(PlayerIntelligence).filter(
                PlayerIntelligence.player_name == name
            ).first()
            if record:
                return {
                    "role":                 record.role,
                    "batting_summary":      record.batting_summary,
                    "bowling_summary":      record.bowling_summary,
                    "overall_rating":       round(float(record.overall_rating or 0), 2),
                    "intelligence_summary": record.intelligence_summary
                }
        return None

    @staticmethod
    def _fetch_batting_stats_multi(
        name_variants: list,
        db
    ) -> dict | None:

        for name in name_variants:
            record = db.query(PlayerBattingStats).filter(
                PlayerBattingStats.batsman == name
            ).first()
            if record:
                return {
                    "total_runs":      int(record.total_runs or 0),
                    "balls_faced":     int(record.balls_faced or 0),
                    "strike_rate":     round(float(record.strike_rate or 0), 2),
                    "batting_average": round(float(record.batting_average or 0), 2),
                    "total_fours":     int(record.total_fours or 0),
                    "total_sixes":     int(record.total_sixes or 0),
                    "dot_balls":       int(record.dot_balls or 0)
                }
        return None

    @staticmethod
    def _fetch_bowling_stats_multi(
        name_variants: list,
        db
    ) -> dict | None:

        for name in name_variants:
            record = db.query(PlayerBowlingStats).filter(
                PlayerBowlingStats.bowler == name
            ).first()
            if record:
                return {
                    "balls_bowled":        int(record.balls_bowled or 0),
                    "runs_conceded":       int(record.runs_conceded or 0),
                    "wickets":             int(record.wickets or 0),
                    "economy_rate":        round(float(record.economy_rate or 0), 2),
                    "bowling_strike_rate": round(float(record.bowling_strike_rate or 0), 2),
                    "bowling_average":     round(float(record.bowling_average or 0), 2),
                    "dot_balls":           int(record.dot_balls or 0)
                }
        return None

    @staticmethod
    def _fetch_ranking_multi(
        name_variants: list,
        db
    ) -> dict | None:

        for name in name_variants:
            record = db.query(PlayerRankings).filter(
                PlayerRankings.player_name == name
            ).first()
            if record:
                return {
                    "ranking_score":  round(float(record.ranking_score or 0), 2),
                    "role":           record.role,
                    "total_runs":     int(record.total_runs or 0),
                    "strike_rate":    round(float(record.strike_rate or 0), 2),
                    "total_wickets":  int(record.total_wickets or 0),
                    "economy_rate":   round(float(record.economy_rate or 0), 2),
                    "db_name":        name
                }
        return None

    # ---------------------------------------------------------------------------
    # Private — generate AI narrative for single player
    # ---------------------------------------------------------------------------

    @staticmethod
    def _generate_narrative(
        canonical:     str,
        intelligence:  dict | None,
        batting:       dict | None,
        bowling:       dict | None,
        ranking:       dict | None
    ) -> str:

        intel_text  = intelligence.get("intelligence_summary", "") if intelligence else ""
        batting_text = intelligence.get("batting_summary", "") if intelligence else ""
        bowling_text = intelligence.get("bowling_summary", "") if intelligence else ""

        batting_detail = ""
        if batting:
            batting_detail = (
                f"Batting — {batting['total_runs']} runs, "
                f"SR {batting['strike_rate']}, "
                f"Avg {batting['batting_average']}, "
                f"{batting['total_fours']} fours, "
                f"{batting['total_sixes']} sixes."
            )

        bowling_detail = ""
        if bowling and bowling.get("wickets", 0) > 0:
            bowling_detail = (
                f"Bowling — {bowling['wickets']} wickets, "
                f"Economy {bowling['economy_rate']}, "
                f"Avg {bowling['bowling_average']}."
            )

        ranking_text = ""
        if ranking:
            ranking_text = (
                f"Overall ranking score: {ranking['ranking_score']}. "
                f"Role: {ranking['role']}."
            )

        prompt = f"""You are CricketIQ, an IPL cricket analyst.
Write a concise, insightful player profile for {canonical} based on the data below.
Cover: playing style, key strengths, IPL impact, and one key insight.
Keep it under 150 words. Be specific and data-driven.

DATA:
{intel_text}
{batting_text}
{bowling_text}
{batting_detail}
{bowling_detail}
{ranking_text}

PLAYER PROFILE:"""

        try:
            return GroqClient.complete(
                system_prompt="You are a cricket analyst. Write concise, accurate player profiles.",
                user_prompt=prompt,
                temperature=0.4,
                max_tokens=200
            )
        except Exception as error:
            return intel_text or f"Profile data available for {canonical}."

    # ---------------------------------------------------------------------------
    # Private — generate comparison narrative
    # ---------------------------------------------------------------------------

    @staticmethod
    def _generate_comparison_narrative(
        profile_one: dict,
        profile_two: dict
    ) -> str:

        def summarize(p: dict) -> str:
            name    = p.get("canonical_name", "Unknown")
            batting = p.get("batting") or {}
            bowling = p.get("bowling") or {}
            ranking = p.get("ranking") or {}
            return (
                f"{name}: "
                f"{batting.get('total_runs', 0)} runs, "
                f"SR {batting.get('strike_rate', 0)}, "
                f"Avg {batting.get('batting_average', 0)}, "
                f"{bowling.get('wickets', 0)} wickets, "
                f"Economy {bowling.get('economy_rate', 0)}, "
                f"Rating {ranking.get('ranking_score', 0)}"
            )

        p1_summary = summarize(profile_one)
        p2_summary = summarize(profile_two)

        name_one = profile_one.get("canonical_name", "Player 1")
        name_two = profile_two.get("canonical_name", "Player 2")

        prompt = f"""You are CricketIQ, an IPL cricket analyst.
Compare these two IPL players objectively based on their stats.
Cover: batting comparison, bowling comparison, overall impact, and a verdict.
Keep it under 200 words. Be specific and data-driven.

{p1_summary}
{p2_summary}

COMPARISON:"""

        try:
            return GroqClient.complete(
                system_prompt="You are a cricket analyst. Write concise, accurate player comparisons.",
                user_prompt=prompt,
                temperature=0.4,
                max_tokens=250
            )
        except Exception as error:
            return f"Comparison between {name_one} and {name_two} based on available data."

    # ---------------------------------------------------------------------------
    # Not found response
    # ---------------------------------------------------------------------------

    @staticmethod
    def _not_found(
        player_name: str,
        canonical:   str
    ) -> dict:

        return {
            "player_name":    player_name,
            "canonical_name": canonical,
            "role":           None,
            "batting":        None,
            "bowling":        None,
            "ranking":        None,
            "intelligence":   None,
            "narrative":      (
                f"No player data found for '{player_name}'. "
                "Please check the spelling or try a different name."
            ),
            "found":          False
        }