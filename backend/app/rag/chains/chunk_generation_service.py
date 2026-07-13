from app.database.models.player_intelligence import (
    PlayerIntelligence
)

from app.nlp.chunking.chunking_service import (
    ChunkingService
)
from app.nlp.canonicalization.canonicalizer import (
    Canonicalizer
)


class ChunkGenerationService:

    @staticmethod
    def generate_player_chunks(
        db
    ):

        players = (
            db.query(
                PlayerIntelligence
            ).all()
        )

        all_chunks = []

        for player in players:

            canonical_name = (
                Canonicalizer
                .canonicalize(
                    player.player_name,
                    db=db
                )
            )

            combined_text = f"""
            Player Name:
            {canonical_name}

            Canonical Name:
            {canonical_name}

            Role:
            {player.role}

            Batting Summary:
            {player.batting_summary}

            Bowling Summary:
            {player.bowling_summary}

            Intelligence Summary:
            {player.intelligence_summary}
            """

            chunks = (
                ChunkingService
                .create_chunks(
                    combined_text
                )
            )

            for chunk in chunks:

                all_chunks.append({

                    "raw_player_name":
                    player.player_name,

                    "player_name":
                    canonical_name,

                    "canonical_name":
                    canonical_name,

                    "role":
                    player.role,

                    "chunk_text":
                    chunk
                })

        return {
            "total_chunks":
            len(all_chunks),

            "sample_chunk":
            all_chunks[0]
            if all_chunks
            else None
        }
