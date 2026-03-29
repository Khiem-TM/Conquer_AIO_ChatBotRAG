from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

from app.indexing.config import settings
from app.indexing.vectorstore.local_index_store import LocalIndexStore
from app.shared.db import app_state_db


class SQLiteIndexStore(LocalIndexStore):
    """SQLite-backed index store for local-first usage.

    Source/chunk records live in dedicated SQLite tables. A JSON export is still
    written to ``index_storage_path`` for debugging and easy manual inspection.
    """

    def load_index_data(self) -> dict[str, Any] | None:
        if self._index_data is not None:
            return self._index_data

        with app_state_db._connect() as conn:
            run = conn.execute(
                """
                SELECT run_id, built_at, embedding_backend, embedding_model,
                       schema_version, chunker_version, total_sources, total_chunks, notes_json
                FROM index_runs
                ORDER BY built_at DESC
                LIMIT 1
                """
            ).fetchone()
            if run is None:
                return None

            sources_rows = conn.execute(
                """
                SELECT source_id, source_name, relative_path, file_path, updated_at_ns,
                       file_size, source_hash, document_char_count, chunk_count, metadata_json
                FROM index_sources
                ORDER BY relative_path ASC
                """
            ).fetchall()
            chunk_rows = conn.execute(
                """
                SELECT chunk_id, source_id, source_name, chunk_index, text, vector_json,
                       char_count, token_count, chunk_hash, metadata_json
                FROM index_chunks
                ORDER BY source_id ASC, chunk_index ASC
                """
            ).fetchall()

        sources = {
            str(row['source_id']): {
                'source_name': str(row['source_name']),
                'relative_path': str(row['relative_path']),
                'file_path': str(row['file_path']),
                'updated_at_ns': int(row['updated_at_ns']),
                'file_size': int(row['file_size']),
                'source_hash': str(row['source_hash']),
                'document_char_count': int(row['document_char_count']),
                'chunk_count': int(row['chunk_count']),
                **json.loads(str(row['metadata_json']) or '{}'),
            }
            for row in sources_rows
        }

        chunks: list[dict[str, Any]] = []
        for row in chunk_rows:
            metadata = json.loads(str(row['metadata_json']) or '{}')
            chunks.append(
                {
                    'chunk_id': str(row['chunk_id']),
                    'source_id': str(row['source_id']),
                    'source_name': str(row['source_name']),
                    'chunk_index': int(row['chunk_index']),
                    'text': str(row['text']),
                    'vector': json.loads(str(row['vector_json']) or '[]'),
                    'chunk_hash': str(row['chunk_hash']),
                    'metadata': metadata,
                }
            )

        self._index_data = {
            'run_id': str(run['run_id']),
            'schema_version': int(run['schema_version']),
            'chunker_version': str(run['chunker_version']),
            'built_at': str(run['built_at']),
            'embedding_backend': str(run['embedding_backend']),
            'embedding_model': str(run['embedding_model']),
            'sources': sources,
            'chunks': chunks,
            'manifest': {
                'total_sources': int(run['total_sources']),
                'total_chunks': int(run['total_chunks']),
                **json.loads(str(run['notes_json']) or '{}'),
            },
        }
        return self._index_data

    def write_index_data(self, index_data: dict[str, Any]) -> None:
        chunks = list(index_data.get('chunks', []))
        sources = dict(index_data.get('sources', {}))
        manifest = {
            **dict(index_data.get('manifest', {})),
            'updated_at': self.utc_now(),
        }
        run_id = str(index_data.get('run_id') or f'run_{uuid.uuid4().hex}')

        # Ensure chunk_count is synchronized with actual chunk payload.
        chunk_counts: dict[str, int] = {}
        for chunk in chunks:
            source_id = str(chunk.get('source_id', ''))
            chunk_counts[source_id] = chunk_counts.get(source_id, 0) + 1
        for source_id, payload in sources.items():
            payload['chunk_count'] = chunk_counts.get(source_id, 0)

        with app_state_db._connect() as conn:
            conn.execute('DELETE FROM index_chunks')
            conn.execute('DELETE FROM index_sources')
            conn.execute('DELETE FROM index_runs')

            for source_id, payload in sources.items():
                metadata = {
                    key: value
                    for key, value in payload.items()
                    if key not in {
                        'source_name',
                        'relative_path',
                        'file_path',
                        'updated_at_ns',
                        'file_size',
                        'source_hash',
                        'document_char_count',
                        'chunk_count',
                    }
                }
                conn.execute(
                    """
                    INSERT INTO index_sources(
                        source_id, source_name, relative_path, file_path, updated_at_ns,
                        file_size, source_hash, document_char_count, chunk_count, metadata_json
                    )
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source_id,
                        str(payload.get('source_name', '')),
                        str(payload.get('relative_path') or payload.get('file_path') or ''),
                        str(payload.get('file_path') or payload.get('relative_path') or ''),
                        int(payload.get('updated_at_ns', 0)),
                        int(payload.get('file_size', 0)),
                        str(payload.get('source_hash', '')),
                        int(payload.get('document_char_count', 0)),
                        int(payload.get('chunk_count', 0)),
                        json.dumps(metadata, ensure_ascii=False),
                    ),
                )

            for chunk in chunks:
                metadata = dict(chunk.get('metadata', {}) or {})
                conn.execute(
                    """
                    INSERT INTO index_chunks(
                        chunk_id, source_id, source_name, chunk_index, text, vector_json,
                        char_count, token_count, chunk_hash, metadata_json
                    )
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(chunk.get('chunk_id', '')),
                        str(chunk.get('source_id', '')),
                        str(chunk.get('source_name', '')),
                        int(chunk.get('chunk_index', 0) or metadata.get('chunk_index', 0) or 0),
                        str(chunk.get('text', '')),
                        json.dumps(chunk.get('vector', []), ensure_ascii=False),
                        int(metadata.get('char_count', len(str(chunk.get('text', ''))))),
                        int(metadata.get('token_count', 0)),
                        str(chunk.get('chunk_hash') or metadata.get('chunk_hash') or ''),
                        json.dumps(metadata, ensure_ascii=False),
                    ),
                )

            conn.execute(
                """
                INSERT INTO index_runs(
                    run_id, built_at, embedding_backend, embedding_model, schema_version,
                    chunker_version, total_sources, total_chunks, notes_json
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    str(index_data.get('built_at') or self.utc_now()),
                    str(index_data.get('embedding_backend', 'pending')),
                    str(index_data.get('embedding_model', settings.embedding_model)),
                    int(index_data.get('schema_version', settings.index_schema_version)),
                    str(index_data.get('chunker_version', settings.index_chunker_version)),
                    len(sources),
                    len(chunks),
                    json.dumps(manifest, ensure_ascii=False),
                ),
            )

        index_data['run_id'] = run_id
        index_data['manifest'] = manifest
        super().write_index_data(index_data)

    def clear_index(self) -> None:
        with app_state_db._connect() as conn:
            conn.execute('DELETE FROM index_chunks')
            conn.execute('DELETE FROM index_sources')
            conn.execute('DELETE FROM index_runs')
        self._index_data = None
        storage_path = self.get_storage_path()
        if storage_path.exists():
            storage_path.unlink()
