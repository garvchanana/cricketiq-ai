import streamlit as st
 
from services.api_client import ask
from utils.formatters    import (
    rows_to_df,
    format_df_columns,
    format_route_badge,
    format_chart_label,
    format_execution_time,
    has_error,
    get_error_message,
    is_partial_result
)
 
# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
 
st.set_page_config(
    page_title = "Chat — CricketIQ AI",
    page_icon  = "💬",
    layout     = "wide"
)
 
# ---------------------------------------------------------------------------
# Session state — chat history
# ---------------------------------------------------------------------------
 
if "messages" not in st.session_state:
    st.session_state.messages = []
 
if "last_result" not in st.session_state:
    st.session_state.last_result = None
 
# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
 
st.title("💬 CricketIQ Chat")
st.caption(
    "Ask any IPL cricket question. "
    "The system automatically routes to SQL, RAG, or Hybrid."
)
st.divider()
 
# ---------------------------------------------------------------------------
# Suggested questions
# ---------------------------------------------------------------------------
 
with st.expander("💡 Example questions to try", expanded=False):
    examples = [
        "Who scored the most runs in IPL?",
        "Top 5 bowlers by wickets in IPL",
        "Who is MS Dhoni as a player?",
        "Compare Rohit Sharma and Virat Kohli",
        "Best economy bowlers in death overs",
        "Which venue has the highest run rate?",
        "Why is Jasprit Bumrah so effective?",
        "Is Rohit Sharma better than Virat Kohli overall?",
    ]
 
    cols = st.columns(2)
    for i, example in enumerate(examples):
        if cols[i % 2].button(example, key=f"ex_{i}"):
            st.session_state.pending_question = example
            st.rerun()
 
# ---------------------------------------------------------------------------
# Chat history display
# ---------------------------------------------------------------------------
 
chat_container = st.container()
 
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
 
            # Show data table for assistant messages with rows
            if (
                message["role"] == "assistant"
                and message.get("rows")
            ):
                df = rows_to_df(message["rows"])
                if not df.empty:
                    df = format_df_columns(df)
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True
                    )
 
            # Show metadata
            if (
                message["role"] == "assistant"
                and message.get("meta")
            ):
                meta = message["meta"]
                cols = st.columns(4)
                cols[0].caption(
                    f"Route: {format_route_badge(meta.get('route', ''))}"
                )
                cols[1].caption(
                    f"Chart: {format_chart_label(meta.get('chart_suggestion', ''))}"
                )
                cols[2].caption(
                    f"Rows: {meta.get('row_count', 0)}"
                )
                cols[3].caption(
                    f"Time: {format_execution_time(meta.get('execution_time_ms'))}"
                )
 
# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
 
# Handle pending question from example buttons
pending = st.session_state.pop("pending_question", None)
 
question = st.chat_input(
    "Ask any IPL cricket question...",
    key="chat_input"
) or pending
 
if question:
 
    # Add user message to history
    st.session_state.messages.append({
        "role":    "user",
        "content": question
    })
 
    # Display user message
    with st.chat_message("user"):
        st.markdown(question)
 
    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = ask(question=question)
 
        if has_error(result):
            error_msg = get_error_message(result)
            st.error(f"⚠️ {error_msg}")
            st.session_state.messages.append({
                "role":    "assistant",
                "content": f"⚠️ {error_msg}",
                "rows":    [],
                "meta":    {}
            })
 
        else:
            # Show soft warning if partial result
            if is_partial_result(result):
                st.warning(
                    f"⚠️ Partial result — "
                    f"{result.get('error', 'Some data may be missing.')}",
                    icon="⚠️"
                )
            answer   = result.get("answer", "No answer returned.")
            rows     = result.get("rows", [])
            route    = result.get("route", "")
            chart    = result.get("chart_suggestion", "table")
            row_count = result.get("row_count", 0)
            exec_time = result.get("execution_time_ms")
 
            # Display answer
            st.markdown(answer)
 
            # Display data table if rows exist
            if rows:
                df = rows_to_df(rows)
                if not df.empty:
                    df_display = format_df_columns(df.copy())
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        hide_index=True
                    )
 
                    # Bar chart if suggested
                    if chart == "bar" and len(df.columns) >= 2:
                        numeric_cols = df.select_dtypes(
                            include=["int64", "float64"]
                        ).columns.tolist()
                        text_cols = df.select_dtypes(
                            include=["object"]
                        ).columns.tolist()
 
                        if numeric_cols and text_cols:
                            chart_df = df.set_index(text_cols[0])[
                                numeric_cols[0]
                            ]
                            st.bar_chart(chart_df)
 
            # Metadata row
            meta_cols = st.columns(4)
            meta_cols[0].caption(
                f"Route: {format_route_badge(route)}"
            )
            meta_cols[1].caption(
                f"Chart: {format_chart_label(chart)}"
            )
            meta_cols[2].caption(
                f"Rows: {row_count}"
            )
            meta_cols[3].caption(
                f"Time: {format_execution_time(exec_time)}"
            )
 
            # SQL expander if available
            if result.get("sql"):
                with st.expander("🔍 View SQL Query", expanded=False):
                    st.code(result["sql"], language="sql")
 
            # Routing reasoning expander
            if result.get("reasoning"):
                with st.expander("🧭 Routing Reasoning", expanded=False):
                    st.caption(result["reasoning"])
 
            # Save to history
            st.session_state.messages.append({
                "role":    "assistant",
                "content": answer,
                "rows":    rows,
                "meta": {
                    "route":            route,
                    "chart_suggestion": chart,
                    "row_count":        row_count,
                    "execution_time_ms": exec_time
                }
            })
 
# ---------------------------------------------------------------------------
# Sidebar — chat controls
# ---------------------------------------------------------------------------
 
with st.sidebar:
    st.markdown("### 💬 Chat Controls")
 
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
 
    if st.session_state.messages:
        st.caption(
            f"{len(st.session_state.messages)} messages in history"
        )
 
    st.divider()
    st.markdown("### 🧭 Route Guide")
    st.markdown(format_route_badge("SQL"))
    st.caption("Statistical questions")
    st.markdown(format_route_badge("RAG"))
    st.caption("Profile questions")
    st.markdown(format_route_badge("HYBRID"))
    st.caption("Complex questions")