import logging

from app.agents.sql_agent.sql_agent_service import SQLAgentService
from app.llm.prompt_builder import PromptBuilder
from app.llm.response_parser import ResponseGenerator
from app.rag.chains.full_rag_chain import FullRAGChain

logger = logging.getLogger(__name__)


class HybridComposer:
    """
    Phase 7.4 — Hybrid Answer Composer

    Orchestrates the full HYBRID pipeline:

    1. Run SQL pipeline  → get statistics + narrative
    2. Run RAG pipeline  → get player intelligence context
    3. Fuse both         → send to Groq with hybrid prompt
    4. Return complete   → structured response with all components

    Used when IntentRouter returns route = "HYBRID"
    Examples:
        "Is Rohit better than Kohli overall?"
        "Why is MS Dhoni so effective in death overs?"
        "Compare Bumrah and Malinga as IPL bowlers"
    """

    # ---------------------------------------------------------------------------
    # Main compose method
    # ---------------------------------------------------------------------------

    @classmethod
    def compose(
        cls,
        question: str,
        players: list = None,
        limit: int = None,
        db=None
    ) -> dict:
        """
        Run both SQL and RAG pipelines then fuse into one answer.

        Parameters
        ----------
        question : rewritten user question
        players  : resolved player names from entity extractor
        limit    : result count from entity extractor
        db       : SQLAlchemy session

        Returns
        -------
        {
            "answer":        str,   final fused answer
            "sql_answer":    str,   raw SQL narrative
            "sql_rows":      list,  raw SQL data rows
            "rag_context":   str,   raw RAG context
            "sql_error":     str|None,
            "rag_error":     str|None,
            "route":         "HYBRID"
        }
        """

        players = players or []

        # ── Step 1: Run SQL pipeline ─────────────────────────────────────────
        sql_result = cls._run_sql(
            question=question,
            limit=limit,
            db=db
        )

        # ── Step 2: Run RAG pipeline ─────────────────────────────────────────
        rag_result = cls._run_rag(
            question=question,
            players=players,
            db=db
        )

        # ── Step 3: Extract components ───────────────────────────────────────
        sql_answer  = sql_result.get("answer", "")
        sql_rows    = sql_result.get("rows", [])
        sql_error   = sql_result.get("error")

        rag_context = rag_result.get("context", "")
        rag_error   = rag_result.get("error")

        # ── Step 4: Check if both failed ────────────────────────────────────
        if sql_error and rag_error:
            return cls._result(
                answer=(
                    "Both the statistical database and player intelligence "
                    "pipelines were unable to answer this question. "
                    "Please rephrase and try again."
                ),
                sql_answer=sql_answer,
                sql_rows=sql_rows,
                rag_context=rag_context,
                sql_error=sql_error,
                rag_error=rag_error
            )

        # ── Step 5: Build hybrid prompt ──────────────────────────────────────
        prompt = PromptBuilder.build_hybrid_prompt(
            query=question,
            sql_answer=sql_answer,
            sql_rows=sql_rows,
            rag_context=rag_context,
            players=players
        )

        # ── Step 6: Generate fused answer ────────────────────────────────────
        try:
            fused_answer = ResponseGenerator.generate_hybrid_response(
                prompt=prompt
            )
        except Exception as error:
            # Fallback — return SQL answer if LLM fusion fails
            fused_answer = (
                sql_answer
                or rag_result.get("answer", "")
                or f"Hybrid fusion failed: {str(error)}"
            )

        return cls._result(
            answer=fused_answer,
            sql_answer=sql_answer,
            sql_rows=sql_rows,
            rag_context=rag_context,
            sql_error=sql_error,
            rag_error=rag_error
        )

    # ---------------------------------------------------------------------------
    # SQL pipeline runner
    # ---------------------------------------------------------------------------

    @staticmethod
    def _run_sql(
        question: str,
        limit=None,
        db=None
    ) -> dict:

        try:
            result = SQLAgentService.ask(
                db=db,
                question=question,
                limit=limit
            )
            return result

        except Exception as error:
            return {
                "answer": "",
                "rows":   [],
                "error":  f"SQL pipeline error: {str(error)}"
            }

    # ---------------------------------------------------------------------------
    # RAG pipeline runner
    # ---------------------------------------------------------------------------

    @staticmethod
    def _run_rag(
        question: str,
        players: list = None,
        db=None
    ) -> dict:
        """
        Phase 11.4 fix — use multi-player retrieval when two or more
        players are identified. This ensures both players get their own
        RAG context retrieved, preventing the second player from being
        missed in comparison questions.
        """

        try:
            # Ensure question is always a plain string
            if isinstance(question, dict):
                question = question.get("rewritten") or question.get("original") or str(question)

            question = str(question)

            # Phase 11.4 — use multi-player retrieval for comparisons
            if players and len(players) >= 2:
                result = FullRAGChain.ask_multi_player(
                    query=question,
                    players=players,
                    db=db
                )
                return {
                    "context": result.get("context", ""),
                    "answer":  result.get("answer", ""),
                    "error":   None
                }

            # Single player or no player — standard RAG chain
            result = FullRAGChain.ask_cricket_ai(
                query=question,
                db=db
            )

            return {
                "context": result.get("context", ""),
                "answer":  result.get("answer", ""),
                "error":   None
            }

        except Exception as error:
            logger.error("RAG pipeline error: %s", str(error))
            return {
                "context": "",
                "answer":  "",
                "error":   f"RAG pipeline error: {str(error)}"
            }

    # ---------------------------------------------------------------------------
    # Result builder
    # ---------------------------------------------------------------------------

    @staticmethod
    def _result(
        answer:      str,
        sql_answer:  str,
        sql_rows:    list,
        rag_context: str,
        sql_error,
        rag_error
    ) -> dict:

        return {
            "answer":      answer,
            "sql_answer":  sql_answer,
            "sql_rows":    sql_rows,
            "rag_context": rag_context,
            "sql_error":   sql_error,
            "rag_error":   rag_error,
            "route":       "HYBRID"
        }