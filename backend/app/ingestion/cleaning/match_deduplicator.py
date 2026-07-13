from sqlalchemy.orm import Session

from app.database.models.match import Match


class MatchDeduplicator:

    @staticmethod
    def match_exists(
        db: Session,
        match_id: str
    ):

        return (
            db.query(Match)
            .filter(Match.match_id == match_id)
            .first()
        )