class PlayerTransformer:

    @staticmethod
    def transform(player_data: dict):

        return {
            "id": player_data.get("id"),
            "name": player_data.get("name"),
            "country": player_data.get("country"),
            "role": player_data.get("role"),
            "battingStyle": player_data.get("battingStyle"),
            "bowlingStyle": player_data.get("bowlingStyle")
        }