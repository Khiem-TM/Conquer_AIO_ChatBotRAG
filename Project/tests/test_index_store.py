from __future__ import annotations

import unittest
from pathlib import Path

from app.indexing.vectorstore.local_index_store import LocalIndexStore, SourceDocument
from app.indexing.vectorstore.sqlite_index_store import SQLiteIndexStore


class LocalIndexStoreTestCase(unittest.TestCase):
    def test_split_and_prepare_chunk_records(self) -> None:
        store = LocalIndexStore()
        doc = SourceDocument(
            source_id='sample',
            source_name='sample.txt',
            file_path=Path('sample.txt'),
            relative_path='sample.txt',
            updated_at_ns=1,
            file_size=10,
            text='Đây là đoạn một.\n\nĐây là đoạn hai có nhiều nội dung hơn.',
            source_hash='hash123',
        )
        chunks, texts = store.prepare_chunk_records([doc])
        self.assertGreaterEqual(len(chunks), 1)
        self.assertEqual(len(chunks), len(texts))
        self.assertIn('chunk_hash', chunks[0])
        self.assertEqual(chunks[0]['metadata']['relative_path'], 'sample.txt')


class SQLiteIndexStoreTestCase(unittest.TestCase):
    def test_roundtrip_snapshot(self) -> None:
        store = SQLiteIndexStore()
        snapshot = {
            'schema_version': 2,
            'chunker_version': 'v2',
            'embedding_backend': 'simple',
            'embedding_model': 'nomic-embed-text',
            'built_at': '2026-01-01T00:00:00+00:00',
            'sources': {
                'sample': {
                    'source_name': 'sample.txt',
                    'relative_path': 'sample.txt',
                    'file_path': 'sample.txt',
                    'updated_at_ns': 1,
                    'file_size': 10,
                    'source_hash': 'hash123',
                    'document_char_count': 12,
                    'chunk_count': 1,
                }
            },
            'chunks': [
                {
                    'chunk_id': 'sample_chunk_001',
                    'source_id': 'sample',
                    'source_name': 'sample.txt',
                    'chunk_index': 1,
                    'text': 'hello world',
                    'vector': [0.1, 0.2],
                    'chunk_hash': 'chunkhash',
                    'metadata': {
                        'relative_path': 'sample.txt',
                        'chunk_hash': 'chunkhash',
                        'char_count': 11,
                        'token_count': 2,
                    },
                }
            ],
            'manifest': {'reused_vectors': 0},
        }
        store.write_index_data(snapshot)
        loaded = store.load_index_data()
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded['sources']['sample']['source_hash'], 'hash123')
        self.assertEqual(loaded['chunks'][0]['chunk_hash'], 'chunkhash')
        store.clear_index()


if __name__ == '__main__':
    unittest.main()
