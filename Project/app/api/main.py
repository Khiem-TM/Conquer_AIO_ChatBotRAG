from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.rag_core.chat_service import ChatService
from app.shared.configs import settings
from app.shared.schemas import ChatRequest, ChatResponse, HealthStatus
from app.shared.utils import configure_logging

configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

chat_service = ChatService()


@app.get('/health', response_model=HealthStatus, tags=['system'])
async def health_check() -> HealthStatus:
    return HealthStatus(
        status='ok',
        service=settings.app_name,
        model=settings.ollama_model,
        timestamp=datetime.now(timezone.utc),
    )


@app.post(f"{settings.api_prefix}/chat", response_model=ChatResponse, tags=['chat'])
async def chat(payload: ChatRequest) -> ChatResponse:
    return await chat_service.ask(payload)
