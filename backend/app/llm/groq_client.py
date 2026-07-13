from groq import Groq
 
from app.core.config import settings
 
 
class GroqClient:
 
    _client = None
 
    # Default model — Groq's fastest, most capable free-tier model
    DEFAULT_MODEL = "llama-3.1-8b-instant"
 
    # ---------------------------------------------------------------------------
    # Client singleton
    # ---------------------------------------------------------------------------
 
    @classmethod
    def get_client(cls) -> Groq:
 
        if cls._client is None:
            cls._client = Groq(api_key=settings.GROQ_API_KEY)
 
        return cls._client
 
    # ---------------------------------------------------------------------------
    # Core completion method
    # Used by: SQLGenerator, and any future agent that needs LLM calls
    # ---------------------------------------------------------------------------
 
    @classmethod
    def complete(
        cls,
        user_prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> str:
        """
        Send a prompt to Groq and return the response as a plain string.
 
        Parameters
        ----------
        user_prompt   : the main question or instruction
        system_prompt : role/behavior instruction for the model
        model         : override the default model if needed
        temperature   : lower = more deterministic (0.1 is good for SQL)
        max_tokens    : cap on response length
 
        Returns
        -------
        Plain string response from the model.
        Raises exception on API failure (caller handles it).
        """
 
        client = cls.get_client()
 
        response = client.chat.completions.create(
            model=model or cls.DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
 
        return response.choices[0].message.content
