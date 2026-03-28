"""API router for file upload endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, status

from app.shared.schemas import ApiResponse

router = APIRouter(prefix='/api/v1', tags=['upload'])

DATA_INPUT_DIR = Path('data_input')
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post(
    '/upload',
    response_model=ApiResponse,
    summary='Upload documents',
    description='Upload document files to data_input/ folder for later ingestion',
)
async def upload_files(files: list[UploadFile] = File(...)) -> ApiResponse:
    """
    Upload documents to the data_input/ directory.

    **Supported formats:** PDF, DOCX, TXT, MD

    **Response Example:**
    ```json
    {
      "success": true,
      "message": "Uploaded 2 file(s)",
      "data": {"files": ["report.pdf", "notes.txt"]}
    }
    ```
    """
    DATA_INPUT_DIR.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    for upload in files:
        if not upload.filename:
            continue

        ext = Path(upload.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Unsupported file type: {ext}. Allowed: {", ".join(ALLOWED_EXTENSIONS)}',
            )

        content = await upload.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f'File {upload.filename} exceeds 50 MB limit',
            )

        dest = DATA_INPUT_DIR / upload.filename
        dest.write_bytes(content)
        saved.append(upload.filename)

    return ApiResponse(
        success=True,
        message=f'Uploaded {len(saved)} file(s)',
        data={'files': saved},
    )
