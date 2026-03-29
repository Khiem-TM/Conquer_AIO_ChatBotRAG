"""Main FastAPI application with integrated routers."""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import chat, ingest_new, system, upload
from app.shared.configs import settings
from app.shared.schemas import HealthStatus
from app.shared.utils import configure_logging, get_logger

configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: tự động sync index nếu thư mục data_input có file."""
    try:
        from app.shared.service_container import get_indexing_service
        data_input = Path(settings.index_data_input_dir)
        has_files = data_input.exists() and any(
            p for p in data_input.rglob('*') if p.is_file() and not p.name.startswith('.')
        )
        if has_files:
            logger.info('Startup: phát hiện file trong data_input, đang auto-sync index...')
            result = await get_indexing_service().sync_index()
            logger.info(
                'Startup index sync xong: %d sources, %d chunks.',
                result.total_sources, result.total_chunks,
            )
        else:
            logger.info('Startup: data_input trống, bỏ qua auto-sync.')
    except Exception as exc:
        logger.warning('Startup auto-sync thất bại (không gây crash): %s', exc)
    yield


app = FastAPI(
    title=settings.app_name,
    version='1.1.0',
    description='Local-first RAG Chatbot API with SQLite indexing and Ollama',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    _ = request
    detail = exc.detail
    if isinstance(detail, dict):
        message = str(detail.get('message', 'Unexpected error'))
        code = str(detail.get('code', f'HTTP_{exc.status_code}'))
        extra = {k: v for k, v in detail.items() if k not in {'message', 'code'}}
    else:
        message = str(detail)
        code = f'HTTP_{exc.status_code}'
        extra = {}
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'success': False,
            'error': {
                'code': code,
                'message': message,
                **extra,
            },
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    _ = request
    logger.exception('Unhandled exception: %s', exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred',
            },
        },
    )


@app.get('/health', response_model=HealthStatus, tags=['system'])
async def health_check() -> HealthStatus:
    return HealthStatus(
        status='ok',
        service=settings.app_name,
        model=settings.ollama_model,
        timestamp=datetime.now(timezone.utc),
    )


app.include_router(chat.router)
app.include_router(ingest_new.router)
app.include_router(upload.router)
app.include_router(system.router)
