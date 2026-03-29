from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.shared.configs import settings

DB_PATH = Path(settings.index_db_path)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AppStateDB:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA synchronous=NORMAL')
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_history (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ingest_status (
                    ingest_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    message TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    document_names TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_kv (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS index_runs (
                    run_id TEXT PRIMARY KEY,
                    built_at TEXT NOT NULL,
                    embedding_backend TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    chunker_version TEXT NOT NULL,
                    total_sources INTEGER NOT NULL,
                    total_chunks INTEGER NOT NULL,
                    notes_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS index_sources (
                    source_id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    updated_at_ns INTEGER NOT NULL,
                    file_size INTEGER NOT NULL,
                    source_hash TEXT NOT NULL,
                    document_char_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS index_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    char_count INTEGER NOT NULL,
                    token_count INTEGER NOT NULL,
                    chunk_hash TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(source_id) REFERENCES index_sources(source_id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_index_chunks_source_id ON index_chunks(source_id)'
            )
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_index_chunks_chunk_hash ON index_chunks(chunk_hash)'
            )
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_index_sources_source_hash ON index_sources(source_hash)'
            )

    def fetch_chat_history(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            cur = conn.execute(
                'SELECT id, question, answer, timestamp FROM chat_history ORDER BY timestamp DESC'
            )
            return cur.fetchall()

    def insert_chat_history(self, msg_id: str, question: str, answer: str) -> str:
        ts = _now_iso()
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO chat_history(id, question, answer, timestamp) VALUES(?, ?, ?, ?)',
                (msg_id, question, answer, ts),
            )
        return ts

    def clear_chat_history(self) -> int:
        with self._connect() as conn:
            cur = conn.execute('SELECT COUNT(*) AS c FROM chat_history')
            count = int(cur.fetchone()['c'])
            conn.execute('DELETE FROM chat_history')
            return count

    def upsert_ingest(
        self,
        ingest_id: str,
        status: str,
        message: str | None,
        created_at: str,
        completed_at: str | None,
        document_names_json: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ingest_status(ingest_id, status, message, created_at, completed_at, document_names)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(ingest_id) DO UPDATE SET
                    status=excluded.status,
                    message=excluded.message,
                    created_at=excluded.created_at,
                    completed_at=excluded.completed_at,
                    document_names=excluded.document_names
                """,
                (ingest_id, status, message, created_at, completed_at, document_names_json),
            )

    def get_ingest(self, ingest_id: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            cur = conn.execute(
                'SELECT ingest_id, status, message, created_at, completed_at, document_names FROM ingest_status WHERE ingest_id=?',
                (ingest_id,),
            )
            return cur.fetchone()

    def list_ingests(self, limit: int) -> list[sqlite3.Row]:
        with self._connect() as conn:
            cur = conn.execute(
                'SELECT ingest_id, status, message, created_at, completed_at, document_names FROM ingest_status ORDER BY created_at DESC LIMIT ?',
                (limit,),
            )
            return cur.fetchall()

    def kv_get(self, key: str) -> Any | None:
        with self._connect() as conn:
            cur = conn.execute('SELECT value_json FROM app_kv WHERE key=?', (key,))
            row = cur.fetchone()
            if not row:
                return None
            return json.loads(str(row['value_json']))

    def kv_set(self, key: str, value: Any) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO app_kv(key, value_json, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json=excluded.value_json,
                    updated_at=excluded.updated_at
                """,
                (key, payload, _now_iso()),
            )


app_state_db = AppStateDB()
