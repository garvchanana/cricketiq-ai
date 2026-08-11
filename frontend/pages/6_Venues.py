import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
 
from services.api_client import sql_execute
from utils.formatters    import (
    rows_to_df,
    format_execution_time
)
 
st.set_page_config(
    page_title = "Venues — CricketIQ AI",
    page_icon  = "🏟️",
    layout     = "wide"
)
 
st.title("🏟️ Venue Analytics")
st.caption("IPL venue statistics — run rates, boundaries, pitch types and match counts.")
st.divider()
 
# ---------------------------------------------------------------------------
# Venue overview — top venues
# ---------------------------------------------------------------------------
 
st.markdown("### 🏆 Top Venues by Run Rate")
 
col_limit, col_sort = st.columns(2)
 
with col_limit:
    limit = st.slider("Show top N venues", 5, 30, 10)
 
with col_sort:
    sort_col = st.selectbox(
        "Sort by",
        ["average_run_rate", "total_matches", "total_boundaries", "dot_ball_percentage"]
    )
 
sort_order = st.radio(
    "Order",
    ["DESC ↓", "ASC ↑"],
    horizontal=True,
    index=0
)
sort_dir = "DESC" if "DESC" in sort_order else "ASC"
 
# Filter to significant venues only (min 5 matches)
# This removes one-off venues while keeping all IPL grounds
with st.spinner("Loading venue data..."):
    result = sql_execute(
        f"SELECT venue, total_matches, total_runs, average_run_rate, "
        f"total_boundaries, dot_ball_percentage, venue_type "
        f"FROM venue_stats "
        f"WHERE total_matches >= 5 "
        f"ORDER BY {sort_col} {sort_dir} "
        f"LIMIT {limit}"
    )
 
rows = result.get("rows", [])
 
if rows:
    df = rows_to_df(rows)
    df_display = df.copy()
    df_display.columns = [
        "Venue", "Matches", "Total Runs",
        "Run Rate", "Boundaries", "Dot Ball %", "Type"
    ]
    df_display["Run Rate"]    = df_display["Run Rate"].apply(lambda x: round(float(x), 2))
    df_display["Dot Ball %"]  = df_display["Dot Ball %"].apply(lambda x: round(float(x), 2))
 
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
 
    # Run rate bar chart
    st.markdown("### 📈 Run Rate by Venue")
    chart_df = df_display.set_index("Venue")["Run Rate"]
    st.bar_chart(chart_df)
 
    st.caption(
        f"{len(rows)} venues shown | "
        f"Time: {format_execution_time(result.get('execution_time_ms'))}"
    )
 
else:
    st.info("No venue data found.")
 
st.divider()
 
# ---------------------------------------------------------------------------
# Phase stats across all venues
# ---------------------------------------------------------------------------
 
st.markdown("### 🎯 Match Phase Summary")
 
with st.spinner("Loading phase data..."):
    phase_result = sql_execute(
        "SELECT phase, run_rate, wickets, boundaries, dot_balls "
        "FROM match_phase_stats "
        "ORDER BY FIELD(phase, 'Powerplay', 'Middle Overs', 'Death Overs')"
    )
 
phase_rows = phase_result.get("rows", [])
 
if phase_rows:
    df_phase = rows_to_df(phase_rows)
    df_phase.columns = ["Phase", "Run Rate", "Wickets", "Boundaries", "Dot Balls"]
    df_phase["Run Rate"] = df_phase["Run Rate"].apply(lambda x: round(float(x), 2))
 
    col_pp, col_mo, col_do = st.columns(3)
 
    phase_map = {r["phase"]: r for r in phase_rows}
 
    pp = phase_map.get("Powerplay", {})
    mo = phase_map.get("Middle Overs", {})
    do = phase_map.get("Death Overs", {})
 
    with col_pp:
        st.markdown("#### ⚡ Powerplay")
        st.metric("Run Rate",   f"{round(float(pp.get('run_rate', 0)), 2)}")
        st.metric("Wickets",    f"{pp.get('wickets', 0):,}")
        st.metric("Boundaries", f"{pp.get('boundaries', 0):,}")
 
    with col_mo:
        st.markdown("#### 🔄 Middle Overs")
        st.metric("Run Rate",   f"{round(float(mo.get('run_rate', 0)), 2)}")
        st.metric("Wickets",    f"{mo.get('wickets', 0):,}")
        st.metric("Boundaries", f"{mo.get('boundaries', 0):,}")
 
    with col_do:
        st.markdown("#### 💥 Death Overs")
        st.metric("Run Rate",   f"{round(float(do.get('run_rate', 0)), 2)}")
        st.metric("Wickets",    f"{do.get('wickets', 0):,}")
        st.metric("Boundaries", f"{do.get('boundaries', 0):,}")
 
    st.divider()
 
    # Phase run rate chart
    st.markdown("### 📊 Run Rate by Phase")
    chart_df = df_phase.set_index("Phase")["Run Rate"]
    st.bar_chart(chart_df)
 
st.divider()
 
# ---------------------------------------------------------------------------
# Team stats
# ---------------------------------------------------------------------------
 
st.markdown("### 🏏 Team Performance")
 
with st.spinner("Loading team data..."):
    team_result = sql_execute(
        "SELECT team_name, total_runs, run_rate, "
        "total_boundaries, aggression_index, pressure_index "
        "FROM team_stats "
        "ORDER BY total_runs DESC"
    )
 
team_rows = team_result.get("rows", [])
 
if team_rows:
    df_team = rows_to_df(team_rows)
    df_team.columns = [
        "Team", "Total Runs", "Run Rate",
        "Boundaries", "Aggression Index", "Pressure Index"
    ]
    df_team["Run Rate"]         = df_team["Run Rate"].apply(lambda x: round(float(x), 2))
    df_team["Aggression Index"] = df_team["Aggression Index"].apply(lambda x: round(float(x), 2))
    df_team["Pressure Index"]   = df_team["Pressure Index"].apply(lambda x: round(float(x), 2))
 
    st.dataframe(
        df_team,
        use_container_width=True,
        hide_index=True
    )
 
    # Team runs bar chart
    st.markdown("### 📈 Total Runs by Team")
    st.bar_chart(df_team.set_index("Team")["Total Runs"])
 
with st.sidebar:
    st.markdown("### 🏟️ Venue Guide")
    st.markdown("""
    **Pitch types:**
    - **Batting Friendly** — high run rate, flat pitch
    - **Bowling Friendly** — low run rate, assists bowlers
    - **Balanced** — even contest
 
    **Key metrics:**
    - **Run Rate** — average runs per over
    - **Dot Ball %** — percentage of dot balls
    - **Boundaries** — total fours and sixes
 
    **Phase guide:**
    - Powerplay: overs 1-6
    - Middle overs: overs 7-15
    - Death overs: overs 16-20
    """)