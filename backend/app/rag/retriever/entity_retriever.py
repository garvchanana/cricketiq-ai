import re

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

    # ---------------------------------------------------------------------------
    # Whole-word player name matcher
    #
    # Names used to be found with plain substring checks, so "Virat Kohli"
    # also matched the shortcode "T Kohli" (it contains "t Kohli"), and
    # "Mahendra Singh Dhoni" matched "A Singh". Names are now matched as whole
    # words, longest name first, and reported in the order they appear in the
    # question.
    # ---------------------------------------------------------------------------

    _name_pattern = None
    _name_lookup  = None

    @classmethod
    def _build_name_matcher(cls):

        if cls._name_pattern is not None:
            return

        lookup = {}

        for alias, canonical_name in PLAYER_REGISTRY.items():
            lookup[alias.lower()]          = canonical_name
            lookup[canonical_name.lower()] = canonical_name

        names = sorted(lookup, key=len, reverse=True)

        cls._name_lookup  = lookup
        cls._name_pattern = re.compile(
            r"(?<!\w)(?:"
            + "|".join(re.escape(name) for name in names)
            + r")(?!\w)",
            re.IGNORECASE
        )

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

    @classmethod
    def _candidate_names(
        cls,
        query: str,
        db: Session = None
    ):

        query = (
            query or ""
        ).strip()

        candidates = []

        def add_candidate(name):
            # The intelligence table stores canonical full names
            # ("Shreyas Iyer"), while the registry holds database shortcodes
            # ("SS Iyer"). Every candidate is therefore added together with
            # its canonical form, otherwise the lookup can never match
            # players whose shortcode differs from their name.
            if not name:
                return

            for variant in (name, PLAYER_REGISTRY.get(name, name)):
                if variant and variant not in candidates:
                    candidates.append(variant)

        add_candidate(query)

        cls._build_name_matcher()

        for match in cls._name_pattern.finditer(query):

            typed     = match.group(0)
            canonical = cls._name_lookup[typed.lower()]

            add_candidate(canonical)
            add_candidate(CANONICAL_TO_ALIAS.get(canonical))
            add_candidate(typed)

        if db is not None:

            mappings = (
                db.query(
                    PlayerMapping
                )
                .all()
            )

            for mapping in mappings:

                for name in (
                    mapping.raw_name,
                    mapping.canonical_name
                ):

                    if name and re.search(
                        r"(?<!\w)" + re.escape(name) + r"(?!\w)",
                        query,
                        re.IGNORECASE
                    ):

                        add_candidate(mapping.canonical_name)
                        add_candidate(mapping.raw_name)

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