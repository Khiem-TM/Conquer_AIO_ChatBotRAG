"""API router for ingest endpoints with status tracking."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.shared.configs import settings
from app.shared.schemas import ApiResponse
from app.shared.security import require_local_api_key
from app.shared.service_container import get_indexing_service
from app.shared.storage import ingest_status_store

router = APIRouter(prefix='/api/v1', tags=['ingest'])
DATA_INPUT_DIR = Path(settings.index_data_input_dir)


@router.post('/ingest', response_model=ApiResponse, dependencies=[Depends(require_local_api_key)])
async def start_ingest() -> ApiResponse:
    try:
        document_names = sorted(
            p.relative_to(DATA_INPUT_DIR).as_posix()
            for p in DATA_INPUT_DIR.rglob('*')
            if p.is_file() and not p.name.startswith('.')
        ) if DATA_INPUT_DIR.exists() else []
        ingest_id = ingest_status_store.create_ingest(document_names=document_names)
        ingest_status_store.update_status(ingest_id, 'processing', f'Đang ingest {len(document_names)} tài liệu local...')
        try:
            result = await get_indexing_service().sync_index()
            ingest_message = (
                f'Đã ingest {len(document_names)} tài liệu, tạo {result.total_chunks} chunk'
                if document_names
                else 'Không có tài liệu nào để ingest'
            )
            ingest_status_store.mark_done(ingest_id, ingest_message)
            return ApiResponse(
                success=True,
                message='Ingest completed',
                data={
                    'ingest_id': ingest_id,
                    'status': 'done',
                    'ingested_docs': len(document_names),
                    'ingested_chunks': result.total_chunks,
                    'updated_sources': result.updated_sources,
                    'deleted_sources': result.deleted_sources,
                    'document_names': document_names,
                    'message': ingest_message,
                },
            )
        except Exception as e:
            ingest_status_store.mark_failed(ingest_id, f'Error: {str(e)}')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Ingest error: {str(e)}')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to start ingest: {str(e)}')


@router.get('/ingest/status/{ingest_id}', response_model=ApiResponse, dependencies=[Depends(require_local_api_key)])
async def get_ingest_status(ingest_id: str) -> ApiResponse:
    ingest_status = ingest_status_store.get_status(ingest_id)
    if not ingest_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Ingest ID not found: {ingest_id}')
    return ApiResponse(success=True, message='OK', data=ingest_status.model_dump())


@router.get('/ingest/history', response_model=ApiResponse, dependencies=[Depends(require_local_api_key)])
async def list_ingest_history(limit: int = Query(default=20, ge=1, le=200)) -> ApiResponse:
    items = ingest_status_store.list_ingests(limit=limit)
    return ApiResponse(success=True, message='OK', data={'items': [item.model_dump() for item in items]})
