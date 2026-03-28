"""In-memory storage for chat history and ingest status."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.shared.schemas.history import ChatHistoryEntry, IngestStatus


class HistoryStore:
    """Global in-memory store for chat history (thread-safe)."""

    def __init__(self) -> None:
        self._history: list[ChatHistoryEntry] = []
        self._lock = Lock()

    def add_entry(self, question: str, answer: str) -> ChatHistoryEntry:
        """Add a chat entry to history."""
        with self._lock:
            entry = ChatHistoryEntry(
                id=f'msg_{uuid.uuid4()}',
                question=question,
                answer=answer,
                timestamp=datetime.now(timezone.utc),
            )
            self._history.insert(0, entry)  # Insert at beginning for "latest first"
            return entry

    def get_all(self) -> list[ChatHistoryEntry]:
        """Get all chat history (latest first)."""
        with self._lock:
            return self._history.copy()

    def clear(self) -> int:
        """Clear all history and return count of deleted entries."""
        with self._lock:
            count = len(self._history)
            self._history.clear()
            return count

    def get_count(self) -> int:
        """Get total chat count."""
        with self._lock:
            return len(self._history)


class IngestStatusStore:
    """Global in-memory store for ingest status tracking (thread-safe)."""

    def __init__(self) -> None:
        self._ingests: dict[str, IngestStatus] = {}
        self._lock = Lock()

    def create_ingest(self) -> str:
        """Create new ingest job and return ingest_id."""
        with self._lock:
            ingest_id = f'ingest_{uuid.uuid4()}'
            self._ingests[ingest_id] = IngestStatus(
                ingest_id=ingest_id,
                status='pending',
                created_at=datetime.now(timezone.utc),
            )
            return ingest_id

    def update_status(
        self,
        ingest_id: str,
        status: str,
        message: str | None = None,
        completed: bool = False,
    ) -> IngestStatus | None:
        """Update ingest status."""
        with self._lock:
            if ingest_id not in self._ingests:
                return None

            ingest = self._ingests[ingest_id]
            ingest.status = status
            if message:
                ingest.message = message
            if completed:
                ingest.completed_at = datetime.now(timezone.utc)

            self._ingests[ingest_id] = ingest
            return ingest

    def get_status(self, ingest_id: str) -> IngestStatus | None:
        """Get ingest status by ID."""
        with self._lock:
            return self._ingests.get(ingest_id)

    def mark_done(self, ingest_id: str, message: str = 'Ingest completed successfully') -> IngestStatus | None:
        """Mark ingest as done."""
        return self.update_status(ingest_id, 'done', message, completed=True)

    def mark_failed(self, ingest_id: str, message: str = 'Ingest failed') -> IngestStatus | None:
        """Mark ingest as failed."""
        return self.update_status(ingest_id, 'failed', message, completed=True)


# Global instances
history_store = HistoryStore()
ingest_status_store = IngestStatusStore()
