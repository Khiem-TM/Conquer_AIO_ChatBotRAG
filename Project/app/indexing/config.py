from __future__ import annotations

"""Cấu hình riêng cho phần indexing của người 2.

File này được tách riêng để phần `app/indexing` có thể chạy độc lập, không phải
phụ thuộc vào config chung của API hay RAG Core. Khi merge code, cách làm này
giúp giảm khả năng conflict với phần của các thành viên khác.
"""

import os
from dataclasses import dataclass


def _get_int_env(name: str, default: int) -> int:
    """Đọc một biến môi trường và ép về kiểu `int`.

    Hàm này được dùng cho các cấu hình số như:
    - thời gian timeout
    - số chiều embedding fallback
    - kích thước chunk
    - độ dài overlap giữa các chunk

    Nếu biến môi trường không tồn tại hoặc giá trị không hợp lệ, hàm sẽ trả về
    `default` để chương trình vẫn chạy ổn định thay vì lỗi ngay từ lúc khởi động.
    """

    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class IndexingSettings:
    """Nhóm toàn bộ setting cần thiết cho lane Embedding + Indexing.

    Mỗi thuộc tính trong class này đại diện cho một cấu hình mà người 2 cần để:
    - đọc dữ liệu đầu vào
    - gọi Ollama để tạo embedding
    - chia chunk
    - lưu index (local JSON hoặc Qdrant)

    Dùng `dataclass(frozen=True)` để thể hiện đây là cấu hình chỉ đọc sau khi
    được khởi tạo, tránh việc bị sửa lung tung trong quá trình chạy.
    """

    ollama_base_url: str = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
    embedding_model: str = os.getenv('EMBEDDING_MODEL', os.getenv('OLLAMA_MODEL', 'llama3.2:3b'))
    request_timeout_seconds: int = _get_int_env('REQUEST_TIMEOUT_SECONDS', 120)
    data_input_dir: str = os.getenv('INDEX_DATA_INPUT_DIR', 'data_input')
    index_storage_path: str = os.getenv('INDEX_STORAGE_PATH', 'data/index_store.json')

    # index_store_backend: "local" | "qdrant"
    index_store_backend: str = os.getenv('INDEX_STORE_BACKEND', 'qdrant').strip().lower()
    qdrant_path: str = os.getenv('QDRANT_PATH', 'data/qdrant')
    qdrant_collection: str = os.getenv('QDRANT_COLLECTION', 'rag_chunks')

    embedding_dimensions: int = _get_int_env('EMBEDDING_DIMENSIONS', 128)
    index_chunk_size: int = _get_int_env('INDEX_CHUNK_SIZE', 900)
    index_chunk_overlap: int = _get_int_env('INDEX_CHUNK_OVERLAP', 120)


# Đây là object config dùng chung cho toàn bộ package `app/indexing`.
settings = IndexingSettings()
