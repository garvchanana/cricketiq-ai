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
    page_title = "Compare — CricketIQ AI",
    page_icon  = "⚖️",
    layout     = "wide"
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("⚖️ Player Comparison")
st.caption(
    "Compare any two IPL players side by side — "
    "batting, bowling, stats and AI analysis."
)
st.divider()

# ---------------------------------------------------------------------------
# Player input
# ---------------------------------------------------------------------------

col1, col_vs, col2, col_btn = st.columns([3, 0.5, 3, 1])

with col1:
    player_one = st.text_input(
        label       = "Player One",
        placeholder = "e.g. Virat Kohli",
        label_visibility = "visible"
    )

with col_vs:
    st.markdown("<br><br>**VS**", unsafe_allow_html=True)

with col2:
    player_two = st.text_input(
        label       = "Player Two",
        placeholder = "e.g. Rohit Sharma",
        label_visibility = "visible"
    )

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    compare_clicked = st.button(
        "⚖️ Compare",
        use_container_width=True,
        type="primary"
    )

# ---------------------------------------------------------------------------
# Quick compare presets
# ---------------------------------------------------------------------------

st.markdown("**Quick comparisons:**")

presets = [
    ("Virat Kohli", "Rohit Sharma"),
    ("MS Dhoni", "KL Rahul"),
    ("Jasprit Bumrah", "Yuzvendra Chahal"),
    ("AB de Villiers", "Chris Gayle"),
    ("Shikhar Dhawan", "David Warner"),
]

preset_cols = st.columns(len(presets))
for i, (p1, p2) in enumerate(presets):
    if preset_cols[i].button(
        f"{p1.split()[0]} vs {p2.split()[0]}",
        key=f"preset_{i}"
    ):
        st.session_state.compare_p1 = p1
        st.session_state.compare_p2 = p2
        st.rerun()

# Handle preset selection
if "compare_p1" in st.session_state:
    player_one      = st.session_state.pop("compare_p1")
    player_two      = st.session_state.pop("compare_p2")
    compare_clicked = True

st.divider()

# ---------------------------------------------------------------------------
# Comparison execution
# ---------------------------------------------------------------------------

if compare_clicked and player_one and player_two:

    st.markdown(f"## ⚖️ {player_one} vs {player_two}")
    st.divider()

    # ── AI Comparison narrative ───────────────────────────────────────────
    with st.spinner("Generating AI comparison..."):
        ai_result = ask(
            question=f"Is {player_one} better than {player_two} in IPL"
        )

    st.markdown("### 🤖 AI Analysis")
    if has_error(ai_result):
        st.error(get_error_message(ai_result))
    else:
        st.markdown(ai_result.get("answer", "No analysis available."))
        st.caption(
            f"Route: {format_route_badge(ai_result.get('route', ''))} | "
            f"Time: {format_execution_time(ai_result.get('execution_time_ms'))}"
        )

    st.divider()

    # ── Side by side stats ────────────────────────────────────────────────
    st.markdown("### 📊 Head to Head Stats")

    # Build search terms — surname-first strategy
    # DB stores Cricsheet shortcodes: "V Kohli", "MS Dhoni", "AB de Villiers"
    # Always search by LAST word first (surname) — most reliable
    # Fallback: try second-last word if surname fails
    # "Virat Kohli"    → ["Kohli", "Virat"]
    # "AB de Villiers" → ["Villiers", "de"]  (skips "AB" — too short)
    # "MS Dhoni"       → ["Dhoni", "MS"]
    def get_search_terms(name: str) -> list:
        parts = name.strip().split()
        # Always start with last word (surname)
        terms = []
        for part in reversed(parts):
            if len(part) > 2:   # skip initials like "V", "AB", "de"
                terms.append(part)
        return terms if terms else [parts[-1]]

    p1_terms = get_search_terms(player_one)
    p2_terms = get_search_terms(player_two)
    p1_last  = p1_terms[0]
    p2_last  = p2_terms[0]

    tab_bat, tab_bowl, tab_rank = st.tabs([
        "🏏 Batting", "🎳 Bowling", "🏆 Rankings"
    ])

    # Batting comparison
    with tab_bat:
        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.markdown(f"#### {player_one}")
            # Try last word first, then full name search
            bat1 = sql_execute(
                f"SELECT batsman, total_runs, strike_rate, "
                f"batting_average, total_fours, total_sixes "
                f"FROM player_batting_stats "
                f"WHERE batsman LIKE '%{p1_last}%' "
                f"ORDER BY total_runs DESC LIMIT 1"
            )
            if not bat1.get("rows") and len(p1_terms) > 1:
                bat1 = sql_execute(
                    f"SELECT batsman, total_runs, strike_rate, "
                    f"batting_average, total_fours, total_sixes "
                    f"FROM player_batting_stats "
                    f"WHERE batsman LIKE '%{p1_terms[1]}%' "
                    f"ORDER BY total_runs DESC LIMIT 1"
                )
            if bat1.get("rows"):
                df = format_df_columns(rows_to_df(bat1["rows"]))
                st.dataframe(
                    df.T,
                    use_container_width=True
                )
            else:
                st.info("No batting data found.")

        with col_p2:
            st.markdown(f"#### {player_two}")
            bat2 = sql_execute(
                f"SELECT batsman, total_runs, strike_rate, "
                f"batting_average, total_fours, total_sixes "
                f"FROM player_batting_stats "
                f"WHERE batsman LIKE '%{p2_last}%' "
                f"ORDER BY total_runs DESC LIMIT 1"
            )
            if not bat2.get("rows") and len(p2_terms) > 1:
                bat2 = sql_execute(
                    f"SELECT batsman, total_runs, strike_rate, "
                    f"batting_average, total_fours, total_sixes "
                    f"FROM player_batting_stats "
                    f"WHERE batsman LIKE '%{p2_terms[1]}%' "
                    f"ORDER BY total_runs DESC LIMIT 1"
                )
            if bat2.get("rows"):
                df = format_df_columns(rows_to_df(bat2["rows"]))
                st.dataframe(
                    df.T,
                    use_container_width=True
                )
            else:
                st.info("No batting data found.")

        # Combined bar chart
        rows1 = bat1.get("rows", [])
        rows2 = bat2.get("rows", [])
        if rows1 and rows2:
            st.markdown("#### 📈 Batting Comparison Chart")
            import pandas as pd
            metrics = ["total_runs", "strike_rate", "total_fours", "total_sixes"]
            labels  = ["Total Runs", "Strike Rate", "Fours", "Sixes"]
            chart_data = {}
            for metric, label in zip(metrics, labels):
                v1 = rows1[0].get(metric, 0) or 0
                v2 = rows2[0].get(metric, 0) or 0
                chart_data[label] = {
                    player_one.split()[0]: float(v1),
                    player_two.split()[0]: float(v2)
                }
            chart_df = pd.DataFrame(chart_data).T
            st.bar_chart(chart_df)

    # Bowling comparison
    with tab_bowl:
        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.markdown(f"#### {player_one}")
            bowl1 = sql_execute(
                f"SELECT bowler, wickets, economy_rate, "
                f"bowling_average, balls_bowled "
                f"FROM player_bowling_stats "
                f"WHERE bowler LIKE '%{p1_last}%' "
                f"ORDER BY wickets DESC LIMIT 1"
            )
            # Try second search term if first fails
            if not bowl1.get("rows") and len(p1_terms) > 1:
                bowl1 = sql_execute(
                    f"SELECT bowler, wickets, economy_rate, "
                    f"bowling_average, balls_bowled "
                    f"FROM player_bowling_stats "
                    f"WHERE bowler LIKE '%{p1_terms[1]}%' "
                    f"ORDER BY wickets DESC LIMIT 1"
                )
            if bowl1.get("rows"):
                df = format_df_columns(rows_to_df(bowl1["rows"]))
                st.dataframe(df.T, use_container_width=True)
            else:
                st.info("No bowling data found.")

        with col_p2:
            st.markdown(f"#### {player_two}")
            bowl2 = sql_execute(
                f"SELECT bowler, wickets, economy_rate, "
                f"bowling_average, balls_bowled "
                f"FROM player_bowling_stats "
                f"WHERE bowler LIKE '%{p2_last}%' "
                f"ORDER BY wickets DESC LIMIT 1"
            )
            # Try second search term if first fails
            if not bowl2.get("rows") and len(p2_terms) > 1:
                bowl2 = sql_execute(
                    f"SELECT bowler, wickets, economy_rate, "
                    f"bowling_average, balls_bowled "
                    f"FROM player_bowling_stats "
                    f"WHERE bowler LIKE '%{p2_terms[1]}%' "
                    f"ORDER BY wickets DESC LIMIT 1"
                )
            if bowl2.get("rows"):
                df = format_df_columns(rows_to_df(bowl2["rows"]))
                st.dataframe(df.T, use_container_width=True)
            else:
                st.info("No bowling data found.")

    # Rankings comparison
    with tab_rank:
        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.markdown(f"#### {player_one}")
            rank1 = sql_execute(
                f"SELECT player_name, role, ranking_score, "
                f"total_runs, strike_rate, total_wickets, economy_rate "
                f"FROM player_rankings "
                f"WHERE player_name LIKE '%{p1_last}%' "
                f"ORDER BY ranking_score DESC LIMIT 1"
            )
            if not rank1.get("rows") and len(p1_terms) > 1:
                rank1 = sql_execute(
                    f"SELECT player_name, role, ranking_score, "
                    f"total_runs, strike_rate, total_wickets, economy_rate "
                    f"FROM player_rankings "
                    f"WHERE player_name LIKE '%{p1_terms[1]}%' "
                    f"ORDER BY ranking_score DESC LIMIT 1"
                )
            if rank1.get("rows"):
                df = format_df_columns(rows_to_df(rank1["rows"]))
                st.dataframe(df.T, use_container_width=True)
            else:
                st.info("No ranking data found.")

        with col_p2:
            st.markdown(f"#### {player_two}")
            rank2 = sql_execute(
                f"SELECT player_name, role, ranking_score, "
                f"total_runs, strike_rate, total_wickets, economy_rate "
                f"FROM player_rankings "
                f"WHERE player_name LIKE '%{p2_last}%' "
                f"ORDER BY ranking_score DESC LIMIT 1"
            )
            if not rank2.get("rows") and len(p2_terms) > 1:
                rank2 = sql_execute(
                    f"SELECT player_name, role, ranking_score, "
                    f"total_runs, strike_rate, total_wickets, economy_rate "
                    f"FROM player_rankings "
                    f"WHERE player_name LIKE '%{p2_terms[1]}%' "
                    f"ORDER BY ranking_score DESC LIMIT 1"
                )
            if rank2.get("rows"):
                df = format_df_columns(rows_to_df(rank2["rows"]))
                st.dataframe(df.T, use_container_width=True)
            else:
                st.info("No ranking data found.")

        # Ranking score bar chart
        rows_r1 = rank1.get("rows", [])
        rows_r2 = rank2.get("rows", [])
        if rows_r1 and rows_r2:
            import pandas as pd
            st.markdown("#### 🏆 Overall Rating Comparison")
            rating_data = pd.DataFrame({
                "Player": [
                    player_one.split()[0],
                    player_two.split()[0]
                ],
                "Rating": [
                    float(rows_r1[0].get("ranking_score", 0) or 0),
                    float(rows_r2[0].get("ranking_score", 0) or 0)
                ]
            }).set_index("Player")
            st.bar_chart(rating_data)

    st.divider()

    # SQL expander
    if ai_result.get("sql"):
        with st.expander("🔍 View SQL", expanded=False):
            st.code(ai_result["sql"], language="sql")

elif compare_clicked and (not player_one or not player_two):
    st.warning("Please enter both player names to compare.")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚖️ Compare Tips")
    st.markdown("""
    **Supported formats:**
    - Full name: `Virat Kohli`
    - Short code: `V Kohli`
    - Nickname: `MS Dhoni`

    **What you get:**
    - AI-powered comparison analysis
    - Side-by-side batting stats
    - Side-by-side bowling stats
    - Overall ranking comparison
    - Visual bar charts
    """)
    st.divider()
    st.markdown("### 🔥 Popular Comparisons")
    popular = [
        ("Virat Kohli", "Rohit Sharma"),
        ("MS Dhoni", "KL Rahul"),
        ("Bumrah", "Chahal"),
    ]
    for p1, p2 in popular:
        if st.button(
            f"{p1} vs {p2}",
            key=f"sidebar_{p1}_{p2}"
        ):
            st.session_state.compare_p1 = p1
            st.session_state.compare_p2 = p2
            st.rerun()