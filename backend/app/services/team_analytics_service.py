from sqlalchemy import func
from sqlalchemy import case

from app.database.models.ball_by_ball import (
    BallByBall
)

from app.database.models.team_stats import (
    TeamStats
)


class TeamAnalyticsService:

    @staticmethod
    def generate_team_analytics(
        db
    ):

        db.query(
            TeamStats
        ).delete()

        db.commit()

        team_data = (

            db.query(

                BallByBall.batting_team.label(
                    "team"
                ),

                func.sum(
                    BallByBall.runs_scored
                    +
                    BallByBall.extras
                ).label(
                    "total_runs"
                ),

                func.count(
                    BallByBall.id
                ).label(
                    "total_balls"
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
                BallByBall.batting_team
            )

            .all()
        )

        objects = []

        for row in team_data:

            total_runs = float(
                row.total_runs or 0
            )

            total_balls = int(
                row.total_balls or 0
            )

            boundaries = int(
                row.boundaries or 0
            )

            dot_balls = int(
                row.dot_balls or 0
            )

            if total_balls == 0:
                continue

            overs = total_balls / 6

            run_rate = 0

            if overs > 0:
                run_rate = (
                    total_runs / overs
                )

            aggression_index = (
                (
                    boundaries
                    /
                    total_balls
                ) * 100
            )

            pressure_index = (
                (
                    dot_balls
                    /
                    total_balls
                ) * 100
            )

            obj = TeamStats(

                team_name=row.team,

                total_runs=int(
                    total_runs
                ),

                total_balls=total_balls,

                run_rate=round(
                    run_rate,
                    2
                ),

                total_boundaries=boundaries,

                dot_balls=dot_balls,

                aggression_index=round(
                    aggression_index,
                    2
                ),

                pressure_index=round(
                    pressure_index,
                    2
                )
            )

            objects.append(obj)

        db.bulk_save_objects(objects)

        db.commit()

        return {
            "teams_processed": len(
                objects
            )
        }