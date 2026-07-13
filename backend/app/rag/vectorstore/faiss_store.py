"""
Phase 11.5 — FAISSStore with index persistence

Key changes from original:
1. save_index() — persists index + player_data to data/faiss_index/
2. load_index() — loads from disk if available, skips rebuild
3. is_persisted() — checks if a saved index exists on disk
4. build_index() unchanged — still builds from scratch when needed
"""

import os
import json
import logging
import numpy  as np
import faiss

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

INDEX_DIR       = os.path.join("data", "faiss_index")
INDEX_FILE      = os.path.join(INDEX_DIR, "player_index.faiss")
METADATA_FILE   = os.path.join(INDEX_DIR, "player_metadata.json")


class FAISSStore:

    def __init__(self):
        self.index       = None
        self.player_data = []

    # ---------------------------------------------------------------------------
    # Persistence — Phase 11.5 additions
    # ---------------------------------------------------------------------------

    @staticmethod
    def is_persisted() -> bool:
        """Check if a saved index exists on disk and is non-empty."""
        return (
            os.path.exists(INDEX_FILE)
            and os.path.exists(METADATA_FILE)
            and os.path.getsize(INDEX_FILE) > 0
        )

    def save_index(self) -> bool:
        """
        Persist the current in-memory index to disk.
        Returns True on success, False on failure.
        """
        if self.index is None or not self.player_data:
            logger.warning("Cannot save — index is empty.")
            return False

        try:
            os.makedirs(INDEX_DIR, exist_ok=True)

            # Save FAISS index
            faiss.write_index(self.index, INDEX_FILE)

            # Save player metadata as JSON
            with open(METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.player_data, f, ensure_ascii=False, indent=2)

            logger.info(
                "FAISS index saved — %d players at %s",
                len(self.player_data),
                INDEX_DIR
            )
            return True

        except Exception as e:
            logger.error("Failed to save FAISS index: %s", str(e))
            return False

    def load_index(self) -> bool:
        """
        Load index from disk into memory.
        Returns True if loaded successfully, False if not available.
        """
        if not self.is_persisted():
            logger.info("No persisted FAISS index found — will build fresh.")
            return False

        try:
            self.index = faiss.read_index(INDEX_FILE)

            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                self.player_data = json.load(f)

            logger.info(
                "FAISS index loaded from disk — %d players",
                len(self.player_data)
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to load FAISS index from disk: %s — will rebuild.",
                str(e)
            )
            self.index       = None
            self.player_data = []
            return False

    # ---------------------------------------------------------------------------
    # Index building — unchanged from original
    # ---------------------------------------------------------------------------

    def build_index(self, player_embeddings: list) -> bool:
        """
        Build FAISS index from player embedding data.

        Parameters
        ----------
        player_embeddings : list of dicts, each with keys:
            - embedding : list[float]  (embedding vector)
            - player_name : str
            - canonical_name : str
            - role : str
            - chunk : str             (text snippet for context)
            - retrieval_source : str
        """
        if not player_embeddings:
            logger.warning("build_index called with empty player_embeddings.")
            return False

        try:
            vectors = np.array(
                [p["embedding"] for p in player_embeddings],
                dtype=np.float32
            )

            dimension = vectors.shape[1]

            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(vectors)

            self.player_data = [
                {k: v for k, v in p.items() if k != "embedding"}
                for p in player_embeddings
            ]

            logger.info(
                "FAISS index built — %d vectors, dimension %d",
                len(self.player_data),
                dimension
            )
            return True

        except Exception as e:
            logger.error("Failed to build FAISS index: %s", str(e))
            return False

    # ---------------------------------------------------------------------------
    # Search — unchanged from original
    # ---------------------------------------------------------------------------

    def search(
        self,
        query_embedding: list,
        top_k: int = 5
    ) -> list:
        """
        Search the FAISS index for the top-k nearest neighbours.

        Returns list of player_data dicts with added 'distance' key.
        """
        if self.index is None or not self.player_data:
            logger.warning("Search called on empty index.")
            return []

        try:
            query_vector = np.array(
                [query_embedding],
                dtype=np.float32
            )

            distances, indices = self.index.search(query_vector, top_k)

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:
                    continue
                result = dict(self.player_data[idx])
                result["distance"] = float(dist)
                results.append(result)

            return results

        except Exception as e:
            logger.error("FAISS search failed: %s", str(e))
            return []

    def get_total_vectors(self) -> int:
        """Return the number of vectors in the index."""
        if self.index is None:
            return 0
        return self.index.ntotal