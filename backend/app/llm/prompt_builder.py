class PromptBuilder:
 
    # ---------------------------------------------------------------------------
    # Existing RAG prompt — unchanged
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
        ANSWER
        ------------------------
        """
 
        return prompt
 
    # ---------------------------------------------------------------------------
    # Phase 7.4 — Hybrid prompt
    # Combines SQL stats + RAG narrative into one coherent answer
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
 
========================
ANSWER
========================"""
 
        return prompt