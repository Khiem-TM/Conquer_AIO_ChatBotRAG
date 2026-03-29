from __future__ import annotations

from pydantic import BaseModel, Field

from .common import Citation


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description='User input question')
    top_k: int = Field(default=5, ge=1, le=20)
    include_citations: bool = Field(default=True)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    model: str
    latency_ms: int
    conversation_id: str | None = None
    mode: str = Field(default='document_qa')
    confidence: str = Field(default='medium')
    metadata: dict[str, object] = Field(default_factory=dict)

