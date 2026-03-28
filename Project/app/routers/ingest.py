"""API router for ingest endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.models.ingest import IngestRequest, IngestResponse, IngestStatus
from app.models.common import ErrorResponse
from app.services.ingest import IngestService

router = APIRouter(prefix="/v1", tags=["ingest"])
ingest_service = IngestService()


@router.post(
    "/ingest",
    response_model=IngestResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Start document ingestion",
    description="Upload and process documents for indexing",
)
async def start_ingest(payload: IngestRequest) -> IngestResponse:
    """
    Start ingesting documents.

    **Example Request:**
    ```json
    {
      "documents": ["path/to/doc1.pdf", "path/to/doc2.md"]
    }
    ```

    **Example Response:**
    ```json
    {
      "ingest_id": "ing_abc123def456",
      "status": "processing",
      "timestamp": "2024-03-28T10:30:00",
      "message": "Processing 2 document(s)"
    }
    ```
    """
    try:
        if not payload.documents:
            raise ValueError("At least one document is required")

        # Start ingest operation
        ingest_id = ingest_service.start_ingest(len(payload.documents))

        # TODO: Trigger actual ingest in background (or simulate immediately)
        # For MVP, complete immediately
        ingest_service.complete_ingest(
            ingest_id,
            docs_processed=len(payload.documents),
            chunks_created=len(payload.documents) * 100,  # Simulated chunk count
        )

        status_response = ingest_service.get_status(ingest_id)
        if not status_response:
            raise Exception("Failed to create ingest operation")

        return IngestResponse(
            ingest_id=status_response.ingest_id,
            status=status_response.status,
            timestamp=status_response.timestamp,
            message=status_response.message,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                }
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INGEST_ERROR",
                    "message": str(e),
                }
            },
        )


@router.get(
    "/ingest/status/{ingest_id}",
    response_model=dict,
    responses={404: {"model": ErrorResponse}},
    summary="Check ingest status",
    description="Get the status of an ingest operation",
)
async def get_ingest_status(ingest_id: str) -> dict:
    """
    Get status of an ingest operation.

    **Path Parameters:**
    - `ingest_id`: The ingest operation ID

    **Example Response:**
    ```json
    {
      "ingest_id": "ing_abc123def456",
      "status": "done",
      "timestamp": "2024-03-28T10:30:15",
      "message": "Successfully processed 2 document(s) and created 200 chunk(s)",
      "docs_processed": 2,
      "chunks_created": 200
    }
    ```
    """
    status = ingest_service.get_status(ingest_id)

    if status is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Ingest operation '{ingest_id}' not found",
                }
            },
        )

    return status.model_dump()
