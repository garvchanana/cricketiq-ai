from sqlalchemy.orm import Session

from app.database.models.player import Player


class PlayerDeduplicator:

    @staticmethod
    def player_exists(
        db: Session,
        api_player_id: str
    ):

        return (
            db.query(Player)
            .filter(Player.api_player_id == api_player_id)
            .first()
        )