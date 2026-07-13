"""
Phase 11.6 — Updated config.py

Fixes:
- Migrated from deprecated class-based Config to model_config
- Uses ConfigDict from pydantic_settings (Pydantic v2 pattern)
- Eliminates PydanticDeprecatedSince20 warning seen in all test runs
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # MySQL
    MYSQL_USER:     str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_HOST:     str = "localhost"
    MYSQL_PORT:     int = 3306
    MYSQL_DATABASE: str = "cricketiq"

    # Groq
    GROQ_API_KEY:   str = ""

    # HuggingFace — Phase 11.6 fix eliminates unauthenticated HF warning
    HF_TOKEN:       str = ""

    # App
    LOG_LEVEL:      str = "INFO"

    # Phase 11.6 fix — replaces deprecated inner class Config
    model_config = SettingsConfigDict(
        env_file        = ".env",
        env_file_encoding = "utf-8",
        case_sensitive  = False,
        extra           = "ignore"
    )


settings = Settings()