from sqlalchemy import func
from sqlalchemy import case

from app.database.models.ball_by_ball import BallByBall
from app.database.models.player_batting_stats import PlayerBattingStats


class BattingFeatureService:

    @staticmethod
    def generate_batting_features(db):

        db.query(PlayerBattingStats).delete()
        db.commit()

        batting_data = (
            db.query(
                BallByBall.batsman.label("batsman"),

                func.sum(
                    BallByBall.runs_scored
                ).label("total_runs"),

                func.count(
                    BallByBall.id
                ).label("balls_faced"),

                (
                    (
                        func.sum(BallByBall.runs_scored) * 100.0
                    )
                    /
                    func.count(BallByBall.id)
                ).label("strike_rate"),

                func.sum(
                    case(
                        (BallByBall.runs_scored == 4, 1),
                        else_=0
                    )
                ).label("total_fours"),

                func.sum(
                    case(
                        (BallByBall.runs_scored == 6, 1),
                        else_=0
                    )
                ).label("total_sixes"),

                func.sum(
                    case(
                        (BallByBall.runs_scored == 0, 1),
                        else_=0
                    )
                ).label("dot_balls"),

                # Phase 11.1 fix — count actual dismissals for true average
                # A dismissal is when wicket == 1 on a ball faced by this batter
                func.sum(
                    case(
                        (BallByBall.wicket == 1, 1),
                        else_=0
                    )
                ).label("dismissals")
            )
            .group_by(BallByBall.batsman)
            .all()
        )

        objects = []

        for row in batting_data:

            total_runs  = int(row.total_runs or 0)
            dismissals  = int(row.dismissals or 0)

            # Phase 11.1 fix — real batting average = runs / dismissals
            # If player was never dismissed, average = total_runs (not out)
            batting_average = (
                round(total_runs / dismissals, 2)
                if dismissals > 0
                else float(total_runs)
            )

            obj = PlayerBattingStats(
                batsman         = row.batsman,
                total_runs      = total_runs,
                balls_faced     = int(row.balls_faced or 0),
                strike_rate     = round(float(row.strike_rate or 0), 2),
                total_fours     = int(row.total_fours or 0),
                total_sixes     = int(row.total_sixes or 0),
                dot_balls       = int(row.dot_balls or 0),
                batting_average = batting_average
            )

            objects.append(obj)

        db.bulk_save_objects(objects)
        db.commit()

        return {"players_processed": len(objects)}