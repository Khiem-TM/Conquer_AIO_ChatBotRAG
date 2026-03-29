"""Chat history and ingest status schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatHistoryEntry(BaseModel):
    """Single chat history entry."""

    id: str = Field(..., description='Unique message ID')
    question: str = Field(..., description='User question')
    answer: str = Field(..., description='AI response')
    timestamp: datetime = Field(..., description='When message was created')

    class Config:
        json_schema_extra = {
            'example': {
                'id': 'msg_550e8400-e29b-41d4-a716-446655440000',
                'question': 'What is Anscombe quartet?',
                'answer': 'Anscombe quartet demonstrates...',
                'timestamp': '2024-01-15T10:30:00Z',
            }
        }


class IngestStatus(BaseModel):
    """Ingest job status."""

    ingest_id: str = Field(..., description='Unique ingest ID')
    status: str = Field(
        ..., description='Status of ingest: pending, processing, done, failed'
    )
    message: str | None = Field(default=None, description='Status message')
    created_at: datetime = Field(..., description='When ingest started')
    completed_at: datetime | None = Field(default=None, description='When ingest finished')
    document_names: list[str] = Field(
        default_factory=list, description='Uploaded document names for this ingest'
    )

    class Config:
        json_schema_extra = {
            'example': {
                'ingest_id': 'ingest_550e8400-e29b-41d4-a716-446655440000',
                'status': 'done',
                'message': '5 documents ingested, 1240 chunks created',
                'created_at': '2024-01-15T10:00:00Z',
                'completed_at': '2024-01-15T10:05:00Z',
            }
        }
