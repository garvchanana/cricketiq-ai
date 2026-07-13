from app.llm.groq_client import GroqClient
 
 
class ResponseGenerator:
 
    # ---------------------------------------------------------------------------
    # Existing RAG response generator — unchanged
    # Uses llama-3.1-8b-instant (fast, good for RAG)
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def generate_response(prompt: str) -> str:
 
        client = GroqClient.get_client()
 
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
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
    # Uses llama3-70b-8192 (more capable, for complex fusion answers)
    # ---------------------------------------------------------------------------
 
    @staticmethod
    def generate_hybrid_response(prompt: str) -> str:
        """
        Generate a hybrid answer that fuses SQL stats with RAG context.
        Uses the larger 70b model for better reasoning on complex questions.
        """
 
        client = GroqClient.get_client()
 
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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