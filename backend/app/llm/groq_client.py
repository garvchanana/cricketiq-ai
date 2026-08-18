from groq import Groq

from app.core.config import settings


class GroqClient:

    _client = None

    # Phase D.7 model deprecation fix — llama-3.1-8b-instant was
    # deprecated by Groq. Replaced with openai/gpt-oss-20b, Groq's
    # recommended lightweight replacement for fast, simple tasks.
    DEFAULT_MODEL = "openai/gpt-oss-20b"

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