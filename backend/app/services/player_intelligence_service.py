from app.database.models.player_rankings import (
    PlayerRankings
)

from app.database.models.player_intelligence import (
    PlayerIntelligence
)


class PlayerIntelligenceService:

    @staticmethod
    def generate_player_intelligence(
        db
    ):

        db.query(
            PlayerIntelligence
        ).delete()

        db.commit()

        rankings = (
            db.query(
                PlayerRankings
            ).all()
        )

        objects = []

        for player in rankings:

            total_runs = int(
                player.total_runs or 0
            )

            strike_rate = float(
                player.strike_rate or 0
            )

            wickets = int(
                player.total_wickets or 0
            )

            economy = float(
                player.economy_rate or 0
            )

            rating = float(
                player.ranking_score or 0
            )

            batting_summary = (
                f"{player.player_name} "
                f"has scored "
                f"{total_runs} IPL runs "
                f"with a strike rate of "
                f"{round(strike_rate, 2)}."
            )

            bowling_summary = (
                f"{player.player_name} "
                f"has taken "
                f"{wickets} wickets "
                f"with an economy rate of "
                f"{round(economy, 2)}."
            )

            intelligence_summary = (
                f"{player.player_name} "
                f"is classified as a "
                f"{player.role}. "
                f"The player has an overall "
                f"rating of "
                f"{round(rating, 2)} "
                f"based on batting and "
                f"bowling analytics."
            )

            obj = PlayerIntelligence(

                player_name=player.player_name,

                role=player.role,

                batting_summary=batting_summary,

                bowling_summary=bowling_summary,

                overall_rating=round(
                    rating,
                    2
                ),

                intelligence_summary=(
                    intelligence_summary
                )
            )

            objects.append(obj)

        db.bulk_save_objects(objects)

        db.commit()

        return {
            "players_processed": len(
                objects
            )
        }