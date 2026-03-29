"""System/data-source status endpoints for frontend diagnostics."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status

from app.indexing.index_service import IndexNotReadyError
from app.shared.configs import settings
from app.shared.db import DB_PATH, app_state_db
from app.shared.schemas import ApiResponse
from app.shared.security import require_local_api_key
from app.shared.service_container import get_indexing_service
from app.shared.storage import history_store, ingest_status_store

router = APIRouter(prefix='/api/v1', tags=['system'])


def _safe_sqlite_count(query: str) -> int:
    try:
        with app_state_db._connect() as conn:
            cur = conn.execute(query)
            row = cur.fetchone()
            return int(row[0]) if row and row[0] is not None else 0
    except Exception:
        return 0


@router.get('/system/data-sources', response_model=ApiResponse, dependencies=[Depends(require_local_api_key)])
async def get_data_sources_status() -> ApiResponse:
    try:
        data_input_dir = Path(settings.index_data_input_dir)
        data_input_dir.mkdir(parents=True, exist_ok=True)
        doc_files = sorted(
            p.relative_to(data_input_dir).as_posix()
            for p in data_input_dir.rglob('*')
            if p.is_file() and not p.name.startswith('.')
        )
        try:
            snapshot = await get_indexing_service().get_index_snapshot()
        except IndexNotReadyError:
            snapshot = None
        response = {
            'vector_store': {
                'backend': settings.index_store_backend,
                'index_storage_path': settings.index_storage_path,
                'index_db_path': settings.index_db_path,
                'qdrant_path': settings.qdrant_path,
                'qdrant_collection': settings.qdrant_collection,
            },
            'documents': {
                'path': str(data_input_dir),
                'file_count': len(doc_files),
                'files': doc_files,
            },
            'models': {
                'generation_model': settings.ollama_model,
                'reranker_model': settings.ollama_reranker_model,
                'embedding_model': settings.embedding_model,
                'llm_reranker_enabled': settings.retrieval_enable_llm_reranker,
            },
            'index': {
                'ready': bool(snapshot),
                'built_at': snapshot.get('built_at') if snapshot else None,
                'chunk_count': len(snapshot.get('chunks', [])) if snapshot else 0,
                'source_count': len(snapshot.get('sources', {})) if snapshot else 0,
                'embedding_backend': snapshot.get('embedding_backend') if snapshot else 'pending',
                'chunker_version': snapshot.get('chunker_version') if snapshot else settings.index_chunker_version,
                'schema_version': snapshot.get('schema_version') if snapshot else settings.index_schema_version,
                'manifest': snapshot.get('manifest', {}) if snapshot else {},
            },
            'ingest_store': {
                'mode': 'sqlite',
                'count': ingest_status_store.get_count(),
                'sqlite': {
                    'enabled': DB_PATH.exists(),
                    'path': str(DB_PATH),
                    'count': _safe_sqlite_count('SELECT COUNT(*) FROM ingest_status'),
                },
            },
            'chat_store': {
                'mode': 'sqlite',
                'count': history_store.get_count(),
                'sqlite': {
                    'enabled': DB_PATH.exists(),
                    'path': str(DB_PATH),
                    'count': _safe_sqlite_count('SELECT COUNT(*) FROM chat_history'),
                },
            },
            'index_tables': {
                'sources': _safe_sqlite_count('SELECT COUNT(*) FROM index_sources'),
                'chunks': _safe_sqlite_count('SELECT COUNT(*) FROM index_chunks'),
                'runs': _safe_sqlite_count('SELECT COUNT(*) FROM index_runs'),
            },
        }
        return ApiResponse(success=True, message='OK', data=response)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to get data sources status: {exc}')
