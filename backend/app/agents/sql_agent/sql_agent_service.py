from app.agents.sql_agent.query_executor import QueryExecutor
from app.agents.sql_agent.query_validator import QueryValidator
from app.agents.sql_agent.result_formatter import ResultFormatter
from app.agents.sql_agent.schema_loader import SchemaLoader
from app.agents.sql_agent.sql_generator import SQLGenerator
 
class SQLAgentService:
 
    # ---------------------------------------------------------------------------
    # Health
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def health() -> dict:
 
        return {
            "message":        "SQL Agent running",
            "mode":           "read_only",
            "status":         "healthy",
            "allowed_tables": sorted(SchemaLoader.get_allowed_tables()),
            "phase":          "6.8 — complete pipeline"
        }
 
    # ---------------------------------------------------------------------------
    # Schema
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def schema() -> dict:
 
        return {
            "schema":          SchemaLoader.get_allowed_schema(),
            "schema_context":  SchemaLoader.get_schema_context(),
            "relationships":   SchemaLoader.get_relationships(),
            "metric_aliases":  SchemaLoader.get_metric_aliases()
        }
 
    # ---------------------------------------------------------------------------
    # Relevant schema for a question
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def relevant_schema(question: str) -> dict:
 
        return SchemaLoader.get_query_guidance(question)
 
    # ---------------------------------------------------------------------------
    # Generate SQL only
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def generate_sql(
        question: str,
        limit=None
    ) -> dict:
 
        generation = SQLGenerator.generate(
            question=question,
            limit=limit
        )
 
        return generation
 
    # ---------------------------------------------------------------------------
    # Validate SQL only
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def validate_sql(sql: str) -> dict:
 
        return QueryValidator.validate(sql=sql)
 
    # ---------------------------------------------------------------------------
    # Full pipeline — ask()
    # generate → validate → execute → format → return
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def ask(
        db,
        question: str,
        limit=None
    ) -> dict:
 
        # ── Step 1: Generate SQL from question ──────────────────────────────
        generation = SQLGenerator.generate(
            question=question,
            limit=limit
        )
 
        sql    = generation.get("sql")
        intent = generation.get("intent", "general_analytics")
 
        # ── Step 2: Handle generation failure ───────────────────────────────
        if not sql:
            return {
                "question":        question,
                "intent":          intent,
                "sql":             None,
                "schema_guidance": generation.get("schema_guidance"),
                "validation":      None,
                "answer":          generation.get(
                                       "message",
                                       "Could not generate SQL for this question. "
                                       "Please rephrase and try again."
                                   ),
                "rows":            [],
                "row_count":       0,
                "execution_time_ms": 0,
                "chart_suggestion": "table",
                "error":           "generation_failed"
            }
 
        # ── Step 3: Validate SQL safety ──────────────────────────────────────
        validation = QueryValidator.validate(sql=sql)
 
        if not validation["valid"]:
            return {
                "question":        question,
                "intent":          intent,
                "sql":             sql,
                "schema_guidance": generation.get("schema_guidance"),
                "validation":      validation,
                "answer":          (
                                       "Generated SQL did not pass safety validation. "
                                       f"Errors: {', '.join(validation['errors'])}"
                                   ),
                "rows":            [],
                "row_count":       0,
                "execution_time_ms": 0,
                "chart_suggestion": "table",
                "error":           "validation_failed"
            }
 
        # ── Step 4: Execute SQL against database ─────────────────────────────
        execution = QueryExecutor.execute(db=db, sql=sql)
 
        # Handle execution error
        if execution.get("error"):
            return {
                "question":          question,
                "intent":            intent,
                "sql":               sql,
                "schema_guidance":   generation.get("schema_guidance"),
                "validation":        validation,
                "answer":            (
                                         "SQL executed but encountered an error: "
                                         f"{execution['error']}"
                                     ),
                "rows":              [],
                "row_count":         0,
                "execution_time_ms": execution.get("execution_time_ms", 0),
                "chart_suggestion":  "table",
                "error":             "execution_failed"
            }
 
        # ── Step 5: Format result into narrative answer ───────────────────────
        formatted = ResultFormatter.format(
            rows=execution["rows"],
            intent=intent,
            db=db
        )
 
        # ── Step 6: Return complete response ─────────────────────────────────
        return {
            "question":          question,
            "intent":            intent,
            "sql":               sql,
            "schema_guidance":   generation.get("schema_guidance"),
            "validation":        validation,
            "answer":            formatted["answer"],
            "rows":              formatted["rows"],
            "row_count":         execution["row_count"],
            "execution_time_ms": execution["execution_time_ms"],
            "chart_suggestion":  formatted["chart_suggestion"],
            "truncated":         execution.get("truncated", False),
            "error":             None
        }
 