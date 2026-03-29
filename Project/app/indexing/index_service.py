from __future__ import annotations

import asyncio
from typing import Any

from app.indexing.config import settings
from app.indexing.embeddings import EmbeddingService
from app.indexing.schemas import IndexOperationResult, IndexStatus
from app.indexing.vectorstore import LocalIndexStore, QdrantIndexStore, SQLiteIndexStore
from app.indexing.vectorstore.local_index_store import SourceDocument
from app.shared.utils import get_logger, timer

logger = get_logger(__name__)


class IndexNotReadyError(RuntimeError):
    """Raised when index snapshot is requested before index is built."""


class IndexingService:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        index_store: LocalIndexStore | None = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.index_store = index_store or self._create_store(settings.index_store_backend)
        self._lock = asyncio.Lock()

    def _create_store(self, backend: str) -> LocalIndexStore:
        if backend == 'sqlite':
            return SQLiteIndexStore()
        if backend == 'local_json':
            return LocalIndexStore()
        if backend == 'qdrant':
            return QdrantIndexStore()
        raise ValueError(f'Unsupported INDEX_STORE_BACKEND={backend!r}')

    async def get_status(self) -> IndexStatus:
        async with self._lock:
            index_data = self.index_store.load_index_data()
            return self.index_store.build_status_response(index_data)

    async def rebuild_index(self) -> IndexOperationResult:
        async with self._lock:
            with timer() as t:
                documents = self.index_store.collect_documents(self.index_store.scan_source_files())
                index_data = await self._build_index_data(documents, previous_index=None)
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
                current_documents = self.index_store.collect_documents(self.index_store.scan_source_files())
                current_source_map = {document.source_id: document for document in current_documents}
                current_source_ids = set(current_source_map.keys())
                existing_index = self.index_store.load_index_data()

                if not existing_index:
                    index_data = await self._build_index_data(current_documents, previous_index=None)
                    self.index_store.write_index_data(index_data)
                    return self.index_store.build_operation_response(
                        index_data=index_data,
                        message='Index created from current local documents.',
                        latency_ms=t.elapsed_ms,
                        updated_sources=sorted(index_data['sources'].keys()),
                        deleted_sources=[],
                    )

                if self._requires_full_rebuild(existing_index):
                    logger.info('Index metadata changed, rebuilding full local index.')
                    index_data = await self._build_index_data(current_documents, previous_index=None)
                    self.index_store.write_index_data(index_data)
                    return self.index_store.build_operation_response(
                        index_data=index_data,
                        message='Index rebuilt because configuration changed.',
                        latency_ms=t.elapsed_ms,
                        updated_sources=sorted(index_data['sources'].keys()),
                        deleted_sources=[],
                    )

                existing_sources = dict(existing_index.get('sources', {}))
                updated_source_ids = sorted(
                    source_id
                    for source_id, document in current_source_map.items()
                    if source_id not in existing_sources
                    or str(existing_sources[source_id].get('source_hash', '')) != document.source_hash
                )
                deleted_source_ids = sorted(source_id for source_id in existing_sources if source_id not in current_source_ids)

                if not updated_source_ids and not deleted_source_ids:
                    manifest = dict(existing_index.get('manifest', {}))
                    manifest['last_sync_at'] = self.index_store.utc_now()
                    existing_index['manifest'] = manifest
                    self.index_store.write_index_data(existing_index)
                    return self.index_store.build_operation_response(
                        index_data=existing_index,
                        message='Index is already up to date.',
                        latency_ms=t.elapsed_ms,
                        updated_sources=[],
                        deleted_sources=[],
                    )

                preserved_chunks = [
                    chunk
                    for chunk in existing_index.get('chunks', [])
                    if chunk['source_id'] not in updated_source_ids and chunk['source_id'] not in deleted_source_ids
                ]
                preserved_sources = {
                    source_id: payload
                    for source_id, payload in existing_sources.items()
                    if source_id not in updated_source_ids and source_id not in deleted_source_ids
                }

                updated_documents = [current_source_map[source_id] for source_id in updated_source_ids]
                rebuilt_chunk_list, embedding_backend, reused_vectors = await self._build_chunks_for_documents(
                    updated_documents,
                    previous_index=existing_index,
                )
                rebuilt_sources = self.index_store.build_sources_payload(updated_documents)
                for source_id, payload in rebuilt_sources.items():
                    payload['chunk_count'] = sum(1 for chunk in rebuilt_chunk_list if chunk['source_id'] == source_id)

                next_index = {
                    'schema_version': settings.index_schema_version,
                    'chunker_version': settings.index_chunker_version,
                    'embedding_backend': embedding_backend,
                    'embedding_model': settings.embedding_model,
                    'built_at': self.index_store.utc_now(),
                    'sources': {**preserved_sources, **rebuilt_sources},
                    'chunks': preserved_chunks + rebuilt_chunk_list,
                    'manifest': {
                        'updated_sources_count': len(updated_source_ids),
                        'deleted_sources_count': len(deleted_source_ids),
                        'reused_vectors': reused_vectors,
                        'last_sync_at': self.index_store.utc_now(),
                    },
                }
                self.index_store.write_index_data(next_index)

            return self.index_store.build_operation_response(
                index_data=next_index,
                message='Index synchronized with local documents.',
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
                    index_data['chunks'] = [chunk for chunk in index_data['chunks'] if chunk['source_id'] != source_id]
                    index_data['built_at'] = self.index_store.utc_now()
                    index_data['manifest'] = {
                        **dict(index_data.get('manifest', {})),
                        'deleted_sources_count': 1,
                        'last_sync_at': self.index_store.utc_now(),
                    }
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
            if not index_data:
                raise IndexNotReadyError('Index not built yet. Please run ingest/sync first.')

            if str(index_data.get('embedding_model', '')).strip() != str(settings.embedding_model).strip():
                raise IndexNotReadyError(
                    'Index embedding_model mismatch. Please rebuild/sync index with current embedding model.'
                )
            if int(index_data.get('schema_version', 0) or 0) != settings.index_schema_version:
                raise IndexNotReadyError('Index schema changed. Please rebuild/sync index.')
            if str(index_data.get('chunker_version', '')).strip() != settings.index_chunker_version:
                raise IndexNotReadyError('Index chunker changed. Please rebuild/sync index.')
            return index_data

    def _requires_full_rebuild(self, index_data: dict[str, Any]) -> bool:
        return (
            str(index_data.get('embedding_model', '')).strip() != str(settings.embedding_model).strip()
            or int(index_data.get('schema_version', 0) or 0) != settings.index_schema_version
            or str(index_data.get('chunker_version', '')).strip() != settings.index_chunker_version
        )

    async def _build_index_data(
        self,
        documents: list[SourceDocument],
        previous_index: dict[str, Any] | None,
    ) -> dict[str, Any]:
        chunks, embedding_backend, reused_vectors = await self._build_chunks_for_documents(documents, previous_index)
        sources_payload = self.index_store.build_sources_payload(documents)
        for source_id, payload in sources_payload.items():
            payload['chunk_count'] = sum(1 for chunk in chunks if chunk['source_id'] == source_id)

        return {
            'schema_version': settings.index_schema_version,
            'chunker_version': settings.index_chunker_version,
            'embedding_backend': embedding_backend,
            'embedding_model': settings.embedding_model,
            'built_at': self.index_store.utc_now(),
            'sources': sources_payload,
            'chunks': chunks,
            'manifest': {
                'reused_vectors': reused_vectors,
                'last_sync_at': self.index_store.utc_now(),
            },
        }

    async def _build_chunks_for_documents(
        self,
        documents: list[SourceDocument],
        previous_index: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], str, int]:
        raw_chunks, texts = self.index_store.prepare_chunk_records(documents)
        if not raw_chunks:
            return [], 'simple', 0

        previous_chunks = list(previous_index.get('chunks', [])) if previous_index else []
        previous_by_hash = {
            str(chunk.get('chunk_hash') or (chunk.get('metadata') or {}).get('chunk_hash') or ''): chunk
            for chunk in previous_chunks
            if str(chunk.get('chunk_hash') or (chunk.get('metadata') or {}).get('chunk_hash') or '')
        }

        reusable_backend = previous_index.get('embedding_backend', 'pending') if previous_index else 'pending'
        if previous_index and reusable_backend == 'ollama':
            preferred_backend = 'ollama'
        elif previous_index and reusable_backend == 'simple':
            preferred_backend = 'simple'
        else:
            preferred_backend = 'ollama'

        chunks_to_embed: list[dict[str, Any]] = []
        texts_to_embed: list[str] = []
        reused_vectors = 0

        for chunk in raw_chunks:
            previous_chunk = previous_by_hash.get(str(chunk.get('chunk_hash', '')))
            if previous_chunk is not None:
                chunk['vector'] = list(previous_chunk.get('vector', []))
                reused_vectors += 1
            else:
                chunks_to_embed.append(chunk)
                texts_to_embed.append(str(chunk.get('text', '')))

        if chunks_to_embed:
            vectors, embedding_backend = await self.embedding_service.embed_texts(texts_to_embed)
            for chunk, vector in zip(chunks_to_embed, vectors, strict=True):
                chunk['vector'] = vector
        else:
            embedding_backend = preferred_backend if preferred_backend in {'ollama', 'simple'} else 'simple'

        for chunk in raw_chunks:
            metadata = dict(chunk.get('metadata', {}) or {})
            metadata['token_count'] = len(str(chunk.get('text', '')).split())
            metadata['chunk_hash'] = chunk.get('chunk_hash')
            chunk['metadata'] = metadata

        return raw_chunks, embedding_backend, reused_vectors
