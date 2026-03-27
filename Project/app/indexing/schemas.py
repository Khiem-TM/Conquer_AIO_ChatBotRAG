from __future__ import annotations

from pydantic import BaseModel, Field


class IndexStatus(BaseModel):
    ready: bool = False
    embedding_backend: str = 'pending'
    embedding_model: str
    total_sources: int = 0
    total_chunks: int = 0
    built_at: str | None = None


class IndexOperationResult(IndexStatus):
    message: str = 'Index updated'
    latency_ms: int = 0
    updated_sources: list[str] = Field(default_factory=list)
    deleted_sources: list[str] = Field(default_factory=list)
