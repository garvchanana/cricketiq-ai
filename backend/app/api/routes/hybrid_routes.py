from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.intent_router import IntentRouter
from app.agents.hybrid_composer import HybridComposer
from app.agents.sql_agent.sql_agent_service import SQLAgentService
from app.api.dependencies.database import get_db
from app.rag.chains.full_rag_chain import FullRAGChain


router = APIRouter(
    prefix="/ask",
    tags=["Unified Ask"]
)


# ---------------------------------------------------------------------------
# GET /ask
# Phase 7.5 — Unified entry point
# Routes every question to SQL, RAG, or HYBRID automatically
# ---------------------------------------------------------------------------

@router.get("")
def unified_ask(
    question: str,
    limit: int | None = None,
    db: Session = Depends(get_db)
):
    """
    Unified ask endpoint — the single entry point for all cricket questions.

    Internally:
    1. Rewrites the question (QueryRewriter)
    2. Extracts entities (EntityExtractor)
    3. Routes to correct pipeline (IntentRouter)
    4. Executes SQL, RAG, or HYBRID pipeline
    5. Returns structured response

    Parameters
    ----------
    question : any cricket question in natural language
    limit    : optional result count override (for SQL ranking questions)
    """

    # ── Step 1: Route the question ───────────────────────────────────────────
    routing = IntentRouter.route(
        question=question,
        db=db
    )

    route     = routing["route"]
    rewritten = routing["rewritten"]
    entities  = routing["entities"]
    players   = routing["players"]
    reasoning = routing["reasoning"]

    # Use entity-extracted limit if not overridden by caller
    effective_limit = limit or routing.get("limit")

    # ── Step 2: Execute correct pipeline ─────────────────────────────────────

    # ── SQL path ─────────────────────────────────────────────────────────────
    if route == "SQL":

        result = SQLAgentService.ask(
            db=db,
            question=rewritten,
            limit=effective_limit
        )

        return {
            "question":          question,
            "rewritten":         rewritten,
            "route":             route,
            "reasoning":         reasoning,
            "entities":          entities,
            "answer":            result.get("answer"),
            "rows":              result.get("rows", []),
            "row_count":         result.get("row_count", 0),
            "chart_suggestion":  result.get("chart_suggestion", "table"),
            "sql":               result.get("sql"),
            "execution_time_ms": result.get("execution_time_ms"),
            "error":             result.get("error")
        }

    # ── RAG path ─────────────────────────────────────────────────────────────
    if route == "RAG":

        result = FullRAGChain.ask_cricket_ai(
            query=rewritten,
            db=db
        )

        return {
            "question":          question,
            "rewritten":         rewritten,
            "route":             route,
            "reasoning":         reasoning,
            "entities":          entities,
            "answer":            result.get("answer"),
            "rows":              [],
            "row_count":         0,
            "chart_suggestion":  "none",
            "sql":               None,
            "execution_time_ms": None,
            "error":             None
        }

    # ── HYBRID path ──────────────────────────────────────────────────────────
    if route == "HYBRID":

        result = HybridComposer.compose(
            question=rewritten,
            players=players,
            limit=effective_limit,
            db=db
        )

        return {
            "question":          question,
            "rewritten":         rewritten,
            "route":             route,
            "reasoning":         reasoning,
            "entities":          entities,
            "answer":            result.get("answer"),
            "rows":              result.get("sql_rows", []),
            "row_count":         len(result.get("sql_rows", [])),
            "chart_suggestion":  "none",
            "sql":               None,
            "execution_time_ms": None,
            "error":             result.get("sql_error") or result.get("rag_error")
        }

    # ── Safety fallback ──────────────────────────────────────────────────────
    return {
        "question":  question,
        "rewritten": rewritten,
        "route":     "UNKNOWN",
        "reasoning": reasoning,
        "entities":  entities,
        "answer":    "Could not determine how to answer this question.",
        "error":     "Unknown route"
    }


# ---------------------------------------------------------------------------
# GET /ask/health
# ---------------------------------------------------------------------------

@router.get("/health")
def unified_ask_health():

    return {
        "status":    "healthy",
        "message":   "Unified Ask endpoint running",
        "routes":    ["SQL", "RAG", "HYBRID"],
        "phase":     "7.5 — complete"
    }


# ---------------------------------------------------------------------------
# GET /ask/route
# Debug endpoint — shows routing decision without executing pipeline
# ---------------------------------------------------------------------------

@router.get("/route")
def inspect_route(
    question: str,
    db: Session = Depends(get_db)
):
    """
    Debug endpoint — shows how a question would be routed
    without actually executing any pipeline.
    Useful for testing and understanding routing decisions.
    """

    routing = IntentRouter.route(
        question=question,
        db=db
    )

    return {
        "question":  question,
        "rewritten": routing["rewritten"],
        "route":     routing["route"],
        "reasoning": routing["reasoning"],
        "entities":  routing["entities"],
        "players":   routing["players"],
        "limit":     routing["limit"]
    }