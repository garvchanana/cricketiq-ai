class SchemaLoader:

    ALLOWED_SCHEMA = {

        "player_batting_stats": {
            "description": "Aggregated IPL batting statistics by player.",
            "columns": [
                "id",
                "batsman",
                "total_runs",
                "balls_faced",
                "strike_rate",
                "total_fours",
                "total_sixes",
                "dot_balls",
                "batting_average"
            ]
        },

        "player_bowling_stats": {
            "description": "Aggregated IPL bowling statistics by player.",
            "columns": [
                "id",
                "bowler",
                "balls_bowled",
                "runs_conceded",
                "wickets",
                "economy_rate",
                "bowling_strike_rate",
                "dot_balls",
                "bowling_average"
            ]
        },

        "advanced_batting_stats": {
            "description": "Advanced batting metrics by batter.",
            "columns": [
                "id",
                "batsman",
                "total_boundaries",
                "boundary_percentage",
                "dot_ball_percentage",
                "aggression_index",
                "pressure_release_index"
            ]
        },

        "player_rankings": {
            "description": "Combined player ranking scores.",
            "columns": [
                "id",
                "player_name",
                "role",
                "ranking_score",
                "total_runs",
                "strike_rate",
                "total_wickets",
                "economy_rate"
            ]
        },

        "venue_stats": {
            "description": "Aggregated venue scoring and style metrics.",
            "columns": [
                "id",
                "venue",
                "total_matches",
                "total_runs",
                "total_balls",
                "average_run_rate",
                "total_boundaries",
                "dot_ball_percentage",
                "venue_type"
            ]
        },

        "team_stats": {
            "description": "Aggregated team scoring metrics.",
            "columns": [
                "id",
                "team_name",
                "total_runs",
                "total_balls",
                "run_rate",
                "total_boundaries",
                "dot_balls",
                "aggression_index",
                "pressure_index"
            ]
        },

        "batter_bowler_matchups": {
            "description": "Batter versus bowler matchup metrics.",
            "columns": [
                "id",
                "batsman",
                "bowler",
                "total_runs",
                "balls_faced",
                "dismissals",
                "strike_rate",
                "dot_ball_percentage",
                "dominance_index"
            ]
        },

        "match_phase_stats": {
            "description": "Powerplay, middle-over, and death-over phase metrics.",
            "columns": [
                "id",
                "phase",
                "total_runs",
                "total_balls",
                "run_rate",
                "wickets",
                "dot_balls",
                "boundaries"
            ]
        },

        "matches": {
            "description": "IPL match metadata.",
            "columns": [
                "match_id",
                "team1",
                "team2",
                "venue",
                "match_type",
                "winner",
                "toss_winner",
                "match_date"
            ]
        }
    }

    TABLE_ALIASES = {

        "player_batting_stats": [
            "batting",
            "batter",
            "batsman",
            "runs",
            "strike rate",
            "fours",
            "sixes",
            "average"
        ],

        "player_bowling_stats": [
            "bowling",
            "bowler",
            "wickets",
            "economy",
            "dot balls",
            "strike rate"
        ],

        "advanced_batting_stats": [
            "aggressive",
            "aggression",
            "boundary",
            "boundaries",
            "pressure release",
            "dot ball percentage"
        ],

        "player_rankings": [
            "ranking",
            "rankings",
            "best player",
            "top player",
            "all rounder",
            "all-rounder"
        ],

        "venue_stats": [
            "venue",
            "ground",
            "stadium",
            "run rate",
            "batting venue"
        ],

        "team_stats": [
            "team",
            "teams",
            "franchise",
            "run rate",
            "aggression"
        ],

        "batter_bowler_matchups": [
            "matchup",
            "matchups",
            "versus",
            "vs",
            "against",
            "batter bowler"
        ],

        "match_phase_stats": [
            "phase",
            "powerplay",
            "middle overs",
            "death overs"
        ],

        "matches": [
            "matches",
            "match date",
            "winner",
            "toss",
            "date"
        ]
    }

    METRIC_ALIASES = {

        "runs":
        "total_runs",

        "strike rate":
        "strike_rate",

        "batting average":
        "batting_average",

        "wickets":
        "wickets",

        "economy":
        "economy_rate",

        "bowling average":
        "bowling_average",

        "bowling strike rate":
        "bowling_strike_rate",

        "boundaries":
        "total_boundaries",

        "fours":
        "total_fours",

        "sixes":
        "total_sixes",

        "run rate":
        "run_rate",

        "average run rate":
        "average_run_rate",

        "ranking":
        "ranking_score"
    }

    RELATIONSHIPS = [
        {
            "left_table": "player_batting_stats",
            "left_column": "batsman",
            "right_table": "player_rankings",
            "right_column": "player_name",
            "relationship": "player batting rows can be joined to player rankings by player name"
        },
        {
            "left_table": "player_bowling_stats",
            "left_column": "bowler",
            "right_table": "player_rankings",
            "right_column": "player_name",
            "relationship": "player bowling rows can be joined to player rankings by player name"
        },
        {
            "left_table": "batter_bowler_matchups",
            "left_column": "batsman",
            "right_table": "player_batting_stats",
            "right_column": "batsman",
            "relationship": "matchup batters can be compared with aggregate batting stats"
        },
        {
            "left_table": "batter_bowler_matchups",
            "left_column": "bowler",
            "right_table": "player_bowling_stats",
            "right_column": "bowler",
            "relationship": "matchup bowlers can be compared with aggregate bowling stats"
        },
        {
            "left_table": "matches",
            "left_column": "venue",
            "right_table": "venue_stats",
            "right_column": "venue",
            "relationship": "matches can be grouped by venue and compared with venue analytics"
        }
    ]

    @classmethod
    def get_allowed_schema(
        cls
    ):

        return cls.ALLOWED_SCHEMA

    @classmethod
    def get_allowed_tables(
        cls
    ):

        return set(
            cls.ALLOWED_SCHEMA.keys()
        )

    @classmethod
    def get_schema_context(
        cls
    ):

        lines = []

        for table_name, table_info in cls.ALLOWED_SCHEMA.items():

            columns = ", ".join(
                table_info["columns"]
            )

            lines.append(
                f"{table_name}: {columns}"
            )

        return "\n".join(
            lines
        )

    @classmethod
    def get_relationships(
        cls
    ):

        return cls.RELATIONSHIPS

    @classmethod
    def get_metric_aliases(
        cls
    ):

        return cls.METRIC_ALIASES

    @classmethod
    def get_table_profile(
        cls,
        table_name: str
    ):

        table_info = cls.ALLOWED_SCHEMA.get(
            table_name
        )

        if not table_info:

            return None

        return {
            "table":
            table_name,

            "description":
            table_info[
                "description"
            ],

            "columns":
            table_info[
                "columns"
            ],

            "aliases":
            cls.TABLE_ALIASES.get(
                table_name,
                []
            )
        }

    @classmethod
    def get_relevant_tables(
        cls,
        question: str
    ):

        normalized = (
            question or ""
        ).lower()

        relevant_tables = []

        for table_name, aliases in cls.TABLE_ALIASES.items():

            if any(
                alias in normalized
                for alias in aliases
            ):

                relevant_tables.append(
                    table_name
                )

        if not relevant_tables:

            relevant_tables = [
                "player_batting_stats",
                "player_bowling_stats",
                "player_rankings"
            ]

        return relevant_tables

    @classmethod
    def get_relevant_schema(
        cls,
        question: str
    ):

        relevant_tables = cls.get_relevant_tables(
            question
        )

        return {
            table_name:
            cls.get_table_profile(
                table_name
            )
            for table_name in relevant_tables
        }

    @classmethod
    def get_query_guidance(
        cls,
        question: str
    ):

        relevant_tables = cls.get_relevant_tables(
            question
        )

        return {
            "question":
            question,

            "relevant_tables":
            relevant_tables,

            "relevant_schema":
            cls.get_relevant_schema(
                question
            ),

            "metric_aliases":
            cls.METRIC_ALIASES,

            "relationships":
            [
                relationship
                for relationship in cls.RELATIONSHIPS
                if (
                    relationship[
                        "left_table"
                    ] in relevant_tables
                    or relationship[
                        "right_table"
                    ] in relevant_tables
                )
            ]
        }
