"""
Phase 11.5 — VectorIndexingService with disk-first loading

Key change: build_player_index() now checks for a persisted index
on disk before rebuilding. This eliminates the slow rebuild-on-every-
startup behavior that was blocking server start.

Startup behavior:
  - Index exists on disk → load in ~0.1s (was ~30-60s rebuild)
  - No index on disk    → build fresh, then save to disk for next time
  - Rebuild forced      → call build_player_index(force_rebuild=True)
"""

import logging

from app.database.models.player_intelligence import PlayerIntelligence
from app.nlp.embeddings.embedding_service import EmbeddingService
from app.rag.vectorstore.faiss_store import FAISSStore

logger = logging.getLogger(__name__)

# Module-level singleton — shared across all requests
faiss_store = FAISSStore()


class VectorIndexingService:

    # ---------------------------------------------------------------------------
    # Phase 11.5 — disk-first index loading
    # ---------------------------------------------------------------------------

    @staticmethod
    def build_player_index(
        db,
        force_rebuild: bool = False
    ) -> dict:
        """
        Build or load the FAISS player intelligence index.

        Phase 11.5 behavior:
        1. If index exists on disk AND force_rebuild=False → load from disk
        2. If no index on disk OR force_rebuild=True → build fresh + save

        Parameters
        ----------
        db            : SQLAlchemy session
        force_rebuild : if True, always rebuild even if disk index exists

        Returns
        -------
        {"status": str, "players_indexed": int, "source": str}
        """

        global faiss_store

        # ── Load from disk if available ───────────────────────────────────
        if not force_rebuild and FAISSStore.is_persisted():
            success = faiss_store.load_index()
            if success:
                logger.info(
                    "FAISS index loaded from disk — %d players indexed",
                    faiss_store.get_total_vectors()
                )
                return {
                    "status":          "loaded_from_disk",
                    "players_indexed": faiss_store.get_total_vectors(),
                    "source":          "disk"
                }
            else:
                logger.warning(
                    "Disk index load failed — rebuilding from DB."
                )

        # ── Build fresh from DB ───────────────────────────────────────────
        logger.info("Building FAISS index from database...")

        records = db.query(PlayerIntelligence).all()

        if not records:
            logger.warning("No PlayerIntelligence records found in DB.")
            return {
                "status":          "empty",
                "players_indexed": 0,
                "source":          "db"
            }

        player_embeddings = []

        for record in records:

            # Build the text chunk to embed
            chunk_parts = []

            if record.player_name:
                chunk_parts.append(f"Player: {record.player_name}")
            if record.role:
                chunk_parts.append(f"Role: {record.role}")
            if record.intelligence_summary:
                chunk_parts.append(record.intelligence_summary)
            if record.batting_summary:
                chunk_parts.append(record.batting_summary)
            if record.bowling_summary:
                chunk_parts.append(record.bowling_summary)

            chunk = "\n".join(chunk_parts)

            if not chunk.strip():
                continue

            try:
                embedding = EmbeddingService.generate_embedding(chunk)
            except Exception as e:
                logger.warning(
                    "Failed to embed player %s: %s",
                    record.player_name, str(e)
                )
                continue

            # Phase 11.2 — resolve canonical name via registry
            from app.nlp.canonicalization.player_registry import PLAYER_REGISTRY
            canonical = PLAYER_REGISTRY.get(
                record.player_name, record.player_name
            )

            player_embeddings.append({
                "embedding":        embedding,
                "player_name":      record.player_name,
                "canonical_name":   canonical,
                "role":             record.role,
                "chunk":            chunk,
                "retrieval_source": "exact",
                "overall_rating":   float(record.overall_rating or 0)
            })

        if not player_embeddings:
            logger.warning("No valid embeddings generated.")
            return {
                "status":          "no_embeddings",
                "players_indexed": 0,
                "source":          "db"
            }

        # Build FAISS index
        success = faiss_store.build_index(player_embeddings)

        if not success:
            return {
                "status":          "build_failed",
                "players_indexed": 0,
                "source":          "db"
            }

        # ── Persist to disk for next startup ─────────────────────────────
        saved = faiss_store.save_index()

        logger.info(
            "FAISS index built — %d players indexed, saved=%s",
            faiss_store.get_total_vectors(),
            saved
        )

        return {
            "status":          "built_and_saved" if saved else "built",
            "players_indexed": faiss_store.get_total_vectors(),
            "source":          "db"
        }

    @staticmethod
    def get_store() -> FAISSStore:
        """Return the module-level FAISSStore singleton."""
        return faiss_store

    @staticmethod
    def rebuild(db) -> dict:
        """Force a full rebuild regardless of disk state."""
        return VectorIndexingService.build_player_index(
            db=db,
            force_rebuild=True
        )