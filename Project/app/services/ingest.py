"""Service layer for ingest operations."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models.ingest import IngestStatus, IngestStatusResponse


class IngestService:
    """Service to manage ingest operations."""

    def __init__(self, status_file: str = "data/ingest_status.json"):
        self.status_file = Path(status_file)
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_status()

    def _load_status(self) -> None:
        """Load ingest status from file."""
        if self.status_file.exists():
            try:
                with open(self.status_file, "r") as f:
                    data = json.load(f)
                    self.ingest_ops: dict = data.get("operations", {})
            except (json.JSONDecodeError, IOError):
                self.ingest_ops = {}
        else:
            self.ingest_ops = {}

    def _save_status(self) -> None:
        """Save ingest status to file."""
        with open(self.status_file, "w") as f:
            json.dump({"operations": self.ingest_ops}, f, indent=2, default=str)

    def start_ingest(self, docs_count: int) -> str:
        """Start a new ingest operation."""
        ingest_id = str(uuid.uuid4())
        timestamp = datetime.now()

        self.ingest_ops[ingest_id] = {
            "id": ingest_id,
            "status": IngestStatus.PROCESSING,
            "timestamp": timestamp.isoformat(),
            "message": f"Processing {docs_count} document(s)",
            "docs_processed": 0,
            "chunks_created": 0,
        }

        self._save_status()
        return ingest_id

    def complete_ingest(
        self, ingest_id: str, docs_processed: int, chunks_created: int
    ) -> None:
        """Mark an ingest operation as complete."""
        if ingest_id in self.ingest_ops:
            self.ingest_ops[ingest_id]["status"] = IngestStatus.DONE
            self.ingest_ops[ingest_id]["message"] = (
                f"Successfully processed {docs_processed} document(s) "
                f"and created {chunks_created} chunk(s)"
            )
            self.ingest_ops[ingest_id]["docs_processed"] = docs_processed
            self.ingest_ops[ingest_id]["chunks_created"] = chunks_created
            self._save_status()

    def fail_ingest(self, ingest_id: str, error_message: str) -> None:
        """Mark an ingest operation as failed."""
        if ingest_id in self.ingest_ops:
            self.ingest_ops[ingest_id]["status"] = IngestStatus.FAILED
            self.ingest_ops[ingest_id]["message"] = error_message
            self._save_status()

    def get_status(self, ingest_id: str) -> Optional[IngestStatusResponse]:
        """Get status of an ingest operation."""
        if ingest_id not in self.ingest_ops:
            return None

        op = self.ingest_ops[ingest_id]
        timestamp = datetime.fromisoformat(op["timestamp"])

        return IngestStatusResponse(
            ingest_id=op["id"],
            status=op["status"],
            timestamp=timestamp,
            message=op["message"],
            docs_processed=op.get("docs_processed", 0),
            chunks_created=op.get("chunks_created", 0),
        )
