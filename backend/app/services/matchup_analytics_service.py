from sqlalchemy import func
from sqlalchemy import case

from app.database.models.ball_by_ball import (
    BallByBall
)

from app.database.models.batter_bowler_matchups import (
    BatterBowlerMatchup
)


class MatchupAnalyticsService:

    @staticmethod
    def generate_matchup_analytics(
        db
    ):

        db.query(
            BatterBowlerMatchup
        ).delete()

        db.commit()

        matchup_data = (

            db.query(

                BallByBall.batsman.label(
                    "batsman"
                ),

                BallByBall.bowler.label(
                    "bowler"
                ),

                func.sum(
                    BallByBall.runs_scored
                ).label(
                    "total_runs"
                ),

                func.count(
                    BallByBall.id
                ).label(
                    "balls_faced"
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
                    "dismissals"
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
                BallByBall.batsman,
                BallByBall.bowler
            )

            .all()
        )

        objects = []

        for row in matchup_data:

            total_runs = float(
                row.total_runs or 0
            )

            balls_faced = int(
                row.balls_faced or 0
            )

            dismissals = int(
                row.dismissals or 0
            )

            dot_balls = int(
                row.dot_balls or 0
            )

            if balls_faced < 10:
                continue

            strike_rate = (
                (
                    total_runs
                    /
                    balls_faced
                ) * 100
            )

            dot_ball_percentage = (
                (
                    dot_balls
                    /
                    balls_faced
                ) * 100
            )

            dominance_index = (
                strike_rate
                -
                (
                    dismissals * 15
                )
                -
                (
                    dot_ball_percentage
                    * 0.3
                )
            )

            obj = BatterBowlerMatchup(

                batsman=row.batsman,

                bowler=row.bowler,

                total_runs=int(
                    total_runs
                ),

                balls_faced=balls_faced,

                dismissals=dismissals,

                strike_rate=round(
                    strike_rate,
                    2
                ),

                dot_ball_percentage=round(
                    dot_ball_percentage,
                    2
                ),

                dominance_index=round(
                    dominance_index,
                    2
                )
            )

            objects.append(obj)

        db.bulk_save_objects(objects)

        db.commit()

        return {
            "matchups_processed": len(
                objects
            )
        }