from __future__ import annotations

"""Backward-compatible shim cho lane indexing.

Giữ lại `from app.indexing.config import settings` để tránh sửa hàng loạt import,
nhưng toàn bộ giá trị đều được lấy từ `app.shared.configs.settings`.
"""

from app.shared.configs import settings as _shared_settings


class _IndexingSettingsShim:
    @property
    def ollama_base_url(self) -> str:
        return _shared_settings.ollama_base_url

    @property
    def embedding_model(self) -> str:
        return _shared_settings.embedding_model

    @property
    def request_timeout_seconds(self) -> int:
        return _shared_settings.request_timeout_seconds

    @property
    def data_input_dir(self) -> str:
        return _shared_settings.index_data_input_dir

    @property
    def index_storage_path(self) -> str:
        return _shared_settings.index_storage_path

    @property
    def index_store_backend(self) -> str:
        return _shared_settings.index_store_backend

    @property
    def qdrant_path(self) -> str:
        return _shared_settings.qdrant_path

    @property
    def qdrant_collection(self) -> str:
        return _shared_settings.qdrant_collection

    @property
    def embedding_dimensions(self) -> int:
        return _shared_settings.embedding_dimensions

    @property
    def index_chunk_size(self) -> int:
        return _shared_settings.index_chunk_size

    @property
    def index_chunk_overlap(self) -> int:
        return _shared_settings.index_chunk_overlap


settings = _IndexingSettingsShim()
