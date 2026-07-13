from sqlalchemy import func
from sqlalchemy import case

from app.database.models.ball_by_ball import (
    BallByBall
)

from app.database.models.match_phase_stats import (
    MatchPhaseStats
)


class MatchPhaseService:

    @staticmethod
    def classify_phase(
        over_number
    ):

        if over_number is None:
            return None

        over = int(float(over_number))

        if over <= 6:
            return "Powerplay"

        elif over <= 15:
            return "Middle Overs"

        return "Death Overs"


    @staticmethod
    def generate_phase_features(
        db
    ):

        db.query(
            MatchPhaseStats
        ).delete()

        db.commit()

        deliveries = (
            db.query(BallByBall)
            .all()
        )

        phase_data = {
            "Powerplay": {
                "runs": 0,
                "balls": 0,
                "wickets": 0,
                "dot_balls": 0,
                "boundaries": 0
            },

            "Middle Overs": {
                "runs": 0,
                "balls": 0,
                "wickets": 0,
                "dot_balls": 0,
                "boundaries": 0
            },

            "Death Overs": {
                "runs": 0,
                "balls": 0,
                "wickets": 0,
                "dot_balls": 0,
                "boundaries": 0
            }
        }

        for ball in deliveries:

            phase = (
                MatchPhaseService
                .classify_phase(
                    ball.over_number
                )
            )

            if phase is None:
                continue

            phase_data[phase]["runs"] += (
                ball.runs_scored
                +
                ball.extras
            )

            phase_data[phase]["balls"] += 1

            if ball.wicket:
                phase_data[phase][
                    "wickets"
                ] += 1

            if ball.runs_scored == 0:
                phase_data[phase][
                    "dot_balls"
                ] += 1

            if (
                ball.runs_scored == 4
                or
                ball.runs_scored == 6
            ):

                phase_data[phase][
                    "boundaries"
                ] += 1

        objects = []

        for phase, stats in phase_data.items():

            overs = stats["balls"] / 6

            run_rate = 0

            if overs > 0:

                run_rate = (
                    stats["runs"]
                    /
                    overs
                )

            obj = MatchPhaseStats(

                phase=phase,

                total_runs=stats["runs"],

                total_balls=stats["balls"],

                run_rate=round(
                    run_rate,
                    2
                ),

                wickets=stats["wickets"],

                dot_balls=stats[
                    "dot_balls"
                ],

                boundaries=stats[
                    "boundaries"
                ]
            )

            objects.append(obj)

        db.bulk_save_objects(objects)

        db.commit()

        return {
            "phases_processed": len(
                objects
            )
        }