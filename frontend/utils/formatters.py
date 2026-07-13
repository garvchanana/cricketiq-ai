import pandas as pd
 
 
# ---------------------------------------------------------------------------
# Row data → Pandas DataFrame
# ---------------------------------------------------------------------------
 
def rows_to_df(rows: list) -> pd.DataFrame:
    """
    Convert API rows list to a clean DataFrame.
    Returns empty DataFrame if rows is empty.
    """
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)
 
 
# ---------------------------------------------------------------------------
# Column name formatter
# ---------------------------------------------------------------------------
 
def format_column_name(col: str) -> str:
    """
    Convert snake_case column names to Title Case for display.
    e.g. "total_runs" → "Total Runs"
    """
    return col.replace("_", " ").title()
 
 
def format_df_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename all DataFrame columns to Title Case.
    """
    if df.empty:
        return df
    df.columns = [format_column_name(c) for c in df.columns]
    return df
 
 
# ---------------------------------------------------------------------------
# Number formatters
# ---------------------------------------------------------------------------
 
def format_number(value) -> str:
    """
    Format large numbers with commas.
    e.g. 9213 → "9,213"
    """
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)
 
 
def format_float(value, decimals: int = 2) -> str:
    """
    Format float to fixed decimal places.
    """
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)
 
 
# ---------------------------------------------------------------------------
# Route badge — coloured label for SQL / RAG / HYBRID
# ---------------------------------------------------------------------------
 
ROUTE_COLORS = {
    "SQL":         "🟢 SQL",
    "RAG":         "🔵 RAG",
    "HYBRID":      "🟣 HYBRID",
    "MULTI_AGENT": "🟠 MULTI-AGENT",
    "UNKNOWN":     "⚪ UNKNOWN"
}
 
 
def format_route_badge(route: str) -> str:
    """
    Return a coloured emoji badge for the route.
    """
    return ROUTE_COLORS.get(route, f"⚪ {route}")
 
 
# ---------------------------------------------------------------------------
# Chart suggestion → chart type label
# ---------------------------------------------------------------------------
 
CHART_LABELS = {
    "bar":   "Bar Chart",
    "radar": "Radar Chart",
    "pie":   "Pie Chart",
    "table": "Data Table",
    "none":  "Text Answer"
}
 
 
def format_chart_label(chart_suggestion: str) -> str:
    return CHART_LABELS.get(chart_suggestion, "Data Table")
 
 
# ---------------------------------------------------------------------------
# Error checker
# ---------------------------------------------------------------------------
 
def has_error(response: dict) -> bool:
    """
    Check if an API response is a fatal error with no usable answer.
 
    Rules:
    - connected=False always means fatal error
    - error field alone is not fatal if answer exists
    - fatal only when: no answer AND error is set
    """
    # Connection failure — always fatal
    if response.get("connected") is False:
        return True
 
    # Has usable answer — not fatal even if error field is set
    answer = response.get("answer", "") or ""
    if str(answer).strip():
        return False
 
    # No answer and error field set — fatal
    error = response.get("error") or ""
    if str(error).strip():
        return True
 
    return False
 
 
def get_error_message(response: dict) -> str:
    """
    Extract the most useful error message from API response.
    """
    error = response.get("error") or ""
    if str(error).strip():
        return str(error)
    return "An unknown error occurred."
 
 
def is_partial_result(response: dict) -> bool:
    """
    True when response has an answer but also a non-fatal error.
    Used to show a soft warning alongside the answer.
    """
    has_answer = bool((response.get("answer") or "").strip())
    has_err    = bool(response.get("error") or "")
    return has_answer and has_err
 
 
# ---------------------------------------------------------------------------
# Player name display
# ---------------------------------------------------------------------------
 
def format_player_name(name: str) -> str:
    """
    Clean up player name for display.
    Handles None and empty strings.
    """
    if not name:
        return "Unknown Player"
    return name.strip().title()
 
 
# ---------------------------------------------------------------------------
# Over number fix — DB is 0-indexed
# Phase 11 fix logged: over_number +1 for display
# ---------------------------------------------------------------------------
 
def format_over_number(over: int) -> str:
    """
    Convert 0-indexed DB over number to 1-indexed display.
    DB stores Over 0 = first over of the match.
    """
    return f"Over {int(over) + 1}"
 
 
# ---------------------------------------------------------------------------
# Execution time formatter
# ---------------------------------------------------------------------------
 
def format_execution_time(ms: float) -> str:
    """
    Format execution time in ms or seconds.
    """
    if ms is None:
        return "N/A"
    if ms < 1000:
        return f"{ms:.1f}ms"
    return f"{ms/1000:.2f}s"