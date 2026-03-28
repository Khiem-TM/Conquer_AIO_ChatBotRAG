"""API router for ingest endpoints with status tracking."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from app.data_ingest import IngestService
from app.shared.schemas import ApiResponse, IngestStatus
from app.shared.storage import ingest_status_store

router = APIRouter(prefix='/api/v1', tags=['ingest'])
ingest_service = IngestService(data_input_dir='data_input')


@router.post(
    '/ingest',
    response_model=ApiResponse,
    summary='Start document ingestion',
    description='Upload and process documents for indexing',
)
async def start_ingest() -> ApiResponse:
    """
    Start ingesting documents.

    This endpoint triggers document ingestion from the `data_input/` directory.
    It returns an `ingest_id` which can be used to track progress.

    **Response Example:**
    ```json
    {
      "success": true,
      "message": "Ingest started",
      "data": {
        "ingest_id": "ingest_550e8400-e29b-41d4",
        "status": "processing"
      }
    }
    ```

    **Next Steps:**
    1. Call `GET /api/v1/ingest/status/{ingest_id}` to check progress
    2. Once status is "done", documents are ready for chat
    """
    try:
        # Create new ingest job
        ingest_id = ingest_status_store.create_ingest()

        # Mark as processing
        ingest_status_store.update_status(ingest_id, 'processing', 'Starting ingestion...')

        # Run ingest (blocking for MVP, could be async later)
        try:
            result = ingest_service.run()
            ingest_status_store.mark_done(
                ingest_id,
                f'Ingested {result.ingested_docs} documents, {result.ingested_chunks} chunks',
            )
            return ApiResponse(
                success=True,
                message='Ingest completed',
                data={
                    'ingest_id': ingest_id,
                    'status': 'done',
                    'ingested_docs': result.ingested_docs,
                    'ingested_chunks': result.ingested_chunks,
                },
            )
        except Exception as e:
            ingest_status_store.mark_failed(ingest_id, f'Error: {str(e)}')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Ingest error: {str(e)}',
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to start ingest: {str(e)}',
        )


@router.get(
    '/ingest/status/{ingest_id}',
    response_model=ApiResponse,
    summary='Get ingest status',
    description='Check the status of an ingest job',
)
async def get_ingest_status(ingest_id: str) -> ApiResponse:
    """
    Get the status of an ingest job.

    **Path Parameters:**
    - `ingest_id`: ID returned from POST /ingest endpoint

    **Response Example:**
    ```json
    {
      "success": true,
      "message": "OK",
      "data": {
        "ingest_id": "ingest_550e8400-e29b-41d4",
        "status": "done",
        "message": "Ingested 5 documents, 1240 chunks",
        "created_at": "2024-01-15T10:00:00Z",
        "completed_at": "2024-01-15T10:05:00Z"
      }
    }
    ```

    **Status Values:**
    - `pending`: Job created, waiting to start
    - `processing`: Actively ingesting documents
    - `done`: Ingest completed successfully
    - `failed`: Ingest failed with error
    """
    try:
        ingest_status = ingest_status_store.get_status(ingest_id)

        if not ingest_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Ingest ID not found: {ingest_id}',
            )

        return ApiResponse(
            success=True,
            message='OK',
            data=ingest_status.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error retrieving ingest status: {str(e)}',
        )
