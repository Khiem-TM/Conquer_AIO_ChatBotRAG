from __future__ import annotations

import os
from dataclasses import dataclass


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class IndexingSettings:
    ollama_base_url: str = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
    embedding_model: str = os.getenv('EMBEDDING_MODEL', 'llama3.1:8b')
    request_timeout_seconds: int = _get_int_env('REQUEST_TIMEOUT_SECONDS', 120)
    data_input_dir: str = os.getenv('INDEX_DATA_INPUT_DIR', 'data_input')
    index_storage_path: str = os.getenv('INDEX_STORAGE_PATH', 'data/index_store.json')
    embedding_dimensions: int = _get_int_env('EMBEDDING_DIMENSIONS', 128)
    index_chunk_size: int = _get_int_env('INDEX_CHUNK_SIZE', 900)
    index_chunk_overlap: int = _get_int_env('INDEX_CHUNK_OVERLAP', 120)


settings = IndexingSettings()
