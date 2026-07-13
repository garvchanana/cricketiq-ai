"""
Phase 11.5 — Index Builder Admin Script

Run this script to force a fresh FAISS index rebuild from the DB.
Use this when:
  - Player intelligence data has been updated
  - The persisted index is stale or corrupted
  - You want to rebuild after adding new players

Usage:
  cd backend
  python index_builder.py
"""

import sys
import logging

sys.path.insert(0, ".")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

logger = logging.getLogger(__name__)


def main():

    from app.database.session import SessionLocal
    from app.rag.vectorstore.vector_indexing_service import VectorIndexingService

    logger.info("Starting FAISS index rebuild...")

    db = SessionLocal()

    try:
        result = VectorIndexingService.rebuild(db=db)

        logger.info("Rebuild complete:")
        logger.info("  Status:          %s", result["status"])
        logger.info("  Players indexed: %d", result["players_indexed"])
        logger.info("  Source:          %s", result["source"])

        if result["players_indexed"] == 0:
            logger.warning(
                "No players indexed — check PlayerIntelligence table has data."
            )
            return 1

        return 0

    except Exception as e:
        logger.error("Rebuild failed: %s", str(e))
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    exit(main())