"""Configuration model using environment variables."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openai_api_key: str = Field(default="", description="Optional OpenAI API key for fallback")
    sec_agent_model: str = Field(default="", description="Force a specific model for all stages")
    sec_agent_user_agent: str = Field(
        default="SEC-Filing-Agent admin@example.com",
        description="User-Agent header for SEC EDGAR requests",
    )

    @classmethod
    def from_env(cls) -> Settings:
        """Load settings from environment variables."""
        return cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            sec_agent_model=os.environ.get("SEC_AGENT_MODEL", ""),
            sec_agent_user_agent=os.environ.get(
                "SEC_AGENT_USER_AGENT", "SEC-Filing-Agent admin@example.com"
            ),
        )
