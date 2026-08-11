import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st

from services.api_client import ask, sql_execute
from utils.formatters    import (
    format_route_badge,
    format_execution_time,
    has_error,
    get_error_message,
    rows_to_df,
    format_df_columns
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title = "Player Search — CricketIQ AI",
    page_icon  = "🔍",
    layout     = "wide"
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🔍 Player Search")
st.caption(
    "Search any IPL player to get their full profile — "
    "stats, intelligence summary, and AI analysis."
)
st.divider()

# ---------------------------------------------------------------------------
# Search input
# ---------------------------------------------------------------------------

col_search, col_btn = st.columns([4, 1])

with col_search:
    player_input = st.text_input(
        label       = "Player name",
        placeholder = "e.g. MS Dhoni, Virat Kohli, Jasprit Bumrah...",
        label_visibility = "collapsed"
    )

with col_btn:
    search_clicked = st.button(
        "🔍 Search",
        use_container_width=True,
        type="primary"
    )

# ---------------------------------------------------------------------------
# Quick search buttons
# ---------------------------------------------------------------------------

st.markdown("**Quick search:**")
quick_players = [
    "MS Dhoni", "Virat Kohli", "Rohit Sharma",
    "Jasprit Bumrah", "AB de Villiers", "Suresh Raina",
    "KL Rahul", "Ravindra Jadeja", "Yuzvendra Chahal"
]

cols = st.columns(len(quick_players))
for i, player in enumerate(quick_players):
    if cols[i].button(player, key=f"quick_{i}"):
        st.session_state.player_search = player
        st.rerun()

# Handle quick search selection
if "player_search" in st.session_state:
    player_input   = st.session_state.pop("player_search")
    search_clicked = True

st.divider()

# ---------------------------------------------------------------------------
# Search execution
# ---------------------------------------------------------------------------

if search_clicked and player_input:

    with st.spinner(f"Fetching profile for {player_input}..."):

        # Use /ask endpoint with profile question
        question = f"Who is {player_input} as an IPL player"
        result   = ask(question=question)

        # Also get stats via SQL
        stats_question = f"What are the IPL stats of {player_input}"
        stats_result   = ask(question=stats_question)

    if has_error(result):
        st.error(get_error_message(result))

    else:
        # ---------------------------------------------------------------------------
        # Player header
        # ---------------------------------------------------------------------------

        st.markdown(f"## 🏏 {player_input}")
        st.caption(
            f"Route: {format_route_badge(result.get('route', ''))} | "
            f"Rewritten as: _{result.get('rewritten', player_input)}_"
        )

        # ---------------------------------------------------------------------------
        # Two column layout — profile + stats
        # ---------------------------------------------------------------------------

        col_profile, col_stats = st.columns([3, 2])

        with col_profile:
            st.markdown("### 📖 Player Intelligence")
            answer = result.get("answer", "No profile data available.")
            st.markdown(answer)

        with col_stats:
            st.markdown("### 📊 Career Stats")

            # Get last name for DB lookup
            last_name = player_input.split()[-1]

            # Try batting stats first
            bat_sql = (
                f"SELECT batsman, total_runs, strike_rate, "
                f"batting_average, total_fours, total_sixes "
                f"FROM player_batting_stats "
                f"WHERE batsman LIKE '%{last_name}%' LIMIT 3"
            )
            bat_exec = sql_execute(bat_sql)
            bat_rows = bat_exec.get("rows", [])

            # Try bowling stats
            bowl_sql = (
                f"SELECT bowler, wickets, economy_rate, "
                f"bowling_average, balls_bowled "
                f"FROM player_bowling_stats "
                f"WHERE bowler LIKE '%{last_name}%' LIMIT 3"
            )
            bowl_exec = sql_execute(bowl_sql)
            bowl_rows = bowl_exec.get("rows", [])

            if bat_rows:
                st.caption("Batting")
                df = format_df_columns(rows_to_df(bat_rows))
                st.dataframe(df, use_container_width=True, hide_index=True)

            if bowl_rows:
                st.caption("Bowling")
                df = format_df_columns(rows_to_df(bowl_rows))
                st.dataframe(df, use_container_width=True, hide_index=True)

            if not bat_rows and not bowl_rows:
                st.info("No stats found. Try the Analytics page.")

        st.divider()

        # ---------------------------------------------------------------------------
        # Additional insights
        # ---------------------------------------------------------------------------

        st.markdown("### 🔬 Deep Dive")

        tab_batting, tab_bowling, tab_matchups = st.tabs([
            "🏏 Batting", "🎳 Bowling", "⚔️ Matchups"
        ])

        with tab_batting:
            with st.spinner("Loading batting stats..."):
                bat_result = ask(
                    question=(
                        f"How many runs total_runs strike_rate "
                        f"batting_average fours sixes has {player_input} "
                        f"scored in IPL"
                    )
                )

            if bat_result.get("rows"):
                df = format_df_columns(rows_to_df(bat_result["rows"]))
                st.dataframe(df, use_container_width=True, hide_index=True)
                if bat_result.get("answer"):
                    st.markdown(bat_result["answer"])
            elif bat_result.get("answer"):
                st.markdown(bat_result["answer"])
            else:
                # Direct SQL fallback
                from services.api_client import sql_ask
                fallback = sql_ask(
                    question=f"SELECT batsman, total_runs, strike_rate, "
                             f"batting_average FROM player_batting_stats "
                             f"WHERE batsman LIKE "
                             f"'%{player_input.split()[-1]}%' LIMIT 5"
                )
                if fallback.get("rows"):
                    df = format_df_columns(rows_to_df(fallback["rows"]))
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info(
                        f"{player_input} has minimal batting stats in IPL. "
                        "This is expected for specialist bowlers."
                    )

        with tab_bowling:
            with st.spinner("Loading bowling stats..."):
                bowl_result = ask(
                    question=(
                        f"How many wickets economy_rate bowling_average "
                        f"balls_bowled has {player_input} taken in IPL"
                    )
                )

            if bowl_result.get("rows"):
                df = format_df_columns(rows_to_df(bowl_result["rows"]))
                st.dataframe(df, use_container_width=True, hide_index=True)
                if bowl_result.get("answer"):
                    st.markdown(bowl_result["answer"])
            elif bowl_result.get("answer"):
                st.markdown(bowl_result["answer"])
            else:
                st.info(
                    f"{player_input} has minimal bowling stats in IPL. "
                    "This is expected for specialist batters."
                )

        with tab_matchups:
            last_name = player_input.split()[-1]

            with st.spinner("Loading matchup data..."):

                # As batter — bowlers this player dominates
                batter_sql = (
                    f"SELECT bowler, total_runs, balls_faced, "
                    f"dismissals, strike_rate, dominance_index "
                    f"FROM batter_bowler_matchups "
                    f"WHERE batsman LIKE '%{last_name}%' "
                    f"ORDER BY dominance_index DESC LIMIT 10"
                )
                batter_exec = sql_execute(batter_sql)

                # As bowler — batters this player dismisses most
                bowler_sql = (
                    f"SELECT batsman, total_runs, balls_faced, "
                    f"dismissals, strike_rate, dominance_index "
                    f"FROM batter_bowler_matchups "
                    f"WHERE bowler LIKE '%{last_name}%' "
                    f"ORDER BY dismissals DESC LIMIT 10"
                )
                bowler_exec = sql_execute(bowler_sql)

            st.markdown("#### ⚔️ As Batter — Bowlers Dominated")
            if batter_exec.get("rows"):
                df = format_df_columns(
                    rows_to_df(batter_exec["rows"])
                )
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
                st.caption(
                    f"Showing bowlers {player_input} scores "
                    f"freely against (highest dominance index)"
                )
            else:
                st.info(
                    f"No batter matchup data found for {player_input}."
                )

            st.markdown("#### 🎳 As Bowler — Batters Dismissed Most")
            if bowler_exec.get("rows"):
                df = format_df_columns(
                    rows_to_df(bowler_exec["rows"])
                )
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
                st.caption(
                    f"Showing batters {player_input} has "
                    f"dismissed most often"
                )
            else:
                st.info(
                    f"No bowling matchup data found for {player_input}."
                )

        st.divider()

        # ---------------------------------------------------------------------------
        # SQL and routing metadata
        # ---------------------------------------------------------------------------

        meta_col1, meta_col2, meta_col3 = st.columns(3)
        meta_col1.caption(
            f"Route: {format_route_badge(result.get('route', ''))}"
        )
        meta_col2.caption(
            f"Time: {format_execution_time(result.get('execution_time_ms'))}"
        )
        meta_col3.caption(
            f"Rows: {result.get('row_count', 0)}"
        )

        if result.get("sql"):
            with st.expander("🔍 View SQL", expanded=False):
                st.code(result["sql"], language="sql")

elif search_clicked and not player_input:
    st.warning("Please enter a player name to search.")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🔍 Player Search Tips")
    st.markdown("""
    **Supported formats:**
    - Full name: `Virat Kohli`
    - Short code: `V Kohli`
    - Nickname: `MS Dhoni`
    - Informal: `Hitman` (Rohit Sharma)

    **What you get:**
    - AI-generated player profile
    - Career batting stats
    - Career bowling stats
    - Batter-bowler matchup insights
    """)
    st.divider()
    st.markdown("### 🏏 Popular Searches")
    popular = ["Virat Kohli", "MS Dhoni", "Jasprit Bumrah"]
    for p in popular:
        if st.button(p, key=f"sidebar_{p}"):
            st.session_state.player_search = p
            st.rerun()