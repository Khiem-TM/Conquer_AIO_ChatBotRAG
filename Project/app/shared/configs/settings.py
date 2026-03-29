from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

IndexStoreBackend = Literal['local_json', 'sqlite', 'qdrant']


class Settings(BaseSettings):
    app_name: str = 'rag-chatbot-api'
    app_env: Literal['dev', 'local', 'prod'] = 'local'
    app_host: str = '0.0.0.0'
    app_port: int = 8000
    api_prefix: str = '/api/v1'
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            'http://localhost:3000',
            'http://127.0.0.1:3000',
            'http://localhost:5173',
            'http://127.0.0.1:5173',
        ]
    )

    ollama_base_url: str = 'http://localhost:11434'
    ollama_model: str = 'llama3.1:8b'
    ollama_reranker_model: str = 'llama3.1:8b'
    embedding_model: str = 'nomic-embed-text'
    request_timeout_seconds: int = 600
    ollama_max_concurrent_requests: int = 1
    ollama_http_max_connections: int = 20
    ollama_http_max_keepalive_connections: int = 10
    ollama_stream_read_timeout_seconds: int = 0
    ollama_keep_alive: str = '30m'

    index_data_input_dir: str = 'data_input'
    index_storage_path: str = 'data/index_store.json'
    index_db_path: str = 'data/app_state.db'
    index_store_backend: IndexStoreBackend = 'sqlite'
    qdrant_path: str = 'data/qdrant'
    qdrant_collection: str = 'rag_chunks'
    embedding_dimensions: int = 768
    index_chunk_size: int = 1000
    index_chunk_overlap: int = 160
    index_chunker_version: str = 'v2'
    index_schema_version: int = 2

    retrieval_top_k: int = 5
    retrieval_candidate_top_k: int = 30
    retrieval_rerank_pool_k: int = 18
    retrieval_keyword_weight: float = 0.48
    retrieval_vector_weight: float = 0.52
    retrieval_rrf_k: int = 60
    retrieval_min_context_score: float = 0.05
    retrieval_dedup_jaccard_threshold: float = 0.9
    retrieval_query_cache_size: int = 512
    retrieval_enable_metadata_boost: bool = True
    retrieval_enable_context_compression: bool = True
    retrieval_enable_llm_reranker: bool = False
    retrieval_multi_query_rewrites: int = 1
    prompt_max_context_chars_per_chunk: int = 1100
    prompt_max_total_context_chars: int = 4200

    allow_hash_embedding_fallback: bool = True
    include_citations_default: bool = True
    observability_enabled: bool = True

    local_api_key: str = ''
    local_rate_limit_per_minute: int = 60
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    @field_validator('cors_origins', mode='before')
    @classmethod
    def _parse_cors_origins(cls, value: object) -> list[str]:
        if value is None or value == '':
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith('['):
                try:
                    data = json.loads(raw)
                    if isinstance(data, list):
                        return [str(item).strip() for item in data if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in raw.split(',') if item.strip()]
        raise TypeError('CORS_ORIGINS must be a JSON array or comma-separated string.')

    @field_validator('ollama_base_url')
    @classmethod
    def _normalize_url(cls, value: str) -> str:
        value = value.strip().rstrip('/')
        if not value.startswith('http://') and not value.startswith('https://'):
            raise ValueError('OLLAMA_BASE_URL must start with http:// or https://')
        return value

    @field_validator('index_chunk_size')
    @classmethod
    def _validate_chunk_size(cls, value: int) -> int:
        if value < 300:
            raise ValueError('INDEX_CHUNK_SIZE must be at least 300 for stable retrieval.')
        return value

    @field_validator('index_chunk_overlap')
    @classmethod
    def _validate_chunk_overlap(cls, value: int) -> int:
        if value < 0:
            raise ValueError('INDEX_CHUNK_OVERLAP must be non-negative.')
        return value

    @model_validator(mode='after')
    def _validate_ranges(self) -> 'Settings':
        if self.index_chunk_overlap >= self.index_chunk_size:
            raise ValueError('INDEX_CHUNK_OVERLAP must be smaller than INDEX_CHUNK_SIZE.')
        if self.retrieval_candidate_top_k < self.retrieval_top_k:
            raise ValueError('RETRIEVAL_CANDIDATE_TOP_K must be >= RETRIEVAL_TOP_K.')
        if self.retrieval_rerank_pool_k < self.retrieval_top_k:
            raise ValueError('RETRIEVAL_RERANK_POOL_K must be >= RETRIEVAL_TOP_K.')
        if abs((self.retrieval_keyword_weight + self.retrieval_vector_weight) - 1.0) > 1e-6:
            raise ValueError('RETRIEVAL_KEYWORD_WEIGHT + RETRIEVAL_VECTOR_WEIGHT must equal 1.0.')
        return self

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return path.resolve()


settings = Settings()
