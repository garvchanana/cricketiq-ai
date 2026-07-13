from sqlalchemy import func
from sqlalchemy import case

from app.database.models.ball_by_ball import (
    BallByBall
)

from app.database.models.advanced_batting_stats import (
    AdvancedBattingStats
)


class AdvancedBattingService:

    @staticmethod
    def generate_advanced_features(
        db
    ):

        db.query(
            AdvancedBattingStats
        ).delete()

        db.commit()

        batting_data = (

            db.query(

                BallByBall.batsman.label(
                    "batsman"
                ),

                func.count(
                    BallByBall.id
                ).label(
                    "balls_faced"
                ),

                func.sum(
                    case(
                        (
                            (
                                BallByBall.runs_scored == 4
                            )
                            |
                            (
                                BallByBall.runs_scored == 6
                            ),
                            1
                        ),
                        else_=0
                    )
                ).label(
                    "boundaries"
                ),

                func.sum(
                    case(
                        (
                            BallByBall.runs_scored == 0,
                            1
                        ),
                        else_=0
                    )
                ).label(
                    "dot_balls"
                )
            )

            .group_by(
                BallByBall.batsman
            )

            .all()
        )

        objects = []

        for row in batting_data:

            if row.balls_faced == 0:
                continue

            boundary_percentage = (
                row.boundaries
                /
                row.balls_faced
            ) * 100

            dot_ball_percentage = (
                row.dot_balls
                /
                row.balls_faced
            ) * 100

            aggression_index = (
                boundary_percentage
                -
                dot_ball_percentage
            )

            pressure_release_index = (
                boundary_percentage
                /
                (
                    dot_ball_percentage
                    + 1
                )
            )

            obj = AdvancedBattingStats(

                batsman=row.batsman,

                total_boundaries=row.boundaries,

                boundary_percentage=round(
                    boundary_percentage,
                    2
                ),

                dot_ball_percentage=round(
                    dot_ball_percentage,
                    2
                ),

                aggression_index=round(
                    aggression_index,
                    2
                ),

                pressure_release_index=round(
                    pressure_release_index,
                    2
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