from app.database.models.batter_bowler_matchups import BatterBowlerMatchup
from app.database.models.match_momentum_stats import MatchMomentumStats
from app.llm.groq_client import GroqClient
from app.nlp.canonicalization.canonicalizer import Canonicalizer
from app.nlp.canonicalization.player_registry import CANONICAL_TO_ALIAS
 
 
class MatchupAnalyst:
    """
    Phase 8.3 — Matchup Analyst Agent
 
    Specialized agent that owns batter-bowler matchup intelligence
    and match momentum analysis.
 
    Responsibilities:
    - Fetch batter vs bowler head-to-head dominance data
    - Find best/worst matchups for any player
    - Analyse match momentum and pressure patterns
    - Generate AI narrative for matchup insights
 
    Called by:
    - FinalAnswerAgent (Phase 8.4) for matchup questions
    - /ask endpoint for head-to-head questions
    """
 
    # Minimum balls for a valid matchup
    MIN_BALLS = 10
 
    # ---------------------------------------------------------------------------
    # Batter vs Bowler — head to head
    # ---------------------------------------------------------------------------
 
    @classmethod
    def get_head_to_head(
        cls,
        batter: str,
        bowler: str,
        db
    ) -> dict:
        """
        Fetch head-to-head matchup between a specific batter and bowler.
        Uses dominance_index to determine who has the upper hand.
        """
 
        batter_canonical = Canonicalizer.canonicalize(
            player_name=batter, db=db
        )
        bowler_canonical = Canonicalizer.canonicalize(
            player_name=bowler, db=db
        )
 
        batter_variants = cls._get_variants(batter, batter_canonical)
        bowler_variants = cls._get_variants(bowler, bowler_canonical)
 
        record = None
        for b in batter_variants:
            for p in bowler_variants:
                record = db.query(BatterBowlerMatchup).filter(
                    BatterBowlerMatchup.batsman == b,
                    BatterBowlerMatchup.bowler  == p
                ).first()
                if record:
                    break
            if record:
                break
 
        if not record:
            return {
                "batter":    batter_canonical,
                "bowler":    bowler_canonical,
                "found":     False,
                "narrative": (
                    f"No head-to-head data found between "
                    f"{batter_canonical} and {bowler_canonical}. "
                    f"They may not have faced each other enough "
                    f"(minimum {cls.MIN_BALLS} balls required)."
                )
            }
 
        dominance = cls._interpret_dominance(
            dominance_index=float(record.dominance_index or 0),
            batter=batter_canonical,
            bowler=bowler_canonical
        )
 
        return {
            "batter":               batter_canonical,
            "bowler":               bowler_canonical,
            "total_runs":           int(record.total_runs or 0),
            "balls_faced":          int(record.balls_faced or 0),
            "dismissals":           int(record.dismissals or 0),
            "strike_rate":          round(float(record.strike_rate or 0), 2),
            "dot_ball_percentage":  round(float(record.dot_ball_percentage or 0), 2),
            "dominance_index":      round(float(record.dominance_index or 0), 2),
            "dominance_label":      dominance["label"],
            "found":                True,
            "narrative":            dominance["narrative"]
        }
 
    # ---------------------------------------------------------------------------
    # Best matchups for a batter — who they dominate
    # ---------------------------------------------------------------------------
 
    @classmethod
    def get_batter_best_matchups(
        cls,
        batter: str,
        limit: int = 5,
        db = None
    ) -> dict:
        """
        Find bowlers a batter dominates most (highest dominance_index).
        """
 
        canonical     = Canonicalizer.canonicalize(player_name=batter, db=db)
        name_variants = cls._get_variants(batter, canonical)
 
        records = None
        for name in name_variants:
            records = (
                db.query(BatterBowlerMatchup)
                .filter(BatterBowlerMatchup.batsman == name)
                .order_by(BatterBowlerMatchup.dominance_index.desc())
                .limit(limit)
                .all()
            )
            if records:
                break
 
        if not records:
            return {
                "batter":    canonical,
                "found":     False,
                "matchups":  [],
                "narrative": f"No matchup data found for {canonical}."
            }
 
        matchups = [
            {
                "bowler":              Canonicalizer.canonicalize(
                                           player_name=r.bowler, db=db
                                       ),
                "total_runs":          int(r.total_runs or 0),
                "balls_faced":         int(r.balls_faced or 0),
                "dismissals":          int(r.dismissals or 0),
                "strike_rate":         round(float(r.strike_rate or 0), 2),
                "dot_ball_percentage": round(float(r.dot_ball_percentage or 0), 2),
                "dominance_index":     round(float(r.dominance_index or 0), 2)
            }
            for r in records
        ]
 
        narrative = cls._generate_batter_matchup_narrative(
            batter=canonical,
            matchups=matchups,
            matchup_type="dominates"
        )
 
        return {
            "batter":    canonical,
            "type":      "best_matchups",
            "matchups":  matchups,
            "found":     True,
            "narrative": narrative
        }
 
    # ---------------------------------------------------------------------------
    # Worst matchups for a batter — who troubles them most
    # ---------------------------------------------------------------------------
 
    @classmethod
    def get_batter_worst_matchups(
        cls,
        batter: str,
        limit: int = 5,
        db = None
    ) -> dict:
        """
        Find bowlers who trouble a batter most (lowest dominance_index).
        """
 
        canonical     = Canonicalizer.canonicalize(player_name=batter, db=db)
        name_variants = cls._get_variants(batter, canonical)
 
        records = None
        for name in name_variants:
            records = (
                db.query(BatterBowlerMatchup)
                .filter(BatterBowlerMatchup.batsman == name)
                .order_by(BatterBowlerMatchup.dominance_index.asc())
                .limit(limit)
                .all()
            )
            if records:
                break
 
        if not records:
            return {
                "batter":    canonical,
                "found":     False,
                "matchups":  [],
                "narrative": f"No matchup data found for {canonical}."
            }
 
        matchups = [
            {
                "bowler":              Canonicalizer.canonicalize(
                                           player_name=r.bowler, db=db
                                       ),
                "total_runs":          int(r.total_runs or 0),
                "balls_faced":         int(r.balls_faced or 0),
                "dismissals":          int(r.dismissals or 0),
                "strike_rate":         round(float(r.strike_rate or 0), 2),
                "dot_ball_percentage": round(float(r.dot_ball_percentage or 0), 2),
                "dominance_index":     round(float(r.dominance_index or 0), 2)
            }
            for r in records
        ]
 
        narrative = cls._generate_batter_matchup_narrative(
            batter=canonical,
            matchups=matchups,
            matchup_type="struggles against"
        )
 
        return {
            "batter":    canonical,
            "type":      "worst_matchups",
            "matchups":  matchups,
            "found":     True,
            "narrative": narrative
        }
 
    # ---------------------------------------------------------------------------
    # Best matchups for a bowler — who they dismiss most
    # ---------------------------------------------------------------------------
 
    @classmethod
    def get_bowler_best_matchups(
        cls,
        bowler: str,
        limit: int = 5,
        db = None
    ) -> dict:
        """
        Find batters a bowler dominates most (lowest dominance_index = bowler wins).
        """
 
        canonical     = Canonicalizer.canonicalize(player_name=bowler, db=db)
        name_variants = cls._get_variants(bowler, canonical)
 
        records = None
        for name in name_variants:
            records = (
                db.query(BatterBowlerMatchup)
                .filter(BatterBowlerMatchup.bowler == name)
                .order_by(BatterBowlerMatchup.dominance_index.asc())
                .limit(limit)
                .all()
            )
            if records:
                break
 
        if not records:
            return {
                "bowler":    canonical,
                "found":     False,
                "matchups":  [],
                "narrative": f"No matchup data found for {canonical}."
            }
 
        matchups = [
            {
                "batter":              Canonicalizer.canonicalize(
                                           player_name=r.batsman, db=db
                                       ),
                "total_runs":          int(r.total_runs or 0),
                "balls_faced":         int(r.balls_faced or 0),
                "dismissals":          int(r.dismissals or 0),
                "strike_rate":         round(float(r.strike_rate or 0), 2),
                "dot_ball_percentage": round(float(r.dot_ball_percentage or 0), 2),
                "dominance_index":     round(float(r.dominance_index or 0), 2)
            }
            for r in records
        ]
 
        narrative = cls._generate_bowler_matchup_narrative(
            bowler=canonical,
            matchups=matchups
        )
 
        return {
            "bowler":    canonical,
            "type":      "bowler_best_matchups",
            "matchups":  matchups,
            "found":     True,
            "narrative": narrative
        }
 
    # ---------------------------------------------------------------------------
    # Momentum analysis — peak pressure overs
    # ---------------------------------------------------------------------------
 
    @classmethod
    def get_momentum_summary(
        cls,
        db
    ) -> dict:
        """
        Fetch average momentum and pressure scores across all overs.
        Returns which overs have highest momentum and pressure.
        """
 
        from sqlalchemy import func as sqlfunc
 
        over_stats = (
            db.query(
                MatchMomentumStats.over_number,
                sqlfunc.avg(MatchMomentumStats.momentum_score).label("avg_momentum"),
                sqlfunc.avg(MatchMomentumStats.pressure_score).label("avg_pressure"),
                sqlfunc.avg(MatchMomentumStats.total_runs).label("avg_runs"),
                sqlfunc.avg(MatchMomentumStats.wickets).label("avg_wickets")
            )
            .group_by(MatchMomentumStats.over_number)
            .order_by(MatchMomentumStats.over_number)
            .all()
        )
 
        if not over_stats:
            return {
                "found":     False,
                "narrative": "No momentum data available."
            }
 
        overs = [
            {
                "over":         int(row.over_number),
                "avg_momentum": round(float(row.avg_momentum or 0), 2),
                "avg_pressure": round(float(row.avg_pressure or 0), 2),
                "avg_runs":     round(float(row.avg_runs or 0), 2),
                "avg_wickets":  round(float(row.avg_wickets or 0), 3)
            }
            for row in over_stats
        ]
 
        # Find peak overs
        peak_momentum = max(overs, key=lambda x: x["avg_momentum"])
        peak_pressure = max(overs, key=lambda x: x["avg_pressure"])
 
        return {
            "overs":          overs,
            "peak_momentum":  peak_momentum,
            "peak_pressure":  peak_pressure,
            "total_overs":    len(overs),
            "found":          True,
            "narrative": (
                f"Over {peak_momentum['over']} has the highest momentum "
                f"(score: {peak_momentum['avg_momentum']}) in IPL matches. "
                f"Over {peak_pressure['over']} has the highest pressure "
                f"(score: {peak_pressure['avg_pressure']})."
            )
        }
 
    # ---------------------------------------------------------------------------
    # Private — name variant builder
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def _get_variants(
        original: str,
        canonical: str
    ) -> list:
 
        db_alias = CANONICAL_TO_ALIAS.get(canonical)
        return list(dict.fromkeys(filter(None, [
            original,
            canonical,
            db_alias
        ])))
 
    # ---------------------------------------------------------------------------
    # Private — dominance interpretation
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def _interpret_dominance(
        dominance_index: float,
        batter: str,
        bowler: str
    ) -> dict:
 
        if dominance_index > 50:
            label = "Batter dominates"
            narrative = (
                f"{batter} dominates {bowler} "
                f"(dominance index: {round(dominance_index, 2)}). "
                f"{batter} scores freely against this bowler."
            )
        elif dominance_index > 0:
            label = "Slight batter advantage"
            narrative = (
                f"{batter} has a slight edge over {bowler} "
                f"(dominance index: {round(dominance_index, 2)})."
            )
        elif dominance_index > -30:
            label = "Slight bowler advantage"
            narrative = (
                f"{bowler} has a slight edge over {batter} "
                f"(dominance index: {round(dominance_index, 2)})."
            )
        else:
            label = "Bowler dominates"
            narrative = (
                f"{bowler} dominates {batter} "
                f"(dominance index: {round(dominance_index, 2)}). "
                f"{bowler} consistently troubles this batter."
            )
 
        return {"label": label, "narrative": narrative}
 
    # ---------------------------------------------------------------------------
    # Private — narrative generators
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def _generate_batter_matchup_narrative(
        batter: str,
        matchups: list,
        matchup_type: str
    ) -> str:
 
        if not matchups:
            return f"No matchup data found for {batter}."
 
        top = matchups[0]
        lines = "\n".join(
            f"  vs {m['bowler']}: "
            f"{m['total_runs']} runs, "
            f"SR {m['strike_rate']}, "
            f"{m['dismissals']} dismissals, "
            f"dominance {m['dominance_index']}"
            for m in matchups
        )
 
        prompt = f"""You are CricketIQ, an IPL matchup analyst.
Write a concise matchup insight for {batter} who {matchup_type} these bowlers.
Under 100 words. Data-driven and specific.
 
MATCHUP DATA:
{lines}
 
INSIGHT:"""
 
        try:
            return GroqClient.complete(
                system_prompt="You are a cricket analyst. Write concise matchup insights.",
                user_prompt=prompt,
                temperature=0.3,
                max_tokens=130
            )
        except Exception:
            return (
                f"{batter} {matchup_type} "
                f"{top['bowler']} most "
                f"(dominance: {top['dominance_index']})."
            )
 
    @staticmethod
    def _generate_bowler_matchup_narrative(
        bowler: str,
        matchups: list
    ) -> str:
 
        if not matchups:
            return f"No matchup data found for {bowler}."
 
        top = matchups[0]
        lines = "\n".join(
            f"  vs {m['batter']}: "
            f"{m['dismissals']} dismissals, "
            f"SR allowed {m['strike_rate']}, "
            f"dominance {m['dominance_index']}"
            for m in matchups
        )
 
        prompt = f"""You are CricketIQ, an IPL matchup analyst.
Write a concise insight about {bowler}'s most dominated batters in IPL.
Under 100 words. Data-driven and specific.
 
MATCHUP DATA:
{lines}
 
INSIGHT:"""
 
        try:
            return GroqClient.complete(
                system_prompt="You are a cricket analyst. Write concise matchup insights.",
                user_prompt=prompt,
                temperature=0.3,
                max_tokens=130
            )
        except Exception:
            return (
                f"{bowler} dominates "
                f"{top['batter']} most "
                f"(dominance: {top['dominance_index']})."
            )