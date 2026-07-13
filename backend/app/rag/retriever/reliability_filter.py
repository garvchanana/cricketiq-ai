class ReliabilityFilter:

    @staticmethod
    def calculate_reliability_score(
        metadata
    ):

        overall_rating = float(
            metadata.get(
                "overall_rating",
                0
            )
        )

        retrieval_rank = int(
            metadata.get(
                "retrieval_rank",
                999
            )
        )

        distance = float(
            metadata.get(
                "distance",
                1.0
            )
        )

        score = (

            overall_rating * 0.6

            +

            (
                1 / max(
                    retrieval_rank,
                    1
                )
            ) * 100

            +

            (
                1 /
                (
                    distance + 0.001
                )
            ) * 10
        )

        return round(
            score,
            2
        )