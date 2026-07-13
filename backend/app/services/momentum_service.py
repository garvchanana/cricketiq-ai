from sqlalchemy import func
from sqlalchemy import case

from app.database.models.ball_by_ball import (
    BallByBall
)

from app.database.models.match_momentum_stats import (
    MatchMomentumStats
)


class MomentumService:

    @staticmethod
    def generate_momentum_features(
        db
    ):

        db.query(
            MatchMomentumStats
        ).delete()

        db.commit()

        over_data = (

            db.query(

                BallByBall.match_id,

                BallByBall.innings,

                BallByBall.over_number,

                func.sum(
                    BallByBall.runs_scored
                    +
                    BallByBall.extras
                ).label(
                    "total_runs"
                ),

                func.sum(
                    case(
                        (
                            BallByBall.wicket == 1,
                            1
                        ),
                        else_=0
                    )
                ).label(
                    "wickets"
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
                BallByBall.match_id,
                BallByBall.innings,
                BallByBall.over_number
            )

            .all()
        )

        objects = []

        for row in over_data:

            momentum_score = (
                (
                    float(row.total_runs) * 0.6
                )
                +
                (
                    float(row.boundaries) * 2
                )
                -
                (
                    float(row.dot_balls) * 0.5
                )
            )

            pressure_score = (
                (
                    float(row.dot_balls) * 1.5
                )
                +
                (
                    float(row.wickets) * 3
                )
            )

            obj = MatchMomentumStats(

                match_id=row.match_id,

                innings=row.innings,

                over_number=row.over_number,

                total_runs=row.total_runs,

                wickets=row.wickets,

                boundaries=row.boundaries,

                dot_balls=row.dot_balls,

                momentum_score=round(
                    momentum_score,
                    2
                ),

                pressure_score=round(
                    pressure_score,
                    2
                )
            )

            objects.append(obj)

        db.bulk_save_objects(objects)

        db.commit()

        return {
            "overs_processed": len(
                objects
            )
        }