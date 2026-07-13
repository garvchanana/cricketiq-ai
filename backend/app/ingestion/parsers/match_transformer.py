from datetime import datetime


class MatchTransformer:

    @staticmethod
    def transform(match_data: dict):

        date_value = None

        if match_data.get("date"):
            try:
                date_value = datetime.strptime(
                    match_data.get("date"),
                    "%Y-%m-%d"
                )
            except Exception:
                pass

        return {
            "id": match_data.get("id"),
            "team1": (
                match_data.get("teams", [None])[0]
            ),
            "team2": (
                match_data.get("teams", [None, None])[1]
            ),
            "venue": match_data.get("venue"),
            "matchType": match_data.get("matchType"),
            "winner": match_data.get("winner"),
            "tossWinner": match_data.get("tossWinner"),
            "matchDate": date_value
        }