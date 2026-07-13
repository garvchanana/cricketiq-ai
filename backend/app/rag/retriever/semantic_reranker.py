class SemanticReranker:

    @staticmethod
    def rerank(
        results,
        intent
    ):

        for result in results:

            score = float(
                result.get(
                    "hybrid_score",
                    0
                )
            )

            role = (
                result.get(
                    "role",
                    ""
                )
            )

            if (
                intent ==
                "aggressive_batter"
            ):

                if role == "Batter":

                    score += 100

            elif (
                intent ==
                "finisher"
            ):

                if role in [
                    "Batter",
                    "All-Rounder"
                ]:

                    score += 80

            elif (
                intent ==
                "bowler"
            ):

                if role == "Bowler":

                    score += 100

            result[
                "semantic_score"
            ] = round(
                score,
                2
            )

        results.sort(

            key=lambda x:
            x[
                "semantic_score"
            ],

            reverse=True
        )

        return results