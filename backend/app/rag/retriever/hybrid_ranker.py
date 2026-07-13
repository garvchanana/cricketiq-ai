class HybridRanker:

    @staticmethod
    def calculate_hybrid_score(
        result
    ):

        reliability_score = float(
            result.get(
                "reliability_score",
                0
            )
        )

        role = (
            result.get(
                "role",
                ""
            )
        )

        overall_rating = float(
            result.get(
                "overall_rating",
                0
            )
        )

        role_bonus = 0

        if role == "Batter":

            role_bonus = 50

        elif role == "All-Rounder":

            role_bonus = 25

        hybrid_score = (

            reliability_score
            +
            role_bonus
            +
            (
                overall_rating * 0.1
            )
        )

        return round(
            hybrid_score,
            2
        )