from __future__ import annotations

import sqlite3
from pathlib import Path


class ImportRegistry:
    """SQLite registry lưu metadata các file đã ingest/import."""

    def __init__(self, db_path: str = 'data/import_registry.db') -> None:
        self._project_dir = Path(__file__).resolve().parents[3]
        self.db_path = self._resolve_path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (self._project_dir / path).resolve()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS imported_files (
                    file_path TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    file_ext TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    updated_at_ns INTEGER NOT NULL,
                    ingested_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def upsert_file(
        self,
        file_path: str,
        file_name: str,
        file_ext: str,
        file_size: int,
        updated_at_ns: int,
        ingested_at: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO imported_files(
                    file_path, file_name, file_ext, file_size, updated_at_ns, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    file_name=excluded.file_name,
                    file_ext=excluded.file_ext,
                    file_size=excluded.file_size,
                    updated_at_ns=excluded.updated_at_ns,
                    ingested_at=excluded.ingested_at
                """,
                (file_path, file_name, file_ext, file_size, updated_at_ns, ingested_at),
            )
            conn.commit()

    def count_files(self) -> int:
        with self._connect() as conn:
            row = conn.execute('SELECT COUNT(1) AS total FROM imported_files').fetchone()
            return int(row['total']) if row is not None else 0

