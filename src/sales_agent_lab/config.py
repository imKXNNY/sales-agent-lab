"""Pydantic-settings based configuration for sales-agent-lab."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_default_model: str = "qwen3.5:9b"
    llm_fast_model: str = "qwen3.5:9b"
    llm_temperature: float = 0.5
    llm_max_tokens: int = 2048

    # Kundenportal
    kundenportal_base_url: str = "https://webton-kundenportal.vercel.app"
    kundenportal_service_token: str = Field(default="", description="Service token for Kundenportal AIO API")
    kundenportal_tenant_id: str = "92b2f6a6-5e56-4592-8dee-ff4cbfd53c81"

    # MailOps
    mailops_base_url: str = "http://localhost:3101"
    mailops_service_token: str = Field(default="", description="Service token for MailOps API")

    # Agent
    agent_poll_interval_minutes: int = 5
    agent_min_quality_score: float = 7.0
    agent_sender_name: str = "Tectara Systems"
    agent_reply_to: str = "hello@tectara.io"

    # Webhooks
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000
    webhook_secret: str = ""

    # Voice / future
    voice_enabled: bool = False


settings = Settings()
