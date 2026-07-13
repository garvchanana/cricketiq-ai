from sqlalchemy.orm import Session

from app.database.models.player_mapping import (
    PlayerMapping
)


class PlayerNormalizationService:

    @staticmethod
    def normalize_player_name(
        db: Session,
        raw_name: str
    ):

        mapping = (
            db.query(PlayerMapping)
            .filter(
                PlayerMapping.raw_name == raw_name
            )
            .first()
        )

        if mapping:
            return mapping.canonical_name

        return raw_name