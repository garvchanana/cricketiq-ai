from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models.player_intelligence import (
    PlayerIntelligence
)
from app.database.models.player_mapping import (
    PlayerMapping
)
from app.nlp.canonicalization.player_registry import (
    CANONICAL_TO_ALIAS,
    PLAYER_REGISTRY
)


class EntityRetriever:

    @staticmethod
    def find_exact_player(
        db: Session,
        player_name: str
    ):

        return (

            db.query(
                PlayerIntelligence
            )

            .filter(
                PlayerIntelligence.player_name
                == player_name
            )

            .first()
        )

    @staticmethod
    def _candidate_names(
        query: str,
        db: Session = None
    ):

        query = (
            query or ""
        ).strip()

        lower_query = query.lower()

        candidates = []

        def add_candidate(name):
            if (
                name
                and name not in candidates
            ):
                candidates.append(name)

        add_candidate(query)

        for alias, canonical_name in PLAYER_REGISTRY.items():

            if alias.lower() in lower_query:

                add_candidate(alias)

            if canonical_name.lower() in lower_query:

                add_candidate(alias)

        for canonical_name, alias in CANONICAL_TO_ALIAS.items():

            if canonical_name.lower() in lower_query:

                add_candidate(alias)

        if db is not None:

            mappings = (
                db.query(
                    PlayerMapping
                )
                .all()
            )

            for mapping in mappings:

                raw_name = mapping.raw_name
                canonical_name = mapping.canonical_name

                if (
                    raw_name
                    and raw_name.lower() in lower_query
                ):

                    add_candidate(raw_name)

                if (
                    canonical_name
                    and canonical_name.lower() in lower_query
                ):

                    add_candidate(raw_name)

        return candidates

    @classmethod
    def find_player_for_query(
        cls,
        db: Session,
        query: str
    ):

        candidates = cls._candidate_names(
            query,
            db=db
        )

        if not candidates:

            return None

        normalized_candidates = [
            candidate.lower()
            for candidate in candidates
        ]

        players = (
            db.query(
                PlayerIntelligence
            )
            .filter(
                func.lower(
                    PlayerIntelligence.player_name
                ).in_(
                    normalized_candidates
                )
            )
            .all()
        )

        players_by_name = {
            player.player_name.lower(): player
            for player in players
        }

        for candidate in normalized_candidates:

            if candidate in players_by_name:

                return players_by_name[
                    candidate
                ]

        return None
