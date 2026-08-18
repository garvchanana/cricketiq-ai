from app.llm.groq_client import GroqClient


class ResponseGenerator:

    # ---------------------------------------------------------------------------
    # Existing RAG response generator
    # Phase D.7 model deprecation fix — llama-3.1-8b-instant deprecated
    # by Groq. Replaced with openai/gpt-oss-20b (fast, good for RAG).
    # ---------------------------------------------------------------------------

    @staticmethod
    def generate_response(prompt: str) -> str:

        client = GroqClient.get_client()

        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        return completion.choices[0].message.content

    # ---------------------------------------------------------------------------
    # Phase 7.4 — Hybrid response generator
    # Phase D.7 model deprecation fix — llama-3.3-70b-versatile
    # deprecated by Groq. Replaced with openai/gpt-oss-120b, Groq's
    # recommended replacement for more capable, complex reasoning tasks.
    # ---------------------------------------------------------------------------

    @staticmethod
    def generate_hybrid_response(prompt: str) -> str:
        """
        Generate a hybrid answer that fuses SQL stats with RAG context.
        Uses the larger model for better reasoning on complex questions.
        """

        client = GroqClient.get_client()

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role":    "system",
                    "content": (
                        "You are CricketIQ, an expert IPL cricket analyst. "
                        "You combine statistical data with player intelligence "
                        "to give insightful, accurate cricket answers. "
                        "Always ground your answer in the provided data."
                    )
                },
                {
                    "role":    "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
            max_tokens=1024
        )

        return completion.choices[0].message.content