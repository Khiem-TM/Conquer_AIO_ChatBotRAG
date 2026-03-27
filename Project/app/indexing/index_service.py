from __future__ import annotations

import asyncio
from typing import Any

from app.indexing.config import settings
from app.indexing.embeddings import EmbeddingService
from app.indexing.schemas import IndexOperationResult, IndexStatus
from app.indexing.vectorstore import LocalIndexStore
from app.shared.utils import get_logger, timer

logger = get_logger(__name__)


class IndexingService:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        index_store: LocalIndexStore | None = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.index_store = index_store or LocalIndexStore()
        self._lock = asyncio.Lock()

    async def get_status(self) -> IndexStatus:
        async with self._lock:
            index_data = self.index_store.load_index_data()
            return self.index_store.build_status_response(index_data)

    async def rebuild_index(self) -> IndexOperationResult:
        async with self._lock:
            with timer() as t:
                source_files = self.index_store.scan_source_files()
                index_data = await self._build_index_data(source_files)
                self.index_store.write_index_data(index_data)

            return self.index_store.build_operation_response(
                index_data=index_data,
                message='Index rebuilt successfully.',
                latency_ms=t.elapsed_ms,
                updated_sources=sorted(index_data['sources'].keys()),
                deleted_sources=[],
            )

    async def sync_index(self) -> IndexOperationResult:
        async with self._lock:
            with timer() as t:
                current_files = self.index_store.scan_source_files()
                current_source_map = {
                    self.index_store.build_source_id(file_path): file_path for file_path in current_files
                }
                index_data = self.index_store.load_index_data()

                if not index_data:
                    index_data = await self._build_index_data(current_files)
                    self.index_store.write_index_data(index_data)
                    return self.index_store.build_operation_response(
                        index_data=index_data,
                        message='Index created from current data_input files.',
                        latency_ms=t.elapsed_ms,
                        updated_sources=sorted(index_data['sources'].keys()),
                        deleted_sources=[],
                    )

                if index_data.get('embedding_model') != settings.embedding_model:
                    logger.info('Embedding model changed, rebuilding index from scratch.')
                    index_data = await self._build_index_data(current_files)
                    self.index_store.write_index_data(index_data)
                    return self.index_store.build_operation_response(
                        index_data=index_data,
                        message='Index rebuilt because embedding_model changed.',
                        latency_ms=t.elapsed_ms,
                        updated_sources=sorted(index_data['sources'].keys()),
                        deleted_sources=[],
                    )

                existing_sources = index_data.get('sources', {})
                updated_source_ids = sorted(
                    source_id
                    for source_id, file_path in current_source_map.items()
                    if source_id not in existing_sources
                    or existing_sources[source_id].get('updated_at_ns') != file_path.stat().st_mtime_ns
                )
                deleted_source_ids = sorted(
                    source_id for source_id in existing_sources.keys() if source_id not in current_source_map
                )

                if not updated_source_ids and not deleted_source_ids:
                    return self.index_store.build_operation_response(
                        index_data=index_data,
                        message='Index is already up to date.',
                        latency_ms=t.elapsed_ms,
                        updated_sources=[],
                        deleted_sources=[],
                    )

                preserved_chunks = [
                    chunk
                    for chunk in index_data.get('chunks', [])
                    if chunk['source_id'] not in updated_source_ids and chunk['source_id'] not in deleted_source_ids
                ]

                rebuilt_chunks: list[dict[str, Any]] = []
                rebuilt_sources: dict[str, dict[str, Any]] = {}
                if updated_source_ids:
                    updated_files = [current_source_map[source_id] for source_id in updated_source_ids]
                    raw_chunks, texts = self.index_store.prepare_chunk_records(updated_files)
                    if raw_chunks:
                        vectors, rebuilt_backend = await self.embedding_service.embed_texts(texts)
                        for chunk, vector in zip(raw_chunks, vectors, strict=True):
                            chunk['vector'] = vector
                        rebuilt_chunks = raw_chunks
                    else:
                        rebuilt_backend = index_data.get('embedding_backend', 'simple')

                    existing_backend = index_data.get('embedding_backend', 'pending')
                    if preserved_chunks and existing_backend != rebuilt_backend:
                        logger.info('Embedding backend changed during sync, rebuilding full index.')
                        index_data = await self._build_index_data(current_files)
                        self.index_store.write_index_data(index_data)
                        return self.index_store.build_operation_response(
                            index_data=index_data,
                            message='Index rebuilt because embedding backend changed.',
                            latency_ms=t.elapsed_ms,
                            updated_sources=sorted(index_data['sources'].keys()),
                            deleted_sources=[],
                        )

                    rebuilt_sources = self.index_store.build_sources_payload(updated_files)
                    index_data['embedding_backend'] = rebuilt_backend

                next_sources = {
                    source_id: payload
                    for source_id, payload in existing_sources.items()
                    if source_id not in updated_source_ids and source_id not in deleted_source_ids
                }
                next_sources.update(rebuilt_sources)

                index_data['sources'] = next_sources
                index_data['chunks'] = preserved_chunks + rebuilt_chunks
                index_data['built_at'] = self.index_store.utc_now()
                self.index_store.write_index_data(index_data)

            return self.index_store.build_operation_response(
                index_data=index_data,
                message='Index synchronized with data_input.',
                latency_ms=t.elapsed_ms,
                updated_sources=updated_source_ids,
                deleted_sources=deleted_source_ids,
            )

    async def delete_source(self, source_id: str) -> IndexOperationResult:
        async with self._lock:
            with timer() as t:
                index_data = self.index_store.load_index_data() or self.index_store.empty_index_data()
                deleted_sources: list[str] = []
                if source_id in index_data['sources']:
                    index_data['sources'].pop(source_id, None)
                    index_data['chunks'] = [
                        chunk for chunk in index_data['chunks'] if chunk['source_id'] != source_id
                    ]
                    index_data['built_at'] = self.index_store.utc_now()
                    self.index_store.write_index_data(index_data)
                    deleted_sources = [source_id]

            message = 'Source deleted from index.' if deleted_sources else 'Source was not found in index.'
            return self.index_store.build_operation_response(
                index_data=index_data,
                message=message,
                latency_ms=t.elapsed_ms,
                updated_sources=[],
                deleted_sources=deleted_sources,
            )

    async def get_index_snapshot(self) -> dict[str, Any]:
        async with self._lock:
            index_data = self.index_store.load_index_data()
            if not index_data or index_data.get('embedding_model') != settings.embedding_model:
                source_files = self.index_store.scan_source_files()
                index_data = await self._build_index_data(source_files)
                self.index_store.write_index_data(index_data)
            return index_data

    async def _build_index_data(self, source_files: list[Any]) -> dict[str, Any]:
        raw_chunks, texts = self.index_store.prepare_chunk_records(source_files)
        if raw_chunks:
            vectors, embedding_backend = await self.embedding_service.embed_texts(texts)
            for chunk, vector in zip(raw_chunks, vectors, strict=True):
                chunk['vector'] = vector
        else:
            embedding_backend = 'simple'

        return {
            'embedding_backend': embedding_backend,
            'embedding_model': settings.embedding_model,
            'built_at': self.index_store.utc_now(),
            'sources': self.index_store.build_sources_payload(source_files),
            'chunks': raw_chunks,
        }
