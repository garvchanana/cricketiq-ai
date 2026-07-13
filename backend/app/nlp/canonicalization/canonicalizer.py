from app.nlp.canonicalization.player_registry import (
    PLAYER_REGISTRY
)


class Canonicalizer:

    @staticmethod
    def _initials_from_name(
        name: str
    ):

        parts = [
            part
            for part in (
                name or ""
            ).replace(
                ".",
                " "
            ).split()
            if part
        ]

        if len(parts) < 2:

            return ""

        return "".join(
            part[0].lower()
            for part in parts[:-1]
            if part
        )

    @staticmethod
    def _surname(
        name: str
    ):

        parts = [
            part
            for part in (
                name or ""
            ).split()
            if part
        ]

        if not parts:

            return ""

        return parts[-1].lower()

    @classmethod
    def _resolve_from_players(
        cls,
        player_name: str,
        db
    ):

        raw_initials = cls._initials_from_name(
            player_name
        )

        raw_surname = cls._surname(
            player_name
        )

        if (
            not raw_initials
            or not raw_surname
        ):

            return None

        from sqlalchemy import func

        from app.database.models.player import (
            Player
        )

        candidates = (
            db.query(
                Player
            )
            .filter(
                func.lower(
                    Player.standardized_name
                ).like(
                    f"%{raw_surname}%"
                )
            )
            .all()
        )

        matches = []

        for candidate in candidates:

            display_name = (
                candidate.standardized_name
                or candidate.player_name
            )

            if not display_name:

                continue

            candidate_surname = cls._surname(
                display_name
            )

            if candidate_surname != raw_surname:

                continue

            candidate_initials = cls._initials_from_name(
                display_name
            )

            if (
                candidate_initials
                and candidate_initials.startswith(
                    raw_initials[0]
                )
            ):

                matches.append(
                    display_name
                )

        unique_matches = sorted(
            set(matches)
        )

        if len(unique_matches) == 1:

            return unique_matches[0]

        for match in unique_matches:

            if cls._initials_from_name(
                match
            ) == raw_initials:

                return match

        return None

    @staticmethod
    def canonicalize(
        player_name: str,
        db=None
    ):

        if not player_name:

            return player_name

        if db is not None:

            from sqlalchemy import func

            from app.database.models.player_mapping import (
                PlayerMapping
            )

            mapping = (
                db.query(
                    PlayerMapping
                )
                .filter(
                    func.lower(
                        PlayerMapping.raw_name
                    )
                    == player_name.lower()
                )
                .first()
            )

            if mapping:

                return mapping.canonical_name

            player_display_name = (
                Canonicalizer
                ._resolve_from_players(
                    player_name=player_name,
                    db=db
                )
            )

            if player_display_name:

                return player_display_name

        return PLAYER_REGISTRY.get(

            player_name,

            player_name
        )

    @staticmethod
    def canonicalize_text(
        text: str,
        db=None
    ):

        if not text:

            return text

        canonical_text = text

        registry_items = sorted(
            PLAYER_REGISTRY.items(),
            key=lambda item: len(
                item[0]
            ),
            reverse=True
        )

        for raw_name, canonical_name in registry_items:

            canonical_text = canonical_text.replace(
                raw_name,
                canonical_name
            )

        if db is not None:

            from app.database.models.player_mapping import (
                PlayerMapping
            )

            mappings = (
                db.query(
                    PlayerMapping
                )
                .all()
            )

            mappings = sorted(
                mappings,
                key=lambda mapping: len(
                    mapping.raw_name or ""
                ),
                reverse=True
            )

            for mapping in mappings:

                if (
                    mapping.raw_name
                    and mapping.canonical_name
                ):

                    canonical_text = canonical_text.replace(
                        mapping.raw_name,
                        mapping.canonical_name
                    )

        return canonical_text
