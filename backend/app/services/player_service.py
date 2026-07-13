import uuid

from sqlalchemy.orm import Session

from app.database.models.player import Player


class PlayerService:

    @staticmethod
    def bulk_create_players(
        db: Session,
        players_data: list
    ):

        players = []

        for player_data in players_data:

            player = Player(
                player_uuid=str(uuid.uuid4()),
                api_player_id=player_data.get("id"),
                player_name=player_data.get("name"),
                standardized_name=player_data.get("name"),
                country=player_data.get("country"),
                role=player_data.get("role"),
                batting_style=player_data.get("battingStyle"),
                bowling_style=player_data.get("bowlingStyle")
            )

            players.append(player)

        db.bulk_save_objects(players)

        db.commit()

        return players