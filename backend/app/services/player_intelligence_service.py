"""
Phase 12.4 fix — PlayerIntelligenceService writes canonical names

Previously, player_name in player_intelligence stored raw DB
shortcodes (e.g. "JJ Bumrah", "MS Dhoni") copied directly from
player_rankings.player_name. This meant every summary text and
every RAG-retrieved chunk showed shortcodes instead of full names,
requiring runtime canonicalization patches scattered across
retrieval_service.py and full_rag_chain.py.

Fix: resolve player_name through PLAYER_REGISTRY once, at
generation time, so canonical full names are baked directly into
batting_summary, bowling_summary, and intelligence_summary text —
and into the player_name column itself.
"""

from app.database.models.player_rankings import PlayerRankings
from app.database.models.player_intelligence import PlayerIntelligence
from app.nlp.canonicalization.player_registry import PLAYER_REGISTRY


class PlayerIntelligenceService:

    @staticmethod
    def generate_player_intelligence(db):

        db.query(PlayerIntelligence).delete()
        db.commit()

        rankings = db.query(PlayerRankings).all()

        objects = []

        for player in rankings:

            # Phase 12.4 fix — resolve canonical full name once, upfront.
            # Falls back to the raw DB name if not found in registry.
            canonical_name = PLAYER_REGISTRY.get(
                player.player_name,
                player.player_name
            )

            total_runs  = int(player.total_runs or 0)
            strike_rate = float(player.strike_rate or 0)
            wickets     = int(player.total_wickets or 0)
            economy     = float(player.economy_rate or 0)
            rating      = float(player.ranking_score or 0)

            batting_summary = (
                f"{canonical_name} "
                f"has scored "
                f"{total_runs} IPL runs "
                f"with a strike rate of "
                f"{round(strike_rate, 2)}."
            )

            bowling_summary = (
                f"{canonical_name} "
                f"has taken "
                f"{wickets} wickets "
                f"with an economy rate of "
                f"{round(economy, 2)}."
            )

            intelligence_summary = (
                f"{canonical_name} "
                f"is classified as a "
                f"{player.role}. "
                f"The player has an overall "
                f"rating of "
                f"{round(rating, 2)} "
                f"based on batting and "
                f"bowling analytics."
            )

            obj = PlayerIntelligence(
                player_name           = canonical_name,  # canonical, not shortcode
                role                   = player.role,
                batting_summary        = batting_summary,
                bowling_summary        = bowling_summary,
                overall_rating         = round(rating, 2),
                intelligence_summary   = intelligence_summary
            )

            objects.append(obj)

        db.bulk_save_objects(objects)
        db.commit()

        return {"players_processed": len(objects)}