from app.nlp.preprocessing.query_rewriter import QueryRewriter
from app.nlp.entity_extraction.entity_extractor import EntityExtractor
 
 
# ---------------------------------------------------------------------------
# Routing decision constants
# ---------------------------------------------------------------------------
 
ROUTE_SQL    = "SQL"
ROUTE_RAG    = "RAG"
ROUTE_HYBRID = "HYBRID"
 
 
class IntentRouter:
    """
    Phase 7.3 — Intent Router
 
    The brain of the hybrid RAG + SQL system.
    Takes a raw user question, runs it through the rewriter and
    entity extractor, then decides which pipeline to use:
 
    SQL    — statistical / analytical / ranking questions
             answered purely from the database
 
    RAG    — descriptive / profile / narrative questions
             answered from vector store player intelligence
 
    HYBRID — complex questions needing both SQL stats
             AND RAG narrative context fused into one answer
 
    Output
    ------
    {
        "route":     "SQL" | "RAG" | "HYBRID",
        "question":  str,   original question
        "rewritten": str,   cleaned question
        "entities":  dict,  extracted entities
        "reasoning": str,   why this route was chosen
        "limit":     int,   result count (for SQL)
        "players":   list,  resolved player names
    }
    """
 
    # ---------------------------------------------------------------------------
    # Routing rules — evaluated in priority order
    # ---------------------------------------------------------------------------
 
    @classmethod
    def route(
        cls,
        question: str,
        db=None
    ) -> dict:
        """
        Route a question to the correct pipeline.
 
        Parameters
        ----------
        question : raw user question
        db       : SQLAlchemy session (optional, for canonicalization)
 
        Returns
        -------
        Routing decision dict
        """
 
        # ── Step 1: Rewrite question ─────────────────────────────────────────
        rewrite_result = QueryRewriter.rewrite(question=question)
        rewritten      = rewrite_result["rewritten"]
 
        # ── Step 2: Extract entities ─────────────────────────────────────────
        entities = EntityExtractor.extract(
            question=rewritten,
            db=db
        )
 
        # ── Step 3: Apply routing logic ──────────────────────────────────────
        route, reasoning = cls._decide_route(
            entities=entities,
            rewritten=rewritten
        )
 
        return {
            "route":     route,
            "question":  question,
            "rewritten": rewritten,
            "entities":  entities,
            "reasoning": reasoning,
            "limit":     entities.get("limit"),
            "players":   entities.get("players", []),
        }
 
    # ---------------------------------------------------------------------------
    # Core routing decision — rule priority order matters
    # ---------------------------------------------------------------------------
 
    @classmethod
    def _decide_route(
        cls,
        entities: dict,
        rewritten: str
    ) -> tuple:
 
        players      = entities.get("players", [])
        intents      = entities.get("intents", [])
        metrics      = entities.get("metrics", [])
        phases       = entities.get("phases", [])
        teams        = entities.get("teams", [])
        venues       = entities.get("venues", [])
        is_comparison = entities.get("is_comparison", False)
        is_profile    = entities.get("is_profile", False)
        is_ranking    = entities.get("is_ranking", False)
        is_team       = entities.get("is_team", False)
        is_venue      = entities.get("is_venue", False)
 
        # ── Rule 1: Pure profile / descriptive → RAG ─────────────────────────
        # "Who is Rohit Sharma", "Tell me about MS Dhoni"
        # Profile with no metrics and no phases = pure narrative question
        if (
            is_profile
            and len(metrics) == 0
            and len(phases) == 0
            and not is_comparison
        ):
            return ROUTE_RAG, (
                "Profile question with no statistical metrics or phases. "
                "RAG can answer this from player intelligence documents."
            )
 
        # ── Rule 2: Comparison with profile intent → HYBRID ──────────────────
        # "Is Rohit better than Kohli overall?"
        # "Compare Dhoni and Kohli as IPL players"
        # Needs SQL stats + RAG narrative for complete answer
        if (
            is_comparison
            and is_profile
            and len(players) >= 2
        ):
            return ROUTE_HYBRID, (
                "Comparison question with profile context. "
                "Needs SQL for statistics and RAG for player narrative."
            )
 
        # ── Rule 3: Comparison with metrics or phases → SQL ──────────────────
        # "Compare Rohit and Kohli in powerplay by strike rate"
        # Pure statistical comparison
        if (
            is_comparison
            and (len(metrics) > 0 or len(phases) > 0)
        ):
            return ROUTE_SQL, (
                "Statistical comparison with specific metrics or phases. "
                "SQL can answer this from analytics tables."
            )
 
        # ── Rule 4: Comparison with no extra context → HYBRID ────────────────
        # "Compare Rohit Sharma and Virat Kohli"
        # Ambiguous — could need both stats and profile context
        if is_comparison and len(players) >= 2:
            return ROUTE_HYBRID, (
                "Comparison question without specific metrics. "
                "Needs both SQL stats and RAG profile for complete answer."
            )
 
        # ── Rule 5: Single player + metric + phase → SQL ─────────────────────
        # "What is Kohli strike rate in powerplay"
        # "How many wickets did Bumrah take in death overs"
        if (
            len(players) == 1
            and len(metrics) > 0
            and len(phases) > 0
        ):
            return ROUTE_SQL, (
                "Single player with specific metric and phase. "
                "SQL can answer this from match_phase_stats table."
            )
 
        # ── Rule 6: Single player + metric → SQL ─────────────────────────────
        # "How many runs did V Kohli score in IPL"
        # "What is DA Warner strike rate"
        if (
            len(players) == 1
            and len(metrics) > 0
            and not is_profile
        ):
            return ROUTE_SQL, (
                "Single player with specific statistical metric. "
                "SQL can answer this from player stats tables."
            )
 
        # ── Rule 7: Single player + phase + performance → HYBRID ─────────────
        # "Why is MS Dhoni effective in death overs"
        # "How does Bumrah perform in powerplay"
        # Needs SQL for numbers + RAG for narrative explanation
        if (
            len(players) == 1
            and len(phases) > 0
            and "performance" in intents
        ):
            return ROUTE_HYBRID, (
                "Player performance question with phase context. "
                "Needs SQL for phase stats and RAG for narrative explanation."
            )
 
        # ── Rule 8: Pure ranking → SQL ────────────────────────────────────────
        # "Top 10 run scorers", "Best economy bowlers"
        # "Best strike rate batters in death overs"
        if is_ranking and len(players) == 0:
            return ROUTE_SQL, (
                "Pure ranking question with no specific player. "
                "SQL can answer this from summary analytics tables."
            )
 
        # ── Rule 9: Venue question → SQL ─────────────────────────────────────
        # "Best batting venue at Eden Gardens"
        # "Which venue has highest average score"
        if is_venue:
            return ROUTE_SQL, (
                "Venue-based analytics question. "
                "SQL can answer this from venue_stats table."
            )
 
        # ── Rule 10: Team question → SQL ─────────────────────────────────────
        # "How does Mumbai Indians perform in powerplay"
        # "Which team wins most powerplay battles"
        if is_team:
            return ROUTE_SQL, (
                "Team performance question. "
                "SQL can answer this from team_stats table."
            )
 
        # ── Rule 11: Player with only profile intent → RAG ───────────────────
        # "Tell me about Jasprit Bumrah bowling style"
        # "Explain Virat Kohli batting technique"
        if len(players) >= 1 and is_profile:
            return ROUTE_RAG, (
                "Player profile or style question. "
                "RAG can answer this from player intelligence documents."
            )
 
        # ── Rule 12: Has metrics or phases but no player → SQL ───────────────
        # "Top economy bowlers in powerplay"
        # "Best strike rate batters in death overs"
        if len(metrics) > 0 or len(phases) > 0:
            return ROUTE_SQL, (
                "Metric or phase based question with no specific player. "
                "SQL can answer this from analytics tables."
            )
 
        # ── Rule 13: Has players but unclear intent → HYBRID ─────────────────
        # Fallback for ambiguous player questions
        if len(players) >= 1:
            return ROUTE_HYBRID, (
                "Player question with ambiguous intent. "
                "Using hybrid to combine SQL stats with RAG context."
            )
 
        # ── Rule 14: Default fallback → RAG ──────────────────────────────────
        # Anything that doesn't match above — treat as descriptive
        return ROUTE_RAG, (
            "No clear statistical intent detected. "
            "Defaulting to RAG for descriptive answer."
        )