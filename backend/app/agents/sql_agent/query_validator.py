import re

from app.agents.sql_agent.schema_loader import SchemaLoader


class QueryValidator:

    # ---------------------------------------------------------------------------
    # Blocked keywords — these must NEVER appear in any query
    # ---------------------------------------------------------------------------

    BLOCKED_KEYWORDS = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "replace",
        "merge",
        "call",
        "exec",
        "execute",
        "grant",
        "revoke",
        "rename",
        "load",
        "outfile",
        "dumpfile",
        "into",          # covers SELECT INTO and INSERT INTO
        "information_schema",
        "sys",
        "mysql",
        "--",            # SQL comment injection
        "/*",            # block comment injection
        "xp_",           # SQL Server stored proc pattern
        "benchmark(",    # timing attack
        "sleep(",        # timing attack
    ]

    # ---------------------------------------------------------------------------
    # Allowed statement starters
    # ---------------------------------------------------------------------------

    ALLOWED_STARTERS = re.compile(
        r"^\s*(select|with)\b",
        re.IGNORECASE
    )

    # ---------------------------------------------------------------------------
    # Multiple statement detector
    # ---------------------------------------------------------------------------

    @staticmethod
    def _has_multiple_statements(sql: str) -> bool:
        """
        Detect if the SQL contains more than one statement.
        Splits on semicolons and checks for non-empty extras.
        """
        parts = [p.strip() for p in sql.split(";") if p.strip()]
        return len(parts) > 1

    # ---------------------------------------------------------------------------
    # Table extractor
    # ---------------------------------------------------------------------------

    @staticmethod
    def _extract_tables(sql: str) -> set:
        """
        Extract all real table names referenced in the SQL.
        Looks for FROM and JOIN clauses, then removes CTE alias names
        so that WITH clause queries are not incorrectly blocked.

        Phase 11.3 fix: CTE aliases defined in WITH...AS(...) blocks
        were previously flagged as unknown tables. This method now
        extracts CTE alias names first and excludes them from the
        unknown-table check.
        """
        # Step 1 — collect CTE alias names (words before AS in WITH clause)
        # e.g. "WITH top_batters AS (...)" -> cte_aliases = {"top_batters"}
        cte_pattern = re.compile(
            r"\bwith\b.+?\b([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(",
            re.IGNORECASE | re.DOTALL
        )
        cte_aliases = {
            m.group(1).lower()
            for m in cte_pattern.finditer(sql)
        }

        # Step 2 — collect all words after FROM or JOIN
        table_pattern = re.compile(
            r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            re.IGNORECASE
        )
        all_referenced = {
            m.group(1).lower()
            for m in table_pattern.finditer(sql)
        }

        # Step 3 — remove CTE aliases from referenced set
        # CTE aliases are not real tables so must not be flagged as unknown
        return all_referenced - cte_aliases

    # ---------------------------------------------------------------------------
    # Core validation
    # ---------------------------------------------------------------------------

    @classmethod
    def validate(cls, sql: str) -> dict:
        """
        Validate SQL for safety and schema correctness.

        Returns
        -------
        {
            "valid":   bool,
            "sql":     str | None,
            "errors":  list[str],
            "warnings: list[str]
        }
        """

        errors   = []
        warnings = []

        # --- Guard: empty input ---
        if not sql or not sql.strip():
            return cls._result(
                valid=False,
                sql=None,
                errors=["SQL query is empty."],
                warnings=[]
            )

        cleaned = sql.strip()

        # --- Rule 1: Must start with SELECT or WITH ---
        if not cls.ALLOWED_STARTERS.match(cleaned):
            errors.append(
                "Query must start with SELECT or WITH. "
                "Only read-only queries are allowed."
            )

        # --- Rule 2: No blocked keywords ---
        lower_sql = cleaned.lower()

        for keyword in cls.BLOCKED_KEYWORDS:
            # Use word boundary check for word-like keywords
            # Use plain substring for symbol-like patterns (--  /*)
            if keyword in ("--", "/*", "xp_", "benchmark(", "sleep("):
                if keyword in lower_sql:
                    errors.append(
                        f"Blocked pattern detected: '{keyword}'. "
                        "This query is not allowed."
                    )
            else:
                pattern = rf"\b{re.escape(keyword)}\b"
                if re.search(pattern, lower_sql):
                    errors.append(
                        f"Blocked keyword detected: '{keyword.upper()}'. "
                        "Only SELECT queries are permitted."
                    )

        # --- Rule 3: No multiple statements ---
        if cls._has_multiple_statements(cleaned):
            errors.append(
                "Multiple SQL statements detected. "
                "Only a single SELECT statement is allowed."
            )

        # --- Rule 4: Only known tables ---
        allowed_tables  = SchemaLoader.get_allowed_tables()
        referenced_tables = cls._extract_tables(cleaned)
        unknown_tables  = referenced_tables - allowed_tables

        if unknown_tables:
            errors.append(
                f"Unknown table(s) referenced: {', '.join(sorted(unknown_tables))}. "
                f"Allowed tables: {', '.join(sorted(allowed_tables))}."
            )

        # --- Rule 5: LIMIT check (warning, not error) ---
        has_limit = bool(
            re.search(r"\blimit\b", lower_sql, re.IGNORECASE)
        )

        # If it's a broad query (no WHERE with a specific player name),
        # warn if LIMIT is missing
        has_where = bool(
            re.search(r"\bwhere\b", lower_sql, re.IGNORECASE)
        )

        if not has_limit and not has_where:
            warnings.append(
                "Query has no LIMIT clause and no WHERE filter. "
                "This may return a very large result set."
            )

        # --- Rule 6: SELECT * warning ---
        if re.search(r"select\s+\*", lower_sql, re.IGNORECASE):
            warnings.append(
                "Query uses SELECT *. "
                "Consider selecting specific columns for better performance."
            )

        # --- Final result ---
        is_valid = len(errors) == 0

        return cls._result(
            valid=is_valid,
            sql=cleaned if is_valid else None,
            errors=errors,
            warnings=warnings
        )

    # ---------------------------------------------------------------------------
    # Result builder
    # ---------------------------------------------------------------------------

    @staticmethod
    def _result(
        valid: bool,
        sql,
        errors: list,
        warnings: list
    ) -> dict:

        return {
            "valid":    valid,
            "sql":      sql,
            "errors":   errors,
            "warnings": warnings
        }