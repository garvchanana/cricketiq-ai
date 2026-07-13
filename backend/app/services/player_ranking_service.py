from app.database.models.player_batting_stats import PlayerBattingStats
from app.database.models.player_bowling_stats import PlayerBowlingStats
from app.database.models.player_rankings import PlayerRankings


class PlayerRankingService:

    # ---------------------------------------------------------------------------
    # Phase 11.1 fix — performance thresholds for role classification
    #
    # Old behavior: role = "All-Rounder" for ANY player with bowling data,
    # even 1 wicket — this caused Virat Kohli (5 wickets) to be shown
    # as All-Rounder which is misleading.
    #
    # New behavior:
    #   Batter      → runs >= 100, wickets < 20
    #   Bowler      → wickets >= 20, runs < 500
    #   All-Rounder → runs >= 500 AND wickets >= 20 (genuine contribution both)
    # ---------------------------------------------------------------------------

    MIN_WICKETS_BOWLER      = 20   # minimum wickets to be considered a bowler
    MIN_WICKETS_ALL_ROUNDER = 20   # minimum wickets for all-rounder status
    MIN_RUNS_ALL_ROUNDER    = 500  # minimum runs for all-rounder status
    MIN_RUNS_BATTER         = 100  # minimum runs to appear in rankings

    @staticmethod
    def _classify_role(
        runs:    int,
        wickets: int
    ) -> str:
        """
        Classify a player's role based on actual performance thresholds.
        """
        is_genuine_bowler  = wickets >= PlayerRankingService.MIN_WICKETS_BOWLER
        is_genuine_batter  = runs >= PlayerRankingService.MIN_RUNS_ALL_ROUNDER

        if is_genuine_batter and is_genuine_bowler:
            return "All-Rounder"
        elif is_genuine_bowler:
            return "Bowler"
        else:
            return "Batter"

    @staticmethod
    def generate_player_rankings(db):

        db.query(PlayerRankings).delete()
        db.commit()

        batting_stats = db.query(PlayerBattingStats).all()
        bowling_stats = db.query(PlayerBowlingStats).all()

        # Build bowling lookup by player name
        bowling_lookup = {
            b.bowler: b for b in bowling_stats
        }

        objects = []

        for batter in batting_stats:

            total_runs  = int(batter.total_runs or 0)
            strike_rate = float(batter.strike_rate or 0)

            # Skip players with too few runs — not meaningful for rankings
            if total_runs < PlayerRankingService.MIN_RUNS_BATTER:
                continue

            wickets = 0
            economy = 0.0
            bowling_score = 0.0

            bowling_data = bowling_lookup.get(batter.batsman)

            if bowling_data:
                wickets = int(bowling_data.wickets or 0)
                economy = float(bowling_data.economy_rate or 0)

                bowling_score = (
                    (wickets * 8)
                    - (economy * 2)
                )

            batting_score = (
                (total_runs * 0.4)
                + (strike_rate * 0.3)
            )

            final_score = batting_score + bowling_score

            # Phase 11.1 fix — derive role from thresholds not any-wicket rule
            role = PlayerRankingService._classify_role(
                runs=total_runs,
                wickets=wickets
            )

            obj = PlayerRankings(
                player_name   = batter.batsman,
                role          = role,
                ranking_score = round(final_score, 2),
                total_runs    = total_runs,
                strike_rate   = round(strike_rate, 2),
                total_wickets = wickets,
                economy_rate  = round(economy, 2)
            )

            objects.append(obj)

        db.bulk_save_objects(objects)
        db.commit()

        return {"players_ranked": len(objects)}