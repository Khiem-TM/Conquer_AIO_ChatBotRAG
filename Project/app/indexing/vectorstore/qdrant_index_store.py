from __future__ import annotations

import json
from hashlib import sha1
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.indexing.config import settings
from app.indexing.vectorstore.local_index_store import LocalIndexStore
from app.shared.utils import get_logger

logger = get_logger(__name__)


class QdrantIndexStore(LocalIndexStore):
    """Qdrant-backed store, giữ nguyên contract cũ của LocalIndexStore."""

    def __init__(self) -> None:
        super().__init__()
        qdrant_path = self.resolve_path(settings.qdrant_path)
        qdrant_path.mkdir(parents=True, exist_ok=True)
        self._client = QdrantClient(path=str(qdrant_path))
        self._collection = settings.qdrant_collection

    def load_index_data(self) -> dict[str, Any] | None:
        meta = self._load_meta()
        if not self._client.collection_exists(self._collection):
            return meta

        chunks: list[dict[str, Any]] = []
        offset = None
        while True:
            points, offset = self._client.scroll(
                collection_name=self._collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=True,
            )
            for point in points:
                payload = point.payload or {}
                chunks.append(
                    {
                        'source_id': payload.get('source_id', ''),
                        'source_name': payload.get('source_name', ''),
                        'chunk_id': payload.get('chunk_id', ''),
                        'text': payload.get('text', ''),
                        'metadata': payload.get('metadata', {}),
                        'vector': list(point.vector or []),
                    }
                )
            if offset is None:
                break

        if meta is None:
            meta = self.empty_index_data()
        meta['chunks'] = chunks
        return meta

    def write_index_data(self, index_data: dict[str, Any]) -> None:
        chunks = index_data.get('chunks', [])
        vector_size = self._vector_size(chunks)

        if self._client.collection_exists(self._collection):
            self._client.delete_collection(self._collection)

        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

        points: list[PointStruct] = []
        for chunk in chunks:
            chunk_id = str(chunk.get('chunk_id', ''))
            vector = list(chunk.get('vector', []))
            payload = {
                'source_id': chunk.get('source_id', ''),
                'source_name': chunk.get('source_name', ''),
                'chunk_id': chunk_id,
                'text': chunk.get('text', ''),
                'metadata': chunk.get('metadata', {}),
            }
            points.append(PointStruct(id=self._stable_int_id(chunk_id), vector=vector, payload=payload))

        if points:
            self._client.upsert(collection_name=self._collection, points=points)

        self._save_meta(index_data)
        self._index_data = index_data

    def _vector_size(self, chunks: list[dict[str, Any]]) -> int:
        for chunk in chunks:
            vector = chunk.get('vector', [])
            if isinstance(vector, list) and vector:
                return len(vector)
        return max(8, settings.embedding_dimensions)

    def _stable_int_id(self, chunk_id: str) -> int:
        digest = sha1(chunk_id.encode('utf-8')).hexdigest()[:15]
        return int(digest, 16)

    def _load_meta(self) -> dict[str, Any] | None:
        meta_path = self.get_storage_path()
        if not meta_path.exists():
            return None
        try:
            data = json.loads(meta_path.read_text(encoding='utf-8'))
            data['chunks'] = []
            return data
        except Exception as exc:
            logger.warning('Failed to read index metadata from %s: %s', meta_path, exc)
            return None

    def _save_meta(self, index_data: dict[str, Any]) -> None:
        meta_path = self.get_storage_path()
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_only = {
            'embedding_backend': index_data.get('embedding_backend', 'pending'),
            'embedding_model': index_data.get('embedding_model', settings.embedding_model),
            'built_at': index_data.get('built_at'),
            'sources': index_data.get('sources', {}),
            'chunks': [],
        }
        meta_path.write_text(json.dumps(metadata_only, ensure_ascii=False, indent=2), encoding='utf-8')

