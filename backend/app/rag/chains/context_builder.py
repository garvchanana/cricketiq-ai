from app.nlp.canonicalization.canonicalizer import (
    Canonicalizer
)


class ContextBuilder:

    @staticmethod
    def build_context(
        retrieved_docs,
        db=None
    ):

        context_parts = []

        for idx, doc in enumerate(
            retrieved_docs,
            start=1
        ):

            player_name = doc.get(
                "player_name",
                "Unknown"
            )

            canonical_name = doc.get(
                "canonical_name",
                player_name
            )

            role = doc.get(
                "role",
                "Unknown"
            )

            retrieval_source = doc.get(
                "retrieval_source",
                "semantic"
            )

            chunk = doc.get(
                "chunk",
                ""
            )

            raw_player_name = doc.get(
                "raw_player_name"
            )

            if (
                raw_player_name
                and raw_player_name != canonical_name
            ):

                chunk = chunk.replace(
                    raw_player_name,
                    canonical_name
                )

            chunk = (
                Canonicalizer
                .canonicalize_text(
                    chunk,
                    db=db
                )
            )

            context_parts.append(

                f"""
                Context {idx}:

                Player Name:
                {player_name}

                Canonical Name:
                {canonical_name}

                Role:
                {role}

                Retrieval Source:
                {retrieval_source}

                {chunk}
                """
            )

        final_context = "\n".join(
            context_parts
        )

        return final_context
