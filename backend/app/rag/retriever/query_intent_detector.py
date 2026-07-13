class QueryIntentDetector:

    @staticmethod
    def detect_intent(
        query: str
    ):

        query = (
            query or ""
        ).lower()

        if any(
            word in query
            for word in [
                "aggressive",
                "strike rate",
                "attacking"
            ]
        ):
            return "aggressive_batter"

        if any(
            word in query
            for word in [
                "finisher",
                "death overs"
            ]
        ):
            return "finisher"

        if any(
            word in query
            for word in [
                "anchor",
                "consistent"
            ]
        ):
            return "anchor"

        if any(
            word in query
            for word in [
                "bowler",
                "wicket"
            ]
        ):
            return "bowler"

        return "general"