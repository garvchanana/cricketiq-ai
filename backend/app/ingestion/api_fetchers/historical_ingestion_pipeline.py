from app.ingestion.parsers.cricsheet_parser import (
    CricsheetParser
)

from app.ingestion.parsers.ball_transformer import (
    BallTransformer
)

from app.services.ball_service import (
    BallService
)
import uuid


class HistoricalIngestionPipeline:

    @staticmethod
    def ingest_match_file(
        db,
        file_path: str
    ):

        data = (
            CricsheetParser.load_match_file(
                file_path
            )
        )

        match_id = str(uuid.uuid4())

        innings_data = data.get("innings", [])

        transformed_balls = []

        venue = (
            data.get("info", {})
            .get("venue")
        )
        for idx, innings in enumerate(
            innings_data,
            start=1
        ):

            innings_info = innings.get("team")

            deliveries = innings.get(
                "overs",
                []
            )

            for over in deliveries:
                
                current_over = over.get("over")
                
                for delivery in over.get(
                    "deliveries",
                    []
                ):

                    transformed_ball = (
                        BallTransformer.transform(
                            match_id=match_id,
                            innings_number=idx,
                            batting_team=innings_info,
                             venue=venue,
                            over_number=current_over,
                            delivery=delivery
                        )
                    )

                    transformed_balls.append(
                        transformed_ball
                    )
        print(f"Inserting {len(transformed_balls)} balls")
        inserted = (
            BallService.bulk_insert_balls(
                db=db,
                balls_data=transformed_balls
            )
        )

        return {
            "balls_inserted": inserted
        }