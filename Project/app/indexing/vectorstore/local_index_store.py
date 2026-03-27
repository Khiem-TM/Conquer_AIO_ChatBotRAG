from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.indexing.config import settings
from app.indexing.schemas import IndexOperationResult, IndexStatus
from app.shared.utils import get_logger

logger = get_logger(__name__)


class LocalIndexStore:
    def __init__(self) -> None:
        self._index_data: dict[str, Any] | None = None
        self._project_dir = Path(__file__).resolve().parents[3]

    def load_index_data(self) -> dict[str, Any] | None:
        if self._index_data is not None:
            return self._index_data

        storage_path = self.get_storage_path()
        if not storage_path.exists():
            return None

        self._index_data = json.loads(storage_path.read_text(encoding='utf-8'))
        return self._index_data

    def write_index_data(self, index_data: dict[str, Any]) -> None:
        storage_path = self.get_storage_path()
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(json.dumps(index_data, ensure_ascii=False, indent=2), encoding='utf-8')
        self._index_data = index_data

    def scan_source_files(self) -> list[Path]:
        data_input_dir = self.get_data_input_dir()
        if not data_input_dir.exists():
            logger.warning('data_input directory does not exist: %s', data_input_dir)
            return []

        return [
            file_path
            for file_path in sorted(data_input_dir.rglob('*'))
            if file_path.is_file()
            and file_path.suffix.lower() in {'.md', '.txt'}
            and not file_path.name.startswith('~$')
        ]

    def prepare_chunk_records(self, source_files: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
        raw_chunks: list[dict[str, Any]] = []
        texts: list[str] = []

        for file_path in source_files:
            text = self.read_source_text(file_path)
            if not text:
                continue

            chunks = self.split_text(text)
            source_id = self.build_source_id(file_path)
            for index, chunk_text in enumerate(chunks, start=1):
                cleaned_text = chunk_text.strip()
                if not cleaned_text:
                    continue

                raw_chunks.append(
                    {
                        'source_id': source_id,
                        'source_name': file_path.name,
                        'chunk_id': f'{source_id}_chunk_{index:03d}',
                        'text': cleaned_text,
                    }
                )
                texts.append(cleaned_text)

        return raw_chunks, texts

    def build_sources_payload(self, source_files: list[Path]) -> dict[str, dict[str, Any]]:
        return {
            self.build_source_id(file_path): {
                'source_name': file_path.name,
                'file_path': str(file_path),
                'updated_at_ns': file_path.stat().st_mtime_ns,
            }
            for file_path in source_files
        }

    def build_status_response(self, index_data: dict[str, Any] | None) -> IndexStatus:
        if not index_data:
            return IndexStatus(embedding_model=settings.embedding_model)

        return IndexStatus(
            ready=bool(index_data.get('chunks')),
            embedding_backend=index_data.get('embedding_backend', 'pending'),
            embedding_model=index_data.get('embedding_model', settings.embedding_model),
            total_sources=len(index_data.get('sources', {})),
            total_chunks=len(index_data.get('chunks', [])),
            built_at=index_data.get('built_at'),
        )

    def build_operation_response(
        self,
        index_data: dict[str, Any],
        message: str,
        latency_ms: int,
        updated_sources: list[str],
        deleted_sources: list[str],
    ) -> IndexOperationResult:
        status_response = self.build_status_response(index_data)
        return IndexOperationResult(
            ready=status_response.ready,
            embedding_backend=status_response.embedding_backend,
            embedding_model=status_response.embedding_model,
            total_sources=status_response.total_sources,
            total_chunks=status_response.total_chunks,
            built_at=status_response.built_at,
            message=message,
            latency_ms=latency_ms,
            updated_sources=updated_sources,
            deleted_sources=deleted_sources,
        )

    def empty_index_data(self) -> dict[str, Any]:
        return {
            'embedding_backend': 'pending',
            'embedding_model': settings.embedding_model,
            'built_at': None,
            'sources': {},
            'chunks': [],
        }

    def build_source_id(self, file_path: Path) -> str:
        relative_path = file_path.relative_to(self.get_data_input_dir()).as_posix()
        return relative_path.replace('/', '__')

    def read_source_text(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding='utf-8').strip()
        except UnicodeDecodeError:
            return file_path.read_text(encoding='utf-8', errors='ignore').strip()

    def split_text(self, text: str) -> list[str]:
        blocks = [block.strip() for block in re.split(r'\n\s*\n', text) if block.strip()]
        chunks: list[str] = []
        current_chunk = ''

        for block in blocks:
            next_chunk = f'{current_chunk}\n\n{block}'.strip() if current_chunk else block
            if len(next_chunk) <= settings.index_chunk_size:
                current_chunk = next_chunk
                continue

            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ''

            if len(block) <= settings.index_chunk_size:
                current_chunk = block
                continue

            chunks.extend(self.split_long_block(block))

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def split_long_block(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        chunk_size = max(100, settings.index_chunk_size)
        overlap = max(0, min(settings.index_chunk_overlap, chunk_size // 2))

        while start < len(text):
            end = min(len(text), start + chunk_size)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start = max(start + 1, end - overlap)

        return chunks

    def get_data_input_dir(self) -> Path:
        return self.resolve_path(settings.data_input_dir)

    def get_storage_path(self) -> Path:
        return self.resolve_path(settings.index_storage_path)

    def utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (self._project_dir / path).resolve()
