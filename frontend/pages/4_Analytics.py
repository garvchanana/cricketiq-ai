import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st

from services.api_client import ask, sql_execute
from utils.formatters import (
    format_route_badge,
    format_execution_time,
    rows_to_df,
    format_df_columns,
    has_error,
    get_error_message
)
from utils.player_registry import canonicalize_df

st.set_page_config(
    page_title = "Analytics — CricketIQ AI",
    page_icon  = "📊",
    layout     = "wide"
)

st.title("📊 SQL Analytics Explorer")
st.caption(
    "Ask any statistical question in plain English "
    "or write SQL directly. Powered by the IPL database."
)
st.divider()

# ---------------------------------------------------------------------------
# Mode selector
# ---------------------------------------------------------------------------

mode = st.radio(
    "Mode",
    ["💬 Natural Language", "🔧 Direct SQL"],
    horizontal=True
)

st.divider()

# ---------------------------------------------------------------------------
# Natural Language mode
# ---------------------------------------------------------------------------

if mode == "💬 Natural Language":

    st.markdown("### Ask a statistical question")

    question = st.text_input(
        label       = "Question",
        placeholder = "e.g. Top 10 run scorers in IPL",
        label_visibility = "collapsed"
    )

    col_btn, col_limit = st.columns([1, 2])
    with col_btn:
        ask_clicked = st.button(
            "📊 Analyse",
            type="primary",
            use_container_width=True
        )
    with col_limit:
        limit = st.slider("Result limit", 5, 50, 10)

    # Quick question buttons
    st.markdown("**Quick questions:**")
    quick = [
        "Top 10 run scorers in IPL",
        "Top 10 wicket takers in IPL",
        "Best economy bowlers in IPL",
        "Top venues by run rate",
        "Best strike rate batters in IPL",
        "Top all rounders by ranking",
    ]
    q_cols = st.columns(3)
    for i, q in enumerate(quick):
        if q_cols[i % 3].button(q, key=f"quick_q_{i}"):
            st.session_state.analytics_question = q
            st.rerun()

    if "analytics_question" in st.session_state:
        question    = st.session_state.pop("analytics_question")
        ask_clicked = True

    if ask_clicked and question:
        with st.spinner("Analysing..."):
            result = ask(question=question, limit=limit)

        if has_error(result):
            st.error(get_error_message(result))
        else:
            st.markdown(f"### {result.get('answer', '')}")

            rows = result.get("rows", [])
            if rows:
                # Natural language route already canonicalizes server-side
                # via ResultFormatter, but apply client-side too as a
                # safety net in case any raw SQL leaks through
                df = format_df_columns(canonicalize_df(rows_to_df(rows)))
                st.dataframe(df, use_container_width=True, hide_index=True)

                chart = result.get("chart_suggestion", "table")
                if chart == "bar" and len(df.columns) >= 2:
                    numeric = df.select_dtypes(include=["int64","float64"]).columns.tolist()
                    text    = df.select_dtypes(include=["object"]).columns.tolist()
                    if numeric and text:
                        st.bar_chart(df.set_index(text[0])[numeric[0]])

            col1, col2, col3 = st.columns(3)
            col1.caption(f"Route: {format_route_badge(result.get('route',''))}")
            col2.caption(f"Rows: {result.get('row_count', 0)}")
            col3.caption(f"Time: {format_execution_time(result.get('execution_time_ms'))}")

            if result.get("sql"):
                with st.expander("🔍 View SQL", expanded=False):
                    st.code(result["sql"], language="sql")

    elif ask_clicked:
        st.warning("Please enter a question.")

# ---------------------------------------------------------------------------
# Direct SQL mode
# ---------------------------------------------------------------------------

else:
    st.markdown("### Write SQL directly")
    st.caption(
        "Only SELECT queries allowed. Max 200 rows returned. "
        "Note: player names shown here are canonicalized for display, "
        "but you must use DB shortcode names (e.g. 'V Kohli') in your "
        "WHERE clauses, since that's the raw stored format."
    )

    sql_input = st.text_area(
        label  = "SQL Query",
        height = 120,
        placeholder = (
            "SELECT batsman, total_runs, strike_rate\n"
            "FROM player_batting_stats\n"
            "ORDER BY total_runs DESC\n"
            "LIMIT 10"
        ),
        label_visibility = "collapsed"
    )

    if st.button("▶ Execute", type="primary"):
        if sql_input.strip():
            with st.spinner("Executing..."):
                result = sql_execute(sql_input.strip())

            if result.get("error"):
                st.error(f"⚠️ {result['error']}")
            elif result.get("rows"):
                # Phase D.6 fix — canonicalize raw shortcode names
                # (sql_execute is the raw debug endpoint by design,
                # so we canonicalize client-side for display only)
                df = format_df_columns(canonicalize_df(rows_to_df(result["rows"])))
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(
                    f"Rows: {result['row_count']} | "
                    f"Time: {format_execution_time(result.get('execution_time_ms'))}"
                )
            else:
                st.info("Query returned no rows.")
        else:
            st.warning("Please enter a SQL query.")

    # Schema reference — Phase D.6 fix: added missing tables and
    # clarified which tables are intentionally excluded from the
    # SQL agent (RAG-only / raw ball-level tables)
    with st.expander("📋 Available Tables", expanded=False):
        st.markdown("""
        **Tables accessible via SQL agent:**

        | Table | Key Columns |
        |---|---|
        | `player_batting_stats` | batsman, total_runs, strike_rate, batting_average, total_fours, total_sixes |
        | `player_bowling_stats` | bowler, wickets, economy_rate, bowling_average, balls_bowled |
        | `player_rankings` | player_name, role, ranking_score, total_runs, total_wickets |
        | `match_phase_stats` | phase, run_rate, wickets, boundaries, dot_balls |
        | `venue_stats` | venue, average_run_rate, total_matches, total_boundaries, venue_type |
        | `team_stats` | team_name, total_runs, run_rate, aggression_index, pressure_index |
        | `batter_bowler_matchups` | batsman, bowler, total_runs, dismissals, strike_rate, dominance_index |
        | `advanced_batting_stats` | batsman, boundary_percentage, dot_ball_percentage, aggression_index |
        | `matches` | match_id, team1, team2, venue, winner (international data, not IPL-specific) |

        **Not accessible via SQL agent** (used internally by RAG/other pipelines):
        `ball_by_ball`, `players`, `player_intelligence`, `player_mappings`,
        `match_momentum_stats` — these are excluded by design for performance
        and safety reasons.
        """)

with st.sidebar:
    st.markdown("### 📊 Analytics Tips")
    st.markdown("""
    **Natural Language examples:**
    - Top 10 run scorers
    - Best economy in death overs
    - Most sixes in IPL
    - Highest strike rate batters

    **Direct SQL examples:**
    ```sql
    SELECT bowler, wickets
    FROM player_bowling_stats
    ORDER BY wickets DESC
    LIMIT 10
    ```

    **CTE example:**
    ```sql
    WITH top_bowlers AS (
        SELECT bowler, wickets, economy_rate
        FROM player_bowling_stats
        WHERE balls_bowled >= 120
        ORDER BY wickets DESC
        LIMIT 5
    )
    SELECT * FROM top_bowlers
    ORDER BY economy_rate ASC
    ```
    """)