import logging

from app.rag.chains.rag_pipeline import RAGPipeline
from app.llm.prompt_builder import PromptBuilder
from app.llm.response_parser import ResponseGenerator
from app.nlp.canonicalization.canonicalizer import Canonicalizer

logger = logging.getLogger(__name__)


class FullRAGChain:

    @staticmethod
    def ask_cricket_ai(
        query: str,
        db=None
    ):
        """
        Full RAG pipeline — retrieve context then generate answer.

        Phase 11.4 fixes:
        1. Removed print() debug statement — now uses logger.debug()
        2. Empty/null chunks filtered before prompt building
        3. Multi-player queries retrieve context for both players
        """

        rag_result = RAGPipeline.generate_context(
            query=query,
            db=db
        )

        context = rag_result.get("context", "")

        display_query = Canonicalizer.canonicalize_text(
            query,
            db=db
        )

        # Phase 11.4 fix 1 — replaced print() with logger.debug()
        # Use DEBUG level so it only appears when debug logging enabled
        # Previously this printed full context to terminal on every request
        logger.debug("RAG context retrieved:\n%s", context)

        # Phase 11.4 fix 2 — filter empty/null context before prompting
        # Empty context causes the LLM to hallucinate or say
        # "no information available" unhelpfully
        if not context or not context.strip():
            logger.warning(
                "RAG retrieval returned empty context for query: %s",
                query
            )
            context = (
                "No specific player intelligence found for this query. "
                "Answer based on general IPL cricket knowledge."
            )

        prompt = PromptBuilder.build_cricket_prompt(
            query=display_query,
            context=context,
            conversation_history=None
        )

        answer = ResponseGenerator.generate_response(prompt)

        return {
            "query":         display_query,
            "answer":        answer,
            "retrieved_docs": rag_result.get("retrieved_docs", []),
            "context":       context
        }

    @staticmethod
    def ask_multi_player(
        query: str,
        players: list,
        db=None
    ) -> dict:
        """
        Phase 11.4 fix 3 — Multi-player retrieval for comparison questions.

        When comparing two players, the default semantic retrieval
        sometimes only returns context for one player (higher semantic
        similarity). This method explicitly retrieves context for
        each named player separately and combines both contexts.

        Used by HybridComposer for HYBRID comparison questions.
        """

        combined_context_parts = []
        all_docs = []

        for player in players:
            # Build a focused query for each player individually
            player_query = f"Who is {player} as an IPL player"

            result = RAGPipeline.generate_context(
                query=player_query,
                db=db
            )

            player_context = result.get("context", "").strip()

            # Phase 11.4 fix 2 — skip empty contexts
            if player_context and len(player_context) > 50:
                combined_context_parts.append(
                    f"--- {player} ---\n{player_context}"
                )

            docs = result.get("retrieved_docs", [])
            # Filter out null player_name docs
            valid_docs = [
                d for d in docs
                if d.get("player_name") and d.get("chunk")
            ]
            all_docs.extend(valid_docs)

        # Also run the original combined query for broader context
        combined_result = RAGPipeline.generate_context(
            query=query,
            db=db
        )
        combined_query_context = combined_result.get("context", "").strip()
        if combined_query_context and len(combined_query_context) > 50:
            combined_context_parts.append(
                f"--- Combined Context ---\n{combined_query_context}"
            )

        full_context = "\n\n".join(combined_context_parts)

        if not full_context:
            full_context = (
                "No specific player intelligence found. "
                "Answer based on general IPL cricket knowledge."
            )

        logger.debug(
            "Multi-player RAG context for %s:\n%s",
            players,
            full_context
        )

        display_query = Canonicalizer.canonicalize_text(
            query, db=db
        )

        prompt = PromptBuilder.build_cricket_prompt(
            query=display_query,
            context=full_context,
            conversation_history=None
        )

        answer = ResponseGenerator.generate_response(prompt)

        return {
            "query":          display_query,
            "answer":         answer,
            "retrieved_docs": all_docs,
            "context":        full_context,
            "players":        players
        }