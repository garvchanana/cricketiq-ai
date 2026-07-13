from sqlalchemy.orm import Session

from app.database.models.match import Match


class MatchService:

    @staticmethod
    def bulk_create_matches(
        db: Session,
        matches_data: list
    ):

        matches = []

        for match_data in matches_data:

            match = Match(
                match_id=match_data.get("id"),
                team1=match_data.get("team1"),
                team2=match_data.get("team2"),
                venue=match_data.get("venue"),
                match_type=match_data.get("matchType"),
                winner=match_data.get("winner"),
                toss_winner=match_data.get("tossWinner"),
                match_date=match_data.get("matchDate")
            )

            matches.append(match)

        db.bulk_save_objects(matches)

        db.commit()

        return matches