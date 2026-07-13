import time
 
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
 
 
class QueryExecutor:
 
    # Hard limit — no query runs longer than this
    TIMEOUT_SECONDS = 10
 
    # Hard limit — never return more than this many rows
    MAX_ROWS = 200
 
    # ---------------------------------------------------------------------------
    # Core execute method
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def execute(db, sql: str) -> dict:
        """
        Execute a validated SELECT query against the MySQL database.
 
        Parameters
        ----------
        db  : SQLAlchemy session (injected by FastAPI dependency)
        sql : validated SQL string from QueryValidator
 
        Returns
        -------
        {
            "sql":               str,
            "rows":              list[dict],
            "row_count":         int,
            "execution_time_ms": float,
            "truncated":         bool,
            "error":             str | None
        }
        """
 
        started_at = time.perf_counter()
 
        try:
            # Set MySQL session timeout before executing
            # This ensures the DB itself enforces the limit
            db.execute(
                text(
                    f"SET SESSION MAX_EXECUTION_TIME = "
                    f"{QueryExecutor.TIMEOUT_SECONDS * 1000}"
                )
            )
 
            result = db.execute(text(sql))
 
            raw_rows = result.fetchmany(QueryExecutor.MAX_ROWS + 1)
 
            # Detect if result was truncated
            truncated = len(raw_rows) > QueryExecutor.MAX_ROWS
            rows = [
                dict(row._mapping)
                for row in raw_rows[:QueryExecutor.MAX_ROWS]
            ]
 
            elapsed_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2
            )
 
            return {
                "sql":               sql,
                "rows":              rows,
                "row_count":         len(rows),
                "execution_time_ms": elapsed_ms,
                "truncated":         truncated,
                "error":             None
            }
 
        except ProgrammingError as error:
            # Malformed SQL that passed validator — schema mismatch etc.
            elapsed_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2
            )
            return QueryExecutor._error_result(
                sql=sql,
                elapsed_ms=elapsed_ms,
                message=f"SQL programming error: {str(error.orig)}"
            )
 
        except OperationalError as error:
            # Timeout, connection lost, DB unavailable
            elapsed_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2
            )
            return QueryExecutor._error_result(
                sql=sql,
                elapsed_ms=elapsed_ms,
                message=f"Database operational error: {str(error.orig)}"
            )
 
        except Exception as error:
            elapsed_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2
            )
            return QueryExecutor._error_result(
                sql=sql,
                elapsed_ms=elapsed_ms,
                message=f"Unexpected execution error: {str(error)}"
            )
 
    # ---------------------------------------------------------------------------
    # Error result builder
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def _error_result(
        sql: str,
        elapsed_ms: float,
        message: str
    ) -> dict:
 
        return {
            "sql":               sql,
            "rows":              [],
            "row_count":         0,
            "execution_time_ms": elapsed_ms,
            "truncated":         False,
            "error":             message
        }