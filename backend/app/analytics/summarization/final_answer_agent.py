from app.analytics.player_analysis.player_analyst import PlayerAnalyst
from app.analytics.match_analysis.match_analyst import MatchAnalyst
from app.analytics.commentary_analysis.matchup_analyst import MatchupAnalyst
from app.llm.groq_client import GroqClient
from app.rag.chains.full_rag_chain import FullRAGChain
 
 
class FinalAnswerAgent:
    """
    Phase 8.4 — Final Answer Agent
 
    The top-level orchestrator of the multi-agent system.
    Decides which specialist agents to call based on question
    entities and intent, collects their outputs, and fuses
    everything into one coherent cricket intelligence answer.
 
    Agent call matrix:
    ┌─────────────────────┬──────────┬───────────┬──────────┬─────┐
    │ Question type       │ Player   │ Match     │ Matchup  │ RAG │
    ├─────────────────────┼──────────┼───────────┼──────────┼─────┤
    │ Player profile      │ ✓        │           │          │ ✓   │
    │ Player comparison   │ ✓        │           │ ✓        │ ✓   │
    │ Phase question      │          │ ✓         │          │     │
    │ Venue question      │          │ ✓         │          │     │
    │ Team question       │          │ ✓         │          │     │
    │ Head to head        │ ✓        │           │ ✓        │     │
    │ Full analysis       │ ✓        │ ✓         │ ✓        │ ✓   │
    └─────────────────────┴──────────┴───────────┴──────────┴─────┘
 
    Called by:
    - /ask endpoint for complex questions
    - HybridComposer when multi-agent depth is needed
    """
 
    # ---------------------------------------------------------------------------
    # Primary method — answer any cricket question
    # ---------------------------------------------------------------------------
 
    @classmethod
    def answer(
        cls,
        question:     str,
        entities:     dict,
        db
    ) -> dict:
        """
        Orchestrate specialist agents and produce a final answer.
 
        Parameters
        ----------
        question : rewritten user question
        entities : extracted entities from EntityExtractor
        db       : SQLAlchemy session
 
        Returns
        -------
        {
            "answer":          str,   final fused answer
            "agents_called":   list,  which agents were used
            "player_data":     dict,  from PlayerAnalyst
            "match_data":      dict,  from MatchAnalyst
            "matchup_data":    dict,  from MatchupAnalyst
            "rag_data":        dict,  from FullRAGChain
            "route":           str    "MULTI_AGENT"
        }
        """
 
        players      = entities.get("players", [])
        phases       = entities.get("phases", [])
        venues       = entities.get("venues", [])
        teams        = entities.get("teams", [])
        is_comparison = entities.get("is_comparison", False)
        is_profile    = entities.get("is_profile", False)
        is_ranking    = entities.get("is_ranking", False)
        is_team       = entities.get("is_team", False)
        is_venue      = entities.get("is_venue", False)
 
        agents_called = []
        player_data   = {}
        match_data    = {}
        matchup_data  = {}
        rag_data      = {}
 
        # ── Player agent ─────────────────────────────────────────────────────
        if len(players) >= 2 and is_comparison:
            player_data = PlayerAnalyst.compare_players(
                player_one=players[0],
                player_two=players[1],
                db=db
            )
            agents_called.append("PlayerAnalyst.compare")
 
        elif len(players) == 1:
            player_data = PlayerAnalyst.get_player_profile(
                player_name=players[0],
                db=db
            )
            agents_called.append("PlayerAnalyst.profile")
 
        elif is_ranking and not players:
            player_data = PlayerAnalyst.get_top_players(
                limit=10,
                db=db
            )
            agents_called.append("PlayerAnalyst.top_players")
 
        # ── Match / phase / venue / team agent ────────────────────────────────
        if phases:
            match_data["phases"] = MatchAnalyst.get_phase_stats(
                phase=phases[0],
                db=db
            )
            agents_called.append("MatchAnalyst.phase_stats")
 
        if venues:
            match_data["venue"] = MatchAnalyst.get_venue_stats(
                venue_name=venues[0],
                db=db
            )
            agents_called.append("MatchAnalyst.venue_stats")
 
        if is_team and teams:
            match_data["team"] = MatchAnalyst.get_team_record(
                team_name=teams[0],
                db=db
            )
            agents_called.append("MatchAnalyst.team_record")
 
        if not phases and not venues and not is_team and not players:
            match_data["phase_summary"] = MatchAnalyst.get_phase_summary(
                db=db
            )
            agents_called.append("MatchAnalyst.phase_summary")
 
        # ── Matchup agent ─────────────────────────────────────────────────────
        if len(players) >= 2 and is_comparison:
            matchup_data["head_to_head"] = MatchupAnalyst.get_head_to_head(
                batter=players[0],
                bowler=players[1],
                db=db
            )
            agents_called.append("MatchupAnalyst.head_to_head")
 
        if len(players) == 1 and phases:
            matchup_data["batter_best"] = MatchupAnalyst.get_batter_best_matchups(
                batter=players[0],
                limit=3,
                db=db
            )
            agents_called.append("MatchupAnalyst.batter_best")
 
        # ── RAG agent — for profile and complex questions ──────────────────────
        if is_profile or (len(players) >= 1 and not is_ranking):
            try:
                rag_data = FullRAGChain.ask_cricket_ai(
                    query=question,
                    db=db
                )
                agents_called.append("RAGChain")
            except Exception as e:
                rag_data = {
                    "answer": "",
                    "error":  str(e)
                }
 
        # ── Fuse all outputs into final answer ────────────────────────────────
        final_answer = cls._fuse(
            question=question,
            entities=entities,
            player_data=player_data,
            match_data=match_data,
            matchup_data=matchup_data,
            rag_data=rag_data,
            agents_called=agents_called
        )
 
        return {
            "answer":        final_answer,
            "agents_called": agents_called,
            "player_data":   player_data,
            "match_data":    match_data,
            "matchup_data":  matchup_data,
            "rag_data":      rag_data,
            "route":         "MULTI_AGENT"
        }
 
    # ---------------------------------------------------------------------------
    # Fusion method — combine all agent outputs
    # ---------------------------------------------------------------------------
 
    @classmethod
    def _fuse(
        cls,
        question:     str,
        entities:     dict,
        player_data:  dict,
        match_data:   dict,
        matchup_data: dict,
        rag_data:     dict,
        agents_called: list
    ) -> str:
 
        # Build context sections from each agent
        sections = []
 
        # Player section
        if player_data:
            if "comparison_narrative" in player_data:
                sections.append(
                    f"PLAYER COMPARISON:\n{player_data.get('comparison_narrative', '')}"
                )
            elif "narrative" in player_data:
                sections.append(
                    f"PLAYER PROFILE:\n{player_data.get('narrative', '')}"
                )
            elif "players" in player_data:
                top = player_data["players"][:5]
                lines = "\n".join(
                    f"  {p['player_name']} | {p['role']} | "
                    f"Rating: {p['ranking_score']}"
                    for p in top
                )
                sections.append(f"TOP PLAYERS:\n{lines}")
 
        # Match / phase section
        if match_data:
            for key, data in match_data.items():
                if isinstance(data, dict) and data.get("narrative"):
                    sections.append(
                        f"MATCH CONTEXT ({key.upper()}):\n{data['narrative']}"
                    )
 
        # Matchup section
        if matchup_data:
            for key, data in matchup_data.items():
                if isinstance(data, dict) and data.get("narrative"):
                    sections.append(
                        f"MATCHUP INSIGHT ({key.upper()}):\n{data['narrative']}"
                    )
 
        # RAG section
        if rag_data and rag_data.get("answer"):
            sections.append(
                f"PLAYER INTELLIGENCE:\n{rag_data.get('answer', '')}"
            )
 
        # If no sections — return fallback
        if not sections:
            return (
                "I was unable to find enough data to answer this question. "
                "Please try rephrasing or asking about a specific player or stat."
            )
 
        context_text = "\n\n".join(sections)
 
        prompt = f"""You are CricketIQ — an expert IPL cricket intelligence analyst.
You have gathered data from multiple specialist agents to answer this question.
Synthesize all the information below into one clear, insightful, complete answer.
 
AGENTS USED: {", ".join(agents_called)}
 
QUESTION:
{question}
 
GATHERED INTELLIGENCE:
{context_text}
 
INSTRUCTIONS:
1. Lead with the most relevant insight for the question.
2. Incorporate statistics, matchup data, and player intelligence naturally.
3. Be specific — name players, quote numbers, reference phases.
4. Do not repeat information — synthesize it.
5. End with a clear conclusion or key takeaway.
6. Keep it under 250 words.
 
FINAL ANSWER:"""
 
        try:
            return GroqClient.complete(
                system_prompt=(
                    "You are CricketIQ, a world-class IPL cricket analyst. "
                    "Synthesize multi-agent intelligence into clear, "
                    "data-driven cricket answers."
                ),
                user_prompt=prompt,
                temperature=0.4,
                max_tokens=350
            )
        except Exception as error:
            # Fallback — join all narratives directly
            return "\n\n".join(sections)