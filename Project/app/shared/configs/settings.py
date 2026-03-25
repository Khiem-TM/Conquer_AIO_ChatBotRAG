from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'rag-chatbot-api'
    app_env: str = 'dev'
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    api_prefix: str = '/api/v1'
    cors_origins: list[str] = Field(default_factory=lambda: ['http://localhost:3000'])

    ollama_base_url: str = 'http://ollama:11434'
    ollama_model: str = 'llama3.1:8b'
    request_timeout_seconds: int = 120

    retrieval_top_k: int = 5
    include_citations_default: bool = True

    log_level: str = 'INFO'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )


settings = Settings()
