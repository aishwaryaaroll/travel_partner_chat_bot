"""Settings loaded from the environment and ``personal-info/.env``.

The API key is a ``SecretStr`` so it never shows up in reprs, logs or errors.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import PROJECT_ROOT

ENV_FILE = PROJECT_ROOT / "personal-info" / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: SecretStr = SecretStr("")
    model: str = "claude-sonnet-5-5"
    allowed_origins: str = "http://localhost:5173"
    session_ttl_minutes: int = Field(default=60, ge=1, le=24 * 60)
    max_sessions: int = Field(default=500, ge=1)
    max_messages_per_session: int = Field(default=60, ge=2)
    max_message_chars: int = Field(default=2000, ge=10)
    max_body_bytes: int = Field(default=16_384, ge=1024)
    agent_timeout_seconds: float = Field(default=240, gt=0)
    agent_max_turns: int = Field(default=14, ge=1)
    agent_max_budget_usd: float = Field(default=1.0, gt=0)
    rate_limit_chat: str = "20/minute"
    rate_limit_default: str = "60/minute"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip() and o.strip() != "*"]

    @property
    def agent_configured(self) -> bool:
        return bool(self.anthropic_api_key.get_secret_value().strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
