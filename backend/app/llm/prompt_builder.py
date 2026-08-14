class PromptBuilder:

    # ---------------------------------------------------------------------------
    # Existing RAG prompt — Phase D.7 fix: added explicit anti-verbatim
    # instructions to stop the LLM from echoing raw context labels
    # (e.g. "Player Name: X\nRole: Y") instead of writing a natural sentence.
    # This bug was confirmed deterministic for players with longer/more
    # complete context (all-rounders with both batting and bowling data).
    # ---------------------------------------------------------------------------

    @staticmethod
    def build_cricket_prompt(
        query: str,
        context: str,
        conversation_history=None
    ) -> str:

        prompt = f"""
        You are an advanced cricket AI analyst.

        Player Name and Canonical Name may refer
        to the same player.

        Use ONLY the provided cricket context
        and conversation history to answer.

        CRITICAL FORMATTING RULES — follow strictly:
        - NEVER copy field labels from the context verbatim
          (e.g. do not write "Player Name:", "Role:", "Canonical Name:",
          "Batting Summary:", "Bowling Summary:", "Intelligence Summary:").
        - Write your answer as natural, flowing sentences only —
          as if you already know this player and are describing them
          to someone, not reading from a database record.
        - Never repeat the same fact twice in different phrasing.
        - Do not include structural markers like "---" or "===" or
          any part of the context's internal formatting.

        If the answer is unavailable,
        say:
        "The available cricket intelligence
        does not contain enough information."

        ------------------------
        CONVERSATION HISTORY
        ------------------------

        {conversation_history}

        ------------------------
        CRICKET CONTEXT
        ------------------------

        {context}

        ------------------------
        USER QUESTION
        ------------------------

        {query}

        ------------------------
        ANSWER (natural sentences only, no labels, no field names)
        ------------------------
        """

        return prompt

    # ---------------------------------------------------------------------------
    # Phase 7.4 — Hybrid prompt
    # Combines SQL stats + RAG narrative into one coherent answer
    # Phase D.7 fix: same anti-verbatim guard added here too
    # ---------------------------------------------------------------------------

    @staticmethod
    def build_hybrid_prompt(
        query: str,
        sql_answer: str,
        sql_rows: list,
        rag_context: str,
        players: list = None
    ) -> str:
        """
        Build a prompt that fuses SQL statistics with RAG narrative context.

        Parameters
        ----------
        query       : original user question
        sql_answer  : narrative answer from ResultFormatter
        sql_rows    : raw data rows from SQL execution
        rag_context : retrieved player intelligence from RAG pipeline
        players     : list of player names involved in the question
        """

        # Format SQL rows as a readable table
        if sql_rows:
            rows_text = "\n".join(
                "  " + ", ".join(
                    f"{k}: {v}" for k, v in row.items()
                )
                for row in sql_rows[:10]  # cap at 10 rows
            )
        else:
            rows_text = "No statistical data available."

        players_text = (
            ", ".join(players)
            if players
            else "Not specified"
        )

        prompt = f"""You are CricketIQ — an advanced IPL cricket intelligence analyst.

You have been given two sources of information to answer the user's question:

1. STATISTICAL DATA — from the IPL database (factual, numerical)
2. PLAYER INTELLIGENCE — from cricket knowledge documents (contextual, narrative)

Your job is to combine both sources into one complete, insightful answer.

========================
USER QUESTION
========================
{query}

========================
PLAYERS INVOLVED
========================
{players_text}

========================
STATISTICAL DATA (SQL)
========================
Summary: {sql_answer}

Detailed rows:
{rows_text}

========================
PLAYER INTELLIGENCE (RAG)
========================
{rag_context}

========================
INSTRUCTIONS
========================
1. Lead with the key statistical insight from the SQL data.
2. Enrich it with context from the player intelligence.
3. If comparing players, address both statistics and playing style.
4. Keep the answer focused, insightful, and cricket-specific.
5. Do not hallucinate — only use the data provided above.
6. If either source has no useful data, rely on the other.
7. End with a brief conclusion or key takeaway.
8. NEVER copy field labels verbatim (e.g. "Player Name:", "Role:",
   "Canonical Name:", "Batting Summary:"). Write natural sentences only.
9. Do not repeat the same fact twice in different wording.
10. Do not include structural markers like "---" or "===" from the
    source context in your answer.

========================
ANSWER (natural sentences only, no labels, no field names)
========================"""

        return prompt