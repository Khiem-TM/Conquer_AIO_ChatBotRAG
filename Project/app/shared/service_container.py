from __future__ import annotations

from app.indexing.index_service import IndexingService
from app.indexing.vectorstore import LocalIndexStore, SQLiteIndexStore, QdrantIndexStore
from app.rag_core.chat_service import ChatService
from app.shared.configs import settings

_indexing_service: IndexingService | None = None
_chat_service: ChatService | None = None


def _build_store():
    if settings.index_store_backend == 'sqlite':
        return SQLiteIndexStore()
    if settings.index_store_backend == 'local_json':
        return LocalIndexStore()
    if settings.index_store_backend == 'qdrant':
        return QdrantIndexStore()
    raise ValueError(f'Unsupported INDEX_STORE_BACKEND={settings.index_store_backend!r}')


def get_indexing_service() -> IndexingService:
    global _indexing_service
    if _indexing_service is None:
        _indexing_service = IndexingService(index_store=_build_store())
    return _indexing_service


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(indexing_service=get_indexing_service())
    return _chat_service
