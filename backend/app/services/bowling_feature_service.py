from sqlalchemy import func
from sqlalchemy import case

from app.database.models.ball_by_ball import (
    BallByBall
)

from app.database.models.player_bowling_stats import (
    PlayerBowlingStats
)


class BowlingFeatureService:

    @staticmethod
    def generate_bowling_features(
        db
    ):

        db.query(
            PlayerBowlingStats
        ).delete()

        db.commit()

        bowling_data = (

            db.query(

                BallByBall.bowler.label(
                    "bowler"
                ),

                func.count(
                    BallByBall.id
                ).label(
                    "balls_bowled"
                ),

                func.sum(
                    BallByBall.runs_scored
                    +
                    BallByBall.extras
                ).label(
                    "runs_conceded"
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
                BallByBall.bowler
            )

            .all()
        )

        objects = []

        for row in bowling_data:

            overs = (
                row.balls_bowled / 6
            )

            economy = 0

            if overs > 0:
                economy = (
                    float(row.runs_conceded) / overs
                )

            strike_rate = 0

            if row.wickets > 0:
                strike_rate = (
                    float(row.balls_bowled)
                    /
                    float(row.wickets)
                )

            bowling_average = 0

            if row.wickets > 0:
                bowling_average = (
                    float(row.runs_conceded)
                    /
                    float(row.wickets)
                )
            obj = PlayerBowlingStats(

                bowler=row.bowler,

                balls_bowled=row.balls_bowled,

                runs_conceded=row.runs_conceded,

                wickets=row.wickets,

                economy_rate=round(
                    economy,
                    2
                ),

                bowling_strike_rate=round(
                    strike_rate,
                    2
                ),

                dot_balls=row.dot_balls,

                bowling_average=round(
                    bowling_average,
                    2
                )
            )

            objects.append(obj)

        db.bulk_save_objects(objects)

        db.commit()

        return {
            "bowlers_processed": len(
                objects
            )
        }