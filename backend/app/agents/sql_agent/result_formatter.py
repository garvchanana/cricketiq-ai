from app.nlp.canonicalization.canonicalizer import Canonicalizer


class ResultFormatter:

    # Fields that contain player names needing canonicalization
    PLAYER_FIELDS = {
        "batsman",
        "bowler",
        "player_name"
    }

    # ---------------------------------------------------------------------------
    # Intent -> human readable label
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

    # Intent -> which field is the primary subject (used in narrative)
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

    # Intent -> primary metric field (used in narrative)
    METRIC_FIELD = {
        "top_batters_by_runs":      "total_runs",
        "top_bowlers_by_wickets":   "wickets",
        "best_bowlers_by_economy":  "economy_rate",
        "top_batting_venues":       "average_run_rate",
        "top_players_by_ranking":   "ranking_score",
        "top_teams_by_runs":        "total_runs",
        "strike_rate_leaders":      "strike_rate",
    }

    # Intent -> chart type suggestion for frontend
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

    # Phase D.7 fix — metric display config for rich comparison narratives
    # (label, higher_is_better) per metric field
    COMPARISON_METRIC_CONFIG = {
        "total_runs":       ("runs",             True),
        "strike_rate":      ("strike rate",       True),
        "batting_average":  ("batting average",   True),
        "wickets":          ("wickets",           True),
        "economy_rate":     ("economy rate",       False),
        "bowling_average":  ("bowling average",    False),
        "ranking_score":    ("overall rating",     True),
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
    # Phase D.7 fix — rich comparison narrative
    # Builds a genuine metric-by-metric comparison instead of just
    # naming a single "leader", using every relevant column present
    # in the two compared rows.
    # ---------------------------------------------------------------------------

    @classmethod
    def _build_comparison_details(
        cls,
        row1: dict,
        row2: dict,
        subject_field: str
    ) -> str:

        name1 = row1.get(subject_field, "Player 1")
        name2 = row2.get(subject_field, "Player 2")

        comparisons = []

        for key, (label, higher_is_better) in cls.COMPARISON_METRIC_CONFIG.items():

            if key not in row1 or key not in row2:
                continue

            v1 = row1[key]
            v2 = row2[key]

            if v1 is None or v2 is None:
                continue
            if v1 == 0 and v2 == 0:
                continue

            if isinstance(v1, float):
                v1 = round(v1, 2)
            if isinstance(v2, float):
                v2 = round(v2, 2)

            if v1 == v2:
                comparisons.append(f"they are level on {label} ({v1})")
                continue

            if higher_is_better:
                leader, leader_val, other_val = (
                    (name1, v1, v2) if v1 > v2 else (name2, v2, v1)
                )
            else:
                leader, leader_val, other_val = (
                    (name1, v1, v2) if v1 < v2 else (name2, v2, v1)
                )

            comparisons.append(
                f"{leader} has the better {label} ({leader_val} vs {other_val})"
            )

        if not comparisons:
            return ""

        return "; ".join(comparisons) + "."

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

        # --- Comparison detection: rich metric-by-metric comparison ---------
        # Phase D.7 final fix — the intent classifier does not reliably
        # tag every comparison-shaped question as "player_comparison"
        # (e.g. "How is X different from Y" was classified as
        # "general_analytics" instead). Detect comparisons structurally
        # instead: exactly 2 rows, both containing a player name field,
        # regardless of what intent string was assigned.
        is_comparison_shape = (
            len(rows) == 2
            and any(f in rows[0] for f in cls.PLAYER_FIELDS)
            and any(f in rows[1] for f in cls.PLAYER_FIELDS)
        )

        if intent == "player_comparison" or is_comparison_shape:

            if len(rows) == 2:
                subj = subject_field or next(
                    (f for f in cls.PLAYER_FIELDS if f in rows[0]),
                    "batsman"
                )
                name1 = rows[0].get(subj, "Player 1")
                name2 = rows[1].get(subj, "Player 2")

                details = cls._build_comparison_details(
                    row1=rows[0],
                    row2=rows[1],
                    subject_field=subj
                )

                if details:
                    return f"Comparing {name1} and {name2}: {details}"

            # Fallback — 3+ players or no comparable metrics found,
            # keep the original per-player listing behaviour
            subj = subject_field or "batsman"
            parts = []
            for row in rows:
                name   = row.get(subj, "Unknown")
                values = ", ".join(
                    f"{k.replace('_', ' ')}: {v}"
                    for k, v in row.items()
                    if k != subj
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