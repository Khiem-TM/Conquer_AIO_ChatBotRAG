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
    request_timeout_seconds: int = 600

    retrieval_top_k: int = 5
    retrieval_candidate_top_k: int = 30
    retrieval_rerank_pool_k: int = 20
    retrieval_keyword_weight: float = 0.45
    retrieval_vector_weight: float = 0.55
    retrieval_rrf_k: int = 60
    retrieval_min_context_score: float = 0.08
    retrieval_dedup_jaccard_threshold: float = 0.88
    retrieval_source_priority_enabled: bool = True
    retrieval_source_priority_min_score: float = 0.14
    retrieval_source_mismatch_penalty_factor: float = 0.15
    retrieval_debug: bool = False
    retrieval_benchmark_top_k: int = 5
    retrieval_benchmark_path: str = 'app/retrieval/benchmark/samples.json'
    retrieval_quality_hit_rate_threshold: float = 0.75
    retrieval_quality_mrr_threshold: float = 0.55
    retrieval_stability_runs: int = 2
    include_citations_default: bool = True

    log_level: str = 'INFO'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )


settings = Settings()
