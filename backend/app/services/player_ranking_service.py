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
    MIN_RUNS_BATTER         = 100  # minimum runs to qualify via batting alone
    MIN_WICKETS_TO_QUALIFY  = 15   # minimum wickets to qualify via bowling alone

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

        # Build lookups by player name for both directions
        batting_lookup = {
            b.batsman: b for b in batting_stats
        }
        bowling_lookup = {
            b.bowler: b for b in bowling_stats
        }

        # Phase 12.4 fix — REGRESSION GUARD
        # Previously this only looped over batting_stats, which
        # structurally excluded specialist bowlers (e.g. Jasprit Bumrah,
        # Yuzvendra Chahal) who rarely bat. This caused them to be
        # missing from player_rankings entirely, which cascaded into
        # missing player_intelligence rows and missing FAISS embeddings —
        # so RAG had nothing to retrieve for these players in production.
        #
        # Fix: iterate over the UNION of all batter names and all
        # bowler names, so every player who appears in EITHER table
        # gets a ranking row.
        all_player_names = set(batting_lookup.keys()) | set(bowling_lookup.keys())

        objects = []

        for player_name in all_player_names:

            batting_data = batting_lookup.get(player_name)
            bowling_data = bowling_lookup.get(player_name)

            total_runs  = int(batting_data.total_runs or 0) if batting_data else 0
            strike_rate = float(batting_data.strike_rate or 0) if batting_data else 0.0

            wickets = int(bowling_data.wickets or 0) if bowling_data else 0
            economy = float(bowling_data.economy_rate or 0) if bowling_data else 0.0

            # Qualify via EITHER meaningful batting OR meaningful bowling —
            # not batting alone. This is the core fix.
            qualifies_via_batting = total_runs >= PlayerRankingService.MIN_RUNS_BATTER
            qualifies_via_bowling = wickets >= PlayerRankingService.MIN_WICKETS_TO_QUALIFY

            if not (qualifies_via_batting or qualifies_via_bowling):
                continue

            bowling_score = (
                (wickets * 8) - (economy * 2)
                if bowling_data else 0.0
            )

            batting_score = (
                (total_runs * 0.4) + (strike_rate * 0.3)
                if batting_data else 0.0
            )

            final_score = batting_score + bowling_score

            role = PlayerRankingService._classify_role(
                runs=total_runs,
                wickets=wickets
            )

            obj = PlayerRankings(
                player_name   = player_name,
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