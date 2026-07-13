from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
 
from app.agents.sql_agent.sql_agent_service import SQLAgentService
from app.agents.sql_agent.query_executor import QueryExecutor
from app.agents.sql_agent.query_validator import QueryValidator
from app.api.dependencies.database import get_db
 
 
router = APIRouter(
    prefix="/agent/sql",
    tags=["SQL Agent"]
)
 
 
# ---------------------------------------------------------------------------
# GET /agent/sql/health
# ---------------------------------------------------------------------------
 
@router.get("/health")
def sql_agent_health():
 
    return SQLAgentService.health()
 
 
# ---------------------------------------------------------------------------
# GET /agent/sql/schema
# ---------------------------------------------------------------------------
 
@router.get("/schema")
def sql_agent_schema():
 
    return SQLAgentService.schema()
 
 
# ---------------------------------------------------------------------------
# GET /agent/sql/schema/relevant
# ---------------------------------------------------------------------------
 
@router.get("/schema/relevant")
def relevant_sql_schema(question: str):
 
    return SQLAgentService.relevant_schema(question=question)
 
 
# ---------------------------------------------------------------------------
# GET /agent/sql/generate
# ---------------------------------------------------------------------------
 
@router.get("/generate")
def generate_sql(
    question: str,
    limit: int | None = None
):
 
    return SQLAgentService.generate_sql(
        question=question,
        limit=limit
    )
 
 
# ---------------------------------------------------------------------------
# GET /agent/sql/validate
# ---------------------------------------------------------------------------
 
@router.get("/validate")
def validate_sql(sql: str):
 
    return QueryValidator.validate(sql=sql)
 
 
# ---------------------------------------------------------------------------
# GET /agent/sql/execute
# New in Phase 6.5 — runs validated SQL directly against the database
# ---------------------------------------------------------------------------
 
@router.get("/execute")
def execute_sql(
    sql: str,
    db: Session = Depends(get_db)
):
    # Validate first — never execute without safety check
    validation = QueryValidator.validate(sql=sql)
 
    if not validation["valid"]:
        return {
            "sql":               sql,
            "valid":             False,
            "errors":            validation["errors"],
            "warnings":          validation.get("warnings", []),
            "rows":              [],
            "row_count":         0,
            "execution_time_ms": 0,
            "truncated":         False,
            "error":             "SQL blocked by validator."
        }
 
    result = QueryExecutor.execute(db=db, sql=sql)
 
    return {
        "sql":               result["sql"],
        "valid":             True,
        "errors":            [],
        "warnings":          validation.get("warnings", []),
        "rows":              result["rows"],
        "row_count":         result["row_count"],
        "execution_time_ms": result["execution_time_ms"],
        "truncated":         result["truncated"],
        "error":             result["error"]
    }
 
 
# ---------------------------------------------------------------------------
# GET /agent/sql/ask
# Full pipeline: generate → validate → execute → format → answer
# ---------------------------------------------------------------------------
 
@router.get("/ask")
def ask_sql_agent(
    question: str,
    limit: int | None = None,
    db: Session = Depends(get_db)
):
 
    return SQLAgentService.ask(
        db=db,
        question=question,
        limit=limit
    )