import streamlit as st
 
# ---------------------------------------------------------------------------
# Page configuration — must be first Streamlit call
# ---------------------------------------------------------------------------
 
st.set_page_config(
    page_title       = "CricketIQ AI",
    page_icon        = "🏏",
    layout           = "wide",
    initial_sidebar_state = "expanded"
)
 
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
 
from services.api_client import health_check
 
# ---------------------------------------------------------------------------
# Sidebar — navigation and status
# ---------------------------------------------------------------------------
 
with st.sidebar:
    st.markdown("# 🏏")
    st.title("CricketIQ AI")
    st.caption("IPL Intelligence Platform")
    st.divider()
 
    st.markdown("**Navigate**")
    st.markdown("""
    - 💬 **Chat** — Ask anything
    - 🔍 **Player Search** — Full profiles
    - ⚖️ **Compare** — Side by side
    - 📊 **Analytics** — SQL explorer
    - 🏆 **Rankings** — Leaderboard
    - 🏟️ **Venues** — Ground stats
    """)
 
    st.divider()
 
    # Backend status
    st.markdown("**System Status**")
    try:
        backend = health_check()
        if backend.get("connected") is False:
            st.error("⚠️ Backend offline")
        else:
            st.success("✅ Backend connected")
            st.caption(f"Phase: {backend.get('phase', 'unknown')}")
    except Exception:
        st.error("⚠️ Cannot reach backend")
 
# ---------------------------------------------------------------------------
# Home page content
# ---------------------------------------------------------------------------
 
st.title("🏏 CricketIQ AI")
st.subheader("IPL Cricket Intelligence Platform")
st.markdown(
    "Ask any cricket question in plain English. "
    "CricketIQ combines statistical analysis with "
    "player intelligence to give you deep IPL insights."
)
 
st.divider()
 
# ---------------------------------------------------------------------------
# Quick start — example questions
# ---------------------------------------------------------------------------
 
col1, col2, col3 = st.columns(3)
 
with col1:
    st.markdown("### 📊 Analytics")
    st.markdown("""
    - Who scored most runs in IPL?
    - Top 10 wicket takers
    - Best economy bowlers in death overs
    - Which venue has highest run rate?
    """)
 
with col2:
    st.markdown("### 👤 Player Intelligence")
    st.markdown("""
    - Who is MS Dhoni as a player?
    - Tell me about Jasprit Bumrah
    - Explain Virat Kohli batting style
    - What kind of player is Rohit Sharma?
    """)
 
with col3:
    st.markdown("### ⚖️ Comparisons")
    st.markdown("""
    - Is Rohit better than Kohli in IPL?
    - Compare Bumrah and Chahal
    - Mumbai Indians vs CSK performance
    - Best powerplay vs death overs batters
    """)
 
st.divider()
 
# ---------------------------------------------------------------------------
# Route explanation
# ---------------------------------------------------------------------------
 
st.markdown("### How CricketIQ routes your question")
 
r1, r2, r3 = st.columns(3)
 
with r1:
    st.info(
        "🟢 **SQL Route**\n\n"
        "Statistical and ranking questions. "
        "Answered directly from the IPL database "
        "with exact numbers and charts."
    )
 
with r2:
    st.info(
        "🔵 **RAG Route**\n\n"
        "Profile and descriptive questions. "
        "Answered from player intelligence "
        "documents with narrative context."
    )
 
with r3:
    st.info(
        "🟣 **Hybrid Route**\n\n"
        "Complex questions needing both. "
        "Combines database stats with player "
        "intelligence for complete answers."
    )
 
st.divider()
st.caption(
    "Built with FastAPI · MySQL · FAISS · Groq LLM · Streamlit | "
    "Data: IPL ball-by-ball from Cricsheet"
)