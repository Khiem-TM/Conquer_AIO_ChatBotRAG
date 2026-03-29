"""SQLite-backed storage for chat history and ingest status."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from app.shared.db import app_state_db
from app.shared.schemas.history import ChatHistoryEntry, IngestStatus


class HistoryStore:
    def add_entry(self, question: str, answer: str) -> ChatHistoryEntry:
        entry = ChatHistoryEntry(
            id=f'msg_{uuid.uuid4()}',
            question=question,
            answer=answer,
            timestamp=datetime.now(timezone.utc),
        )
        ts = app_state_db.insert_chat_history(entry.id, question, answer)
        entry.timestamp = datetime.fromisoformat(ts)
        return entry

    def get_all(self) -> list[ChatHistoryEntry]:
        rows = app_state_db.fetch_chat_history()
        return [
            ChatHistoryEntry(
                id=str(row['id']),
                question=str(row['question']),
                answer=str(row['answer']),
                timestamp=datetime.fromisoformat(str(row['timestamp'])),
            )
            for row in rows
        ]

    def clear(self) -> int:
        return app_state_db.clear_chat_history()

    def get_count(self) -> int:
        return len(app_state_db.fetch_chat_history())


class IngestStatusStore:
    def create_ingest(self, document_names: list[str] | None = None) -> str:
        ingest_id = f'ingest_{uuid.uuid4()}'
        created_at = datetime.now(timezone.utc)
        item = IngestStatus(
            ingest_id=ingest_id,
            status='pending',
            created_at=created_at,
            document_names=document_names or [],
        )
        app_state_db.upsert_ingest(
            ingest_id=item.ingest_id,
            status=item.status,
            message=item.message,
            created_at=item.created_at.isoformat(),
            completed_at=None,
            document_names_json=json.dumps(item.document_names, ensure_ascii=False),
        )
        return ingest_id

    def update_status(self, ingest_id: str, status: str, message: str | None = None, completed: bool = False) -> IngestStatus | None:
        current = self.get_status(ingest_id)
        if current is None:
            return None
        current.status = status
        if message is not None:
            current.message = message
        if completed:
            current.completed_at = datetime.now(timezone.utc)
        app_state_db.upsert_ingest(
            ingest_id=current.ingest_id,
            status=current.status,
            message=current.message,
            created_at=current.created_at.isoformat(),
            completed_at=current.completed_at.isoformat() if current.completed_at else None,
            document_names_json=json.dumps(current.document_names, ensure_ascii=False),
        )
        return current

    def get_status(self, ingest_id: str) -> IngestStatus | None:
        row = app_state_db.get_ingest(ingest_id)
        if row is None:
            return None
        return IngestStatus(
            ingest_id=str(row['ingest_id']),
            status=str(row['status']),
            message=str(row['message']) if row['message'] is not None else None,
            created_at=datetime.fromisoformat(str(row['created_at'])),
            completed_at=datetime.fromisoformat(str(row['completed_at'])) if row['completed_at'] else None,
            document_names=json.loads(str(row['document_names']) or '[]'),
        )

    def mark_done(self, ingest_id: str, message: str = 'Ingest completed successfully') -> IngestStatus | None:
        return self.update_status(ingest_id, 'done', message, completed=True)

    def mark_failed(self, ingest_id: str, message: str = 'Ingest failed') -> IngestStatus | None:
        return self.update_status(ingest_id, 'failed', message, completed=True)

    def list_ingests(self, limit: int = 50) -> list[IngestStatus]:
        rows = app_state_db.list_ingests(limit)
        return [
            IngestStatus(
                ingest_id=str(row['ingest_id']),
                status=str(row['status']),
                message=str(row['message']) if row['message'] is not None else None,
                created_at=datetime.fromisoformat(str(row['created_at'])),
                completed_at=datetime.fromisoformat(str(row['completed_at'])) if row['completed_at'] else None,
                document_names=json.loads(str(row['document_names']) or '[]'),
            )
            for row in rows
        ]

    def get_count(self) -> int:
        return len(app_state_db.list_ingests(1000000))


history_store = HistoryStore()
ingest_status_store = IngestStatusStore()
