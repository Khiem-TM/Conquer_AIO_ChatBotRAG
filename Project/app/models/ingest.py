"""Ingest-related data models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class IngestStatus(str, Enum):
    """Status of an ingest operation."""

    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class IngestRequest(BaseModel):
    """Request to ingest documents."""

    documents: list[str] = Field(..., description="List of document paths or content")


class IngestResponse(BaseModel):
    """Response from ingest endpoint."""

    ingest_id: str = Field(..., description="Unique ingest operation ID")
    status: IngestStatus = Field(..., description="Current status")
    timestamp: datetime = Field(..., description="Ingest start time")
    message: str = Field(..., description="Status message")


class IngestStatusResponse(BaseModel):
    """Response for ingest status check."""

    ingest_id: str = Field(..., description="Ingest operation ID")
    status: IngestStatus = Field(..., description="Current status")
    timestamp: datetime = Field(..., description="Last update time")
    message: str = Field(..., description="Status message")
    docs_processed: int = Field(default=0, description="Number of documents processed")
    chunks_created: int = Field(default=0, description="Number of chunks created")
