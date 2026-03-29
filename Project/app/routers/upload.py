"""API router for file upload endpoints."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.shared.configs import settings
from app.shared.schemas import ApiResponse
from app.shared.security import require_local_api_key
from app.shared.service_container import get_indexing_service

router = APIRouter(prefix='/api/v1', tags=['upload'])
DATA_INPUT_DIR = Path(settings.index_data_input_dir)
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}
ALLOWED_CONTENT_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown',
    'application/octet-stream',
}
MAX_FILE_SIZE = 50 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


def sanitize_filename(filename: str) -> str:
    name = unicodedata.normalize('NFC', Path(filename).name)
    name = name.replace('/', '_').replace('\\', '_')
    name = re.sub(r'[\x00-\x1f\x7f]+', '', name)
    name = re.sub(r'\s+', ' ', name).strip().strip('.')
    if not name or name in {'.', '..'}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid filename')
    # Guard against OS filename length limits (most filesystems cap at 255 bytes)
    if len(name.encode('utf-8')) > 200:
        stem = Path(name).stem
        suffix = Path(name).suffix
        budget = 200 - len(suffix.encode('utf-8'))
        name = stem.encode('utf-8')[:budget].decode('utf-8', errors='ignore') + suffix
    return name


@router.post('/upload', response_model=ApiResponse, dependencies=[Depends(require_local_api_key)])
async def upload_files(files: list[UploadFile] = File(...)) -> ApiResponse:
    DATA_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for upload in files:
        if not upload.filename:
            continue
        safe_name = sanitize_filename(upload.filename)
        ext = Path(safe_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Unsupported file type: {ext}. Allowed: {", ".join(sorted(ALLOWED_EXTENSIONS))}',
            )
        if upload.content_type and upload.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Unsupported content type: {upload.content_type}',
            )
        dest = DATA_INPUT_DIR / safe_name
        size = 0
        with dest.open('wb') as f:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    f.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f'File {safe_name} exceeds 50 MB limit',
                    )
                f.write(chunk)
        saved.append(safe_name)
        await upload.close()
    return ApiResponse(success=True, message=f'Uploaded {len(saved)} file(s)', data={'files': saved})


@router.get('/documents', response_model=ApiResponse, dependencies=[Depends(require_local_api_key)])
async def list_documents() -> ApiResponse:
    DATA_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(
        p.relative_to(DATA_INPUT_DIR).as_posix()
        for p in DATA_INPUT_DIR.rglob('*')
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS and not p.name.startswith('.')
    )
    return ApiResponse(success=True, message='OK', data={'files': files})


@router.delete('/documents/{filename:path}', response_model=ApiResponse, dependencies=[Depends(require_local_api_key)])
async def delete_document(filename: str) -> ApiResponse:
    DATA_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(Path(filename).name)
    target = DATA_INPUT_DIR / safe_name
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='File not found')
    if target.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Unsupported file type')
    target.unlink()
    sync_result = await get_indexing_service().sync_index()
    return ApiResponse(
        success=True,
        message='Deleted',
        data={'filename': safe_name, 'deleted_sources': sync_result.deleted_sources},
    )
