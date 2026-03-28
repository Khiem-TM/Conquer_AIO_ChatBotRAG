from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = True
    message: str = 'OK'
    data: Any | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: dict[str, str] = Field(
        default_factory=lambda: {
            'code': 'INTERNAL_ERROR',
            'message': 'Unexpected server error',
        }
    )

    class Config:
        json_schema_extra = {
            'example': {
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Question must be at least 1 character',
                },
            }
        }


class Citation(BaseModel):
    source_id: str = Field(..., description='Unique source/document identifier')
    source_name: str | None = Field(default=None, description='Human-readable source name')
    chunk_id: str | None = Field(default=None, description='Retrieved chunk id')
    score: float | None = Field(default=None, description='Retrieval similarity score')
    snippet: str | None = Field(default=None, description='Short supporting text snippet')


class HealthStatus(BaseModel):
    status: str = 'ok'
    service: str = 'rag-chatbot-api'
    model: str
    timestamp: datetime

