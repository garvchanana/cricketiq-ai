class ConfidenceScorer:

    @staticmethod
    def calculate_confidence(
        result
    ):

        semantic_score = float(
            result.get(
                "semantic_score",
                0
            )
        )

        distance = float(
            result.get(
                "distance",
                1
            )
        )

        confidence = (

            semantic_score
            *
            (
                1 / (
                    distance + 0.01
                )
            )
        )

        return round(
            confidence,
            2
        )
    
    @staticmethod
    def confidence_label(
        confidence
    ):

        if confidence >= 500:

            return "High"

        elif confidence >= 250:

            return "Medium"

        return "Low"