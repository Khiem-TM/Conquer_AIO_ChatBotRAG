"""Main FastAPI application with integrated routers."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import chat, ingest_new, upload
from app.shared.configs import settings
from app.shared.schemas import HealthStatus
from app.shared.utils import configure_logging, get_logger

configure_logging(settings.log_level)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version='1.0.0',
    description='RAG Chatbot API with document ingestion and chat history',
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
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'success': False,
            'error': {
                'code': f'HTTP_{exc.status_code}',
                'message': exc.detail,
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
