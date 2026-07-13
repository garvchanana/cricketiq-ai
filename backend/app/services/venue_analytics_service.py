from sqlalchemy import func
from sqlalchemy import case

from app.database.models.ball_by_ball import (
    BallByBall
)


from app.database.models.venue_stats import (
    VenueStats
)


class VenueAnalyticsService:

    @staticmethod
    def generate_venue_analytics(
        db
    ):

        db.query(
            VenueStats
        ).delete()

        db.commit()

        venue_data = (

            db.query(

                BallByBall.venue.label(
                    "venue"
                ),

                func.count(
                    func.distinct(
                        BallByBall.match_id
                    )
                ).label(
                    "matches"
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
                BallByBall.venue
            )

            .all()
        )

        objects = []

        for row in venue_data:

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

            matches = int(
                row.matches or 0
            )

            if total_balls == 0:
                continue

            overs = total_balls / 6

            average_run_rate = 0

            if overs > 0:

                average_run_rate = (
                    total_runs / overs
                )

            dot_ball_percentage = (
                (
                    dot_balls
                    /
                    total_balls
                ) * 100
            )

            venue_type = (
                "Balanced"
            )

            if average_run_rate >= 9:
                venue_type = (
                    "Batting Friendly"
                )

            elif average_run_rate <= 7:
                venue_type = (
                    "Bowling Friendly"
                )

            obj = VenueStats(

                venue=row.venue,

                total_matches=matches,

                total_runs=int(
                    total_runs
                ),

                total_balls=total_balls,

                average_run_rate=round(
                    average_run_rate,
                    2
                ),

                total_boundaries=boundaries,

                dot_ball_percentage=round(
                    dot_ball_percentage,
                    2
                ),

                venue_type=venue_type
            )

            objects.append(obj)

        db.bulk_save_objects(objects)

        db.commit()

        return {
            "venues_processed": len(
                objects
            )
        }