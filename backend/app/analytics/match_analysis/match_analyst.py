from app.database.models.match import Match  # retained for future use
from app.database.models.match_phase_stats import MatchPhaseStats
from app.database.models.advanced_batting_stats import AdvancedBattingStats
from app.database.models.venue_stats import VenueStats
from app.llm.groq_client import GroqClient
from app.nlp.canonicalization.canonicalizer import Canonicalizer
from app.nlp.canonicalization.player_registry import CANONICAL_TO_ALIAS


class MatchAnalyst:
    """
    Phase 8.2 — Match Analyst Agent

    Specialized agent that owns match and phase intelligence.
    Sits on top of MatchService, AdvancedBattingService,
    MatchPhaseService data already in the DB.

    Responsibilities:
    - Fetch phase stats (Powerplay / Middle Overs / Death Overs)
    - Fetch advanced batting metrics per player
    - Fetch venue stats for match context
    - Fetch match records by team or venue
    - Generate AI narrative for phase and match analysis
    - Return structured data for FinalAnswerAgent

    Called by:
    - FinalAnswerAgent (Phase 8.4) for phase/match questions
    - /ask endpoint for venue and phase questions
    """

    # Phase names as stored in DB
    PHASES = ["Powerplay", "Middle Overs", "Death Overs"]

    # ---------------------------------------------------------------------------
    # Phase stats — all three phases
    # ---------------------------------------------------------------------------

    @classmethod
    def get_phase_summary(cls, db) -> dict:
        """
        Fetch stats for all three match phases from match_phase_stats table.
        Returns structured data plus AI narrative.
        """

        records = db.query(MatchPhaseStats).all()

        if not records:
            return {
                "phases":    {},
                "narrative": "No phase data available.",
                "found":     False
            }

        phases = {}
        for record in records:
            phases[record.phase] = {
                "phase":        record.phase,
                "total_runs":   int(record.total_runs or 0),
                "total_balls":  int(record.total_balls or 0),
                "run_rate":     round(float(record.run_rate or 0), 2),
                "wickets":      int(record.wickets or 0),
                "dot_balls":    int(record.dot_balls or 0),
                "boundaries":   int(record.boundaries or 0)
            }

        narrative = cls._generate_phase_narrative(phases=phases)

        return {
            "phases":    phases,
            "narrative": narrative,
            "found":     True
        }

    # ---------------------------------------------------------------------------
    # Single phase stats
    # ---------------------------------------------------------------------------

    @classmethod
    def get_phase_stats(
        cls,
        phase: str,
        db
    ) -> dict:
        """
        Fetch stats for a specific phase.
        phase: "Powerplay" | "Middle Overs" | "Death Overs"
        """

        # Normalise phase name
        phase_map = {
            "powerplay":    "Powerplay",
            "middle overs": "Middle Overs",
            "middle over":  "Middle Overs",
            "death overs":  "Death Overs",
            "death over":   "Death Overs",
        }

        normalised = phase_map.get(phase.lower(), phase)

        record = db.query(MatchPhaseStats).filter(
            MatchPhaseStats.phase == normalised
        ).first()

        if not record:
            return {
                "phase":     normalised,
                "found":     False,
                "narrative": f"No data found for phase: {normalised}"
            }

        stats = {
            "phase":       record.phase,
            "total_runs":  int(record.total_runs or 0),
            "total_balls": int(record.total_balls or 0),
            "run_rate":    round(float(record.run_rate or 0), 2),
            "wickets":     int(record.wickets or 0),
            "dot_balls":   int(record.dot_balls or 0),
            "boundaries":  int(record.boundaries or 0),
            "found":       True
        }

        stats["narrative"] = cls._generate_single_phase_narrative(stats)

        return stats

    # ---------------------------------------------------------------------------
    # Advanced batting — player aggression and pressure metrics
    # ---------------------------------------------------------------------------

    @classmethod
    def get_player_advanced_batting(
        cls,
        player_name: str,
        db
    ) -> dict:
        """
        Fetch advanced batting metrics for a player.
        Tries both canonical and DB shortcode name variants.
        """

        canonical = Canonicalizer.canonicalize(
            player_name=player_name,
            db=db
        )

        db_alias  = CANONICAL_TO_ALIAS.get(canonical)

        name_variants = list(dict.fromkeys(filter(None, [
            player_name,
            canonical,
            db_alias,
        ])))

        record = None
        for name in name_variants:
            record = db.query(AdvancedBattingStats).filter(
                AdvancedBattingStats.batsman == name
            ).first()
            if record:
                break

        if not record:
            return {
                "player_name": player_name,
                "canonical":   canonical,
                "found":       False,
                "narrative":   f"No advanced batting data found for {canonical}."
            }

        return {
            "player_name":           player_name,
            "canonical":             canonical,
            "total_boundaries":      int(record.total_boundaries or 0),
            "boundary_percentage":   round(float(record.boundary_percentage or 0), 2),
            "dot_ball_percentage":   round(float(record.dot_ball_percentage or 0), 2),
            "aggression_index":      round(float(record.aggression_index or 0), 2),
            "pressure_release_index": round(float(record.pressure_release_index or 0), 2),
            "found":                 True,
            "narrative": (
                f"{canonical} has a boundary percentage of "
                f"{round(float(record.boundary_percentage or 0), 2)}%, "
                f"dot ball percentage of "
                f"{round(float(record.dot_ball_percentage or 0), 2)}%, "
                f"aggression index of "
                f"{round(float(record.aggression_index or 0), 2)}, "
                f"and pressure release index of "
                f"{round(float(record.pressure_release_index or 0), 2)}."
            )
        }

    # ---------------------------------------------------------------------------
    # Venue analysis
    # ---------------------------------------------------------------------------

    @classmethod
    def get_venue_stats(
        cls,
        venue_name: str = None,
        limit: int = 10,
        db = None
    ) -> dict:
        """
        Fetch venue stats. If venue_name given, fetch specific venue.
        Otherwise fetch top venues by average run rate.
        """

        if venue_name:
            record = db.query(VenueStats).filter(
                VenueStats.venue.ilike(f"%{venue_name}%")
            ).first()

            if not record:
                return {
                    "venue":     venue_name,
                    "found":     False,
                    "narrative": f"No venue data found for '{venue_name}'."
                }

            return {
                "venue":               record.venue,
                "total_matches":       int(record.total_matches or 0),
                "total_runs":          int(record.total_runs or 0),
                "average_run_rate":    round(float(record.average_run_rate or 0), 2),
                "total_boundaries":    int(record.total_boundaries or 0),
                "dot_ball_percentage": round(float(record.dot_ball_percentage or 0), 2),
                "venue_type":          record.venue_type,
                "found":               True,
                "narrative": (
                    f"{record.venue} has hosted {record.total_matches} IPL matches "
                    f"with an average run rate of "
                    f"{round(float(record.average_run_rate or 0), 2)} runs per over."
                )
            }

        # Top venues by run rate
        records = db.query(VenueStats).order_by(
            VenueStats.average_run_rate.desc()
        ).limit(limit).all()

        venues = [
            {
                "venue":            r.venue,
                "total_matches":    int(r.total_matches or 0),
                "average_run_rate": round(float(r.average_run_rate or 0), 2),
                "total_boundaries": int(r.total_boundaries or 0),
                "venue_type":       r.venue_type
            }
            for r in records
        ]

        narrative = cls._generate_venue_narrative(venues=venues)

        return {
            "venues":    venues,
            "count":     len(venues),
            "narrative": narrative,
            "found":     True
        }

    # ---------------------------------------------------------------------------
    # Team match record
    # NOTE: matches table contains non-IPL data from terminated Cric API.
    # Team stats are derived from team_stats table which has real IPL data.
    # ---------------------------------------------------------------------------

    @classmethod
    def get_team_record(
        cls,
        team_name: str,
        limit: int = 20,
        db = None
    ) -> dict:
        """
        Fetch team performance from team_stats table.
        Falls back to venue_stats for context if needed.
        """
        from app.database.models.team_stats import TeamStats

        record = db.query(TeamStats).filter(
            TeamStats.team_name.ilike(f"%{team_name}%")
        ).first()

        if not record:
            return {
                "team":      team_name,
                "found":     False,
                "narrative": (
                    f"No team stats found for '{team_name}'. "
                    "Try the full team name e.g. 'Mumbai Indians'."
                )
            }

        return {
            "team":             record.team_name,
            "total_runs":       int(record.total_runs or 0),
            "total_balls":      int(record.total_balls or 0),
            "run_rate":         round(float(record.run_rate or 0), 2),
            "total_boundaries": int(record.total_boundaries or 0),
            "dot_balls":        int(record.dot_balls or 0),
            "aggression_index": round(float(record.aggression_index or 0), 2),
            "pressure_index":   round(float(record.pressure_index or 0), 2),
            "found":            True,
            "narrative": (
                f"{record.team_name} has scored {record.total_runs} IPL runs "
                f"at a run rate of {round(float(record.run_rate or 0), 2)} "
                f"with an aggression index of "
                f"{round(float(record.aggression_index or 0), 2)}."
            )
        }

    # ---------------------------------------------------------------------------
    # Private — phase narrative generators
    # ---------------------------------------------------------------------------

    @staticmethod
    def _generate_phase_narrative(phases: dict) -> str:

        lines = []
        for phase_name in ["Powerplay", "Middle Overs", "Death Overs"]:
            p = phases.get(phase_name)
            if p:
                lines.append(
                    f"{phase_name}: {p['run_rate']} RPO, "
                    f"{p['wickets']} wickets, "
                    f"{p['boundaries']} boundaries."
                )

        data_text = "\n".join(lines)

        prompt = f"""You are CricketIQ, an IPL match analyst.
Write a concise phase-by-phase analysis of IPL batting trends.
Cover powerplay aggression, middle overs consolidation, death overs finishing.
Under 120 words. Data-driven and specific.

PHASE DATA:
{data_text}

ANALYSIS:"""

        try:
            return GroqClient.complete(
                system_prompt="You are a cricket analyst. Write concise match phase analysis.",
                user_prompt=prompt,
                temperature=0.3,
                max_tokens=150
            )
        except Exception:
            return data_text

    @staticmethod
    def _generate_single_phase_narrative(stats: dict) -> str:

        return (
            f"In the {stats['phase']}, "
            f"the run rate is {stats['run_rate']} runs per over "
            f"with {stats['wickets']} wickets falling "
            f"and {stats['boundaries']} boundaries hit across "
            f"{stats['total_balls']} balls."
        )

    @staticmethod
    def _generate_venue_narrative(venues: list) -> str:

        if not venues:
            return "No venue data available."

        top = venues[0]
        return (
            f"{top['venue']} leads IPL venues with an average run rate of "
            f"{top['average_run_rate']} runs per over across "
            f"{top['total_matches']} matches. "
            f"{len(venues)} venues analysed."
        )