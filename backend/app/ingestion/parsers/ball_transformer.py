class BallTransformer:

    @staticmethod
    def transform(
        match_id: str,
        innings_number: int,
        batting_team: str,
        venue: str,
        over_number: float,
        delivery: dict
    ):

        wicket_data = delivery.get("wickets", [])

        wicket = bool(wicket_data)

        dismissal_type = None

        if wicket_data:
            dismissal_type = (
                wicket_data[0]
                .get("kind")
            )

        return {
            "match_id": match_id,
            "innings": innings_number,
            "over_number": over_number,
            "batting_team": batting_team,
            "venue": venue,
            "batsman": delivery.get("batter"),
            "bowler": delivery.get("bowler"),
            "non_striker": delivery.get("non_striker"),
            "runs_scored": (
                delivery.get("runs", {})
                .get("batter", 0)
            ),
            "extras": (
                delivery.get("runs", {})
                .get("extras", 0)
            ),
            "wicket": wicket,
            "dismissal_type": dismissal_type,
            "commentary": None
        }