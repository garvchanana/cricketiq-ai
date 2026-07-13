from app.nlp.canonicalization.canonicalizer import Canonicalizer
 
 
class ResultFormatter:
 
    # Fields that contain player names needing canonicalization
    PLAYER_FIELDS = {
        "batsman",
        "bowler",
        "player_name"
    }
 
    # ---------------------------------------------------------------------------
    # Intent → human readable label
    # ---------------------------------------------------------------------------
 
    INTENT_LABELS = {
        "top_batters_by_runs":      "Top IPL batters by runs",
        "top_bowlers_by_wickets":   "Top IPL bowlers by wickets",
        "best_bowlers_by_economy":  "Best IPL bowlers by economy rate",
        "top_batting_venues":       "Top IPL venues by scoring rate",
        "top_players_by_ranking":   "Top IPL players by overall ranking",
        "top_teams_by_runs":        "Top IPL teams by total runs",
        "powerplay_stats":          "IPL powerplay phase statistics",
        "death_over_stats":         "IPL death overs phase statistics",
        "player_comparison":        "IPL player comparison",
        "strike_rate_leaders":      "IPL strike rate leaders",
        "general_analytics":        "IPL analytics result",
    }
 
    # Intent → which field is the primary subject (used in narrative)
    SUBJECT_FIELD = {
        "top_batters_by_runs":      "batsman",
        "top_bowlers_by_wickets":   "bowler",
        "best_bowlers_by_economy":  "bowler",
        "top_batting_venues":       "venue",
        "top_players_by_ranking":   "player_name",
        "top_teams_by_runs":        "team_name",
        "player_comparison":        "batsman",
        "strike_rate_leaders":      "batsman",
    }
 
    # Intent → primary metric field (used in narrative)
    METRIC_FIELD = {
        "top_batters_by_runs":      "total_runs",
        "top_bowlers_by_wickets":   "wickets",
        "best_bowlers_by_economy":  "economy_rate",
        "top_batting_venues":       "average_run_rate",
        "top_players_by_ranking":   "ranking_score",
        "top_teams_by_runs":        "total_runs",
        "strike_rate_leaders":      "strike_rate",
    }
 
    # Intent → chart type suggestion for frontend
    CHART_MAP = {
        "top_batters_by_runs":      "bar",
        "top_bowlers_by_wickets":   "bar",
        "best_bowlers_by_economy":  "bar",
        "top_batting_venues":       "bar",
        "top_players_by_ranking":   "bar",
        "top_teams_by_runs":        "bar",
        "powerplay_stats":          "pie",
        "death_over_stats":         "pie",
        "player_comparison":        "radar",
        "strike_rate_leaders":      "bar",
        "general_analytics":        "table",
    }
 
    # ---------------------------------------------------------------------------
    # Canonicalize player names in rows
    # ---------------------------------------------------------------------------
 
    @classmethod
    def _canonicalize_rows(cls, rows: list, db=None) -> list:
 
        if not rows:
            return rows
 
        canonicalized = []
 
        for row in rows:
            updated_row = dict(row)
 
            for field in cls.PLAYER_FIELDS:
                if field in updated_row and updated_row[field]:
                    updated_row[field] = Canonicalizer.canonicalize(
                        player_name=updated_row[field],
                        db=db
                    )
 
            canonicalized.append(updated_row)
 
        return canonicalized
 
    # ---------------------------------------------------------------------------
    # Narrative answer builder
    # ---------------------------------------------------------------------------
 
    @classmethod
    def _build_narrative(
        cls,
        rows: list,
        intent: str,
        label: str
    ) -> str:
 
        if not rows:
            return "No matching records were found for this query."
 
        subject_field = cls.SUBJECT_FIELD.get(intent)
        metric_field  = cls.METRIC_FIELD.get(intent)
 
        # --- Comparison intent: show all rows equally ---
        if intent == "player_comparison":
            parts = []
            for row in rows:
                name   = row.get(subject_field or "batsman", "Unknown")
                values = ", ".join(
                    f"{k.replace('_', ' ')}: {v}"
                    for k, v in row.items()
                    if k != subject_field
                )
                parts.append(f"{name} — {values}")
 
            return f"{label}:\n" + "\n".join(parts)
 
        # --- Phase stats: no single subject field ---
        if intent in ("powerplay_stats", "death_over_stats"):
            if rows:
                row    = rows[0]
                values = ", ".join(
                    f"{k.replace('_', ' ')}: {v}"
                    for k, v in row.items()
                )
                return f"{label}: {values}."
            return f"{label}: No phase data available."
 
        # --- Ranking intents: narrative with top entry leading ---
        if subject_field and metric_field:
            top_row  = rows[0]
            top_name = top_row.get(subject_field, "Unknown")
            top_val  = top_row.get(metric_field, "N/A")
 
            # Format metric value cleanly
            if isinstance(top_val, float):
                top_val = round(top_val, 2)
 
            metric_label = metric_field.replace("_", " ")
 
            narrative = (
                f"{label}: {top_name} leads with "
                f"{top_val} {metric_label}"
            )
 
            if len(rows) > 1:
                runner_up      = rows[1].get(subject_field, "")
                runner_up_val  = rows[1].get(metric_field, "")
                if isinstance(runner_up_val, float):
                    runner_up_val = round(runner_up_val, 2)
 
                narrative += (
                    f", followed by {runner_up} "
                    f"({runner_up_val} {metric_label})"
                )
 
            narrative += f". {len(rows)} record(s) returned."
            return narrative
 
        # --- General fallback ---
        first_val = next(iter(rows[0].values()), "N/A")
        return (
            f"{label}: {first_val} leads the result. "
            f"{len(rows)} record(s) returned."
        )
 
    # ---------------------------------------------------------------------------
    # Public format method — called by SQLAgentService and /ask route
    # ---------------------------------------------------------------------------
 
    @classmethod
    def format(
        cls,
        rows: list,
        intent: str,
        db=None
    ) -> dict:
        """
        Convert raw SQL result rows into a cricket-friendly response.
 
        Parameters
        ----------
        rows   : raw list of dicts from QueryExecutor
        intent : intent string from SQLGenerator
        db     : SQLAlchemy session for canonicalization (optional)
 
        Returns
        -------
        {
            "answer":           str,   narrative answer
            "rows":             list,  canonicalized rows
            "row_count":        int,
            "chart_suggestion": str,   hint for frontend chart type
            "intent":           str
        }
        """
 
        # Step 1 — canonicalize player names in rows
        clean_rows = cls._canonicalize_rows(rows=rows, db=db)
 
        # Step 2 — resolve label and chart type
        label          = cls.INTENT_LABELS.get(intent, "IPL analytics result")
        chart_type     = cls.CHART_MAP.get(intent, "table")
 
        # Step 3 — build narrative
        narrative = cls._build_narrative(
            rows=clean_rows,
            intent=intent,
            label=label
        )
 
        return {
            "answer":           narrative,
            "rows":             clean_rows,
            "row_count":        len(clean_rows),
            "chart_suggestion": chart_type,
            "intent":           intent
        }