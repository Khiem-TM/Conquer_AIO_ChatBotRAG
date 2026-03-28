"""Chat-related data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message in history."""

    id: str = Field(..., description="Unique message ID")
    question: str = Field(..., description="User question")
    answer: str = Field(..., description="AI answer")
    timestamp: datetime = Field(..., description="Message timestamp")
    sources: list[dict] = Field(default_factory=list, description="Source citations")


class ChatRequest(BaseModel):
    """Request to ask a question."""

    question: str = Field(..., min_length=1, description="User question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of sources to retrieve")
    include_citations: bool = Field(default=True, description="Include citations in response")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""

    id: str = Field(..., description="Chat message ID")
    answer: str = Field(..., description="AI generated answer")
    sources: list[dict] = Field(default_factory=list, description="Source citations")
    timestamp: datetime = Field(..., description="Response timestamp")
    latency_ms: int = Field(..., description="Processing latency in milliseconds")
