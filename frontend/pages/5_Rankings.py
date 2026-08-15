import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
 
from services.api_client import sql_execute
from utils.formatters    import (
    rows_to_df,
    format_execution_time
)
from utils.player_registry import PLAYER_REGISTRY
 
st.set_page_config(
    page_title = "Rankings — CricketIQ AI",
    page_icon  = "🏆",
    layout     = "wide"
)
 
st.title("🏆 IPL Rankings")
st.caption("Overall player rankings based on batting, bowling and all-round performance.")
st.divider()
 
# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
 
col_role, col_limit, col_sort = st.columns(3)
 
with col_role:
    role_filter = st.selectbox(
        "Filter by player type",
        ["All", "Top Batters", "Top Bowlers", "All-Rounders"]
    )
 
with col_limit:
    limit = st.slider("Show top N players", 10, 100, 25)
 
with col_sort:
    sort_by = st.selectbox(
        "Sort by",
        ["ranking_score", "total_runs", "total_wickets", "strike_rate"]
    )
 
sort_order = st.radio(
    "Order",
    ["DESC", "ASC"],
    horizontal=True,
    index=0
)
 
st.divider()
 
# ---------------------------------------------------------------------------
# Build query — use performance thresholds not role column
# since DB classifies most players as All-Rounder
# ---------------------------------------------------------------------------
 
# Performance-based segmentation
# Top Batters:    runs >= 500 AND wickets < 20
# Top Bowlers:    wickets >= 30 AND runs < 1000
# All-Rounders:   runs >= 500 AND wickets >= 20
if role_filter == "Top Batters":
    where_clause = "WHERE total_runs >= 500 AND total_wickets < 20"
elif role_filter == "Top Bowlers":
    where_clause = "WHERE total_wickets >= 30 AND total_runs < 2000"
elif role_filter == "All-Rounders":
    where_clause = "WHERE total_runs >= 500 AND total_wickets >= 20"
else:
    where_clause = "WHERE total_runs >= 100 OR total_wickets >= 10"
 
query = (
    f"SELECT player_name, role, ranking_score, "
    f"total_runs, strike_rate, total_wickets, economy_rate "
    f"FROM player_rankings "
    f"{where_clause} "
    f"ORDER BY {sort_by} {sort_order} "
    f"LIMIT {limit}"
)
 
with st.spinner("Loading rankings..."):
    result = sql_execute(query)
 
rows = result.get("rows", [])
 
if rows:
    df = rows_to_df(rows)
 
    # Canonicalize names using PLAYER_REGISTRY
    df["player_name"] = df["player_name"].apply(
        lambda n: PLAYER_REGISTRY.get(n, n)
    )
 
    # Add rank column
    df.insert(0, "rank", range(1, len(df) + 1))
 
    # Format display
    df_display = df.copy()
    df_display.columns = [
        "Rank", "Player", "DB Role", "Rating",
        "Runs", "Strike Rate", "Wickets", "Economy"
    ]
    # Derive meaningful role from actual performance
    def derive_role(row):
        runs    = int(row["Runs"] or 0)
        wickets = int(row["Wickets"] or 0)
        if runs >= 500 and wickets >= 20:
            return "All-Rounder"
        elif wickets >= 20:
            return "Bowler"
        else:
            return "Batter"
 
    df_display["Role"] = df_display.apply(derive_role, axis=1)
    # Reorder columns
    df_display = df_display[[
        "Rank", "Player", "Role", "Rating",
        "Runs", "Strike Rate", "Wickets", "Economy"
    ]]
    df_display["Rating"]      = df_display["Rating"].apply(lambda x: round(float(x), 2))
    df_display["Strike Rate"] = df_display["Strike Rate"].apply(lambda x: round(float(x), 2))
    # Show economy as 0.0 for players with 0 wickets
    df_display["Economy"] = df.apply(
        lambda row: 0.0 if int(row["total_wickets"] or 0) == 0
        else round(float(row["economy_rate"] or 0), 2),
        axis=1
    )
 
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
 
    st.caption(
        f"{len(rows)} players shown | "
        f"Sorted by {sort_by} {sort_order} | "
        f"Time: {format_execution_time(result.get('execution_time_ms'))}"
    )
 
    st.divider()
 
    # ---------------------------------------------------------------------------
    # Top 10 rating bar chart
    # ---------------------------------------------------------------------------
 
    st.markdown("### 📈 Top 10 by Rating")
    top10 = df_display.head(10)
    chart_df = top10.set_index("Player")["Rating"]
    st.bar_chart(chart_df)
 
    # ---------------------------------------------------------------------------
    # Role distribution
    # ---------------------------------------------------------------------------
 
    if role_filter == "All":
        st.markdown("### 🎭 Role Distribution")
        role_counts = df_display["Role"].value_counts().reset_index()
        role_counts.columns = ["Role", "Count"]
        col_pie, col_tbl = st.columns([2, 1])
        with col_tbl:
            st.dataframe(role_counts, use_container_width=True, hide_index=True)
        with col_pie:
            st.bar_chart(role_counts.set_index("Role")["Count"])
 
else:
    st.info("No ranking data found. Try changing the filters.")
 
with st.sidebar:
    st.markdown("### 🏆 Rankings Info")
    st.markdown("""
    **Rating formula:**
    ```
    (runs × 0.4)
    + (strike_rate × 0.3)
    + (wickets × 8)
    - (economy × 2)
    ```
    **Roles:**
    - Batter — primarily batting contribution
    - Bowler — primarily bowling contribution
    - All-Rounder — balanced contribution
 
    **Note:** Role classification based
    on the ranking formula, not playing
    position. Phase 11 will improve this.
    """)