"""
Phase D.6 fix — Percentile-based venue classification

OLD (buggy): fixed thresholds (>=9 Batting Friendly, <=7 Bowling
Friendly, else Balanced) caused most IPL venues (which cluster in
the 7.5-9.3 run rate range) to be overwhelmingly classified as
"Balanced", with almost no "Bowling Friendly" venues ever appearing.

NEW (fixed): classification is now RELATIVE to the actual
distribution of run rates across all venues, using percentile
thresholds. Top third of venues by run rate = Batting Friendly,
bottom third = Bowling Friendly, middle third = Balanced. This
gives a genuinely balanced 3-way split reflecting real relative
scoring conditions, not an arbitrary absolute cutoff.
"""

from sqlalchemy import func
from sqlalchemy import case

from app.database.models.ball_by_ball import BallByBall
from app.database.models.venue_stats import VenueStats


class VenueAnalyticsService:

    @staticmethod
    def generate_venue_analytics(db):

        db.query(VenueStats).delete()
        db.commit()

        venue_data = (
            db.query(
                BallByBall.venue.label("venue"),
                func.count(func.distinct(BallByBall.match_id)).label("matches"),
                func.sum(
                    BallByBall.runs_scored + BallByBall.extras
                ).label("total_runs"),
                func.count(BallByBall.id).label("total_balls"),
                func.sum(
                    case(
                        (
                            (BallByBall.runs_scored == 4)
                            | (BallByBall.runs_scored == 6),
                            1
                        ),
                        else_=0
                    )
                ).label("boundaries"),
                func.sum(
                    case((BallByBall.runs_scored == 0, 1), else_=0)
                ).label("dot_balls")
            )
            .group_by(BallByBall.venue)
            .all()
        )

        # ── Step 1: Compute run rate for every venue first ────────────────
        computed = []

        for row in venue_data:

            total_runs  = float(row.total_runs or 0)
            total_balls = int(row.total_balls or 0)
            boundaries  = int(row.boundaries or 0)
            dot_balls   = int(row.dot_balls or 0)
            matches     = int(row.matches or 0)

            if total_balls == 0:
                continue

            overs = total_balls / 6
            average_run_rate = (total_runs / overs) if overs > 0 else 0
            dot_ball_percentage = (dot_balls / total_balls) * 100

            computed.append({
                "venue":               row.venue,
                "matches":             matches,
                "total_runs":          int(total_runs),
                "total_balls":         total_balls,
                "average_run_rate":    round(average_run_rate, 2),
                "total_boundaries":    boundaries,
                "dot_ball_percentage": round(dot_ball_percentage, 2),
            })

        if not computed:
            return {"venues_processed": 0}

        # ── Step 2: Determine percentile thresholds from actual data ──────
        # Only consider venues with meaningful sample size (>=5 matches)
        # for threshold calculation, so one-off venues don't skew the cutoffs
        significant = [
            v for v in computed if v["matches"] >= 5
        ]
        rates = sorted(v["average_run_rate"] for v in significant) or \
                sorted(v["average_run_rate"] for v in computed)

        def percentile(data, pct):
            if not data:
                return 0
            k = (len(data) - 1) * pct
            f = int(k)
            c = min(f + 1, len(data) - 1)
            if f == c:
                return data[f]
            return data[f] + (data[c] - data[f]) * (k - f)

        upper_threshold = percentile(rates, 0.67)  # top third cutoff
        lower_threshold = percentile(rates, 0.33)  # bottom third cutoff

        # ── Step 3: Classify each venue relative to the distribution ──────
        objects = []

        for v in computed:

            rate = v["average_run_rate"]

            if rate >= upper_threshold:
                venue_type = "Batting Friendly"
            elif rate <= lower_threshold:
                venue_type = "Bowling Friendly"
            else:
                venue_type = "Balanced"

            obj = VenueStats(
                venue               = v["venue"],
                total_matches       = v["matches"],
                total_runs          = v["total_runs"],
                total_balls         = v["total_balls"],
                average_run_rate    = v["average_run_rate"],
                total_boundaries    = v["total_boundaries"],
                dot_ball_percentage = v["dot_ball_percentage"],
                venue_type          = venue_type
            )

            objects.append(obj)

        db.bulk_save_objects(objects)
        db.commit()

        return {
            "venues_processed": len(objects),
            "upper_threshold":  round(upper_threshold, 2),
            "lower_threshold":  round(lower_threshold, 2),
        }