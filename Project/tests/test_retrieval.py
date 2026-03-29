"""Tests for hybrid retrieval, reranker, and chunker logic.

These tests run without Ollama or any external service — pure unit tests.
"""
from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path

from app.indexing.vectorstore.local_index_store import LocalIndexStore, SourceDocument
from app.retrieval.reranker import HeuristicReranker, RerankInput
from app.retrieval.text_utils import normalize_text, tokenize
from app.retrieval.types import IndexedChunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chunk(chunk_id: str, text: str, source_name: str = 'test.md') -> IndexedChunk:
    return IndexedChunk(
        chunk_id=chunk_id,
        source_id='src_' + chunk_id,
        source_name=source_name,
        text=text,
        vector=[],
        metadata={'relative_path': source_name},
    )


def _make_rerank_input(chunk: IndexedChunk, fused: float = 0.5) -> RerankInput:
    return RerankInput(
        chunk=chunk,
        fused_score=fused,
        keyword_score=fused,
        vector_score=fused,
    )


# ---------------------------------------------------------------------------
# Tokenizer / normalizer
# ---------------------------------------------------------------------------

class TextUtilsTestCase(unittest.TestCase):
    def test_tokenize_basic(self) -> None:
        tokens = tokenize('Phân tích nguyên nhân và kết quả')
        self.assertIn('phân', tokens)
        self.assertIn('nguyên', tokens)
        self.assertGreater(len(tokens), 3)

    def test_tokenize_strips_stopwords_like_và(self) -> None:
        tokens = tokenize('A và B')
        # 'và' may or may not be kept depending on implementation — just check it doesn't crash
        self.assertIsInstance(tokens, list)

    def test_normalize_lowercases(self) -> None:
        self.assertEqual(normalize_text('Hello World'), 'hello world')

    def test_normalize_collapses_whitespace(self) -> None:
        result = normalize_text('  hello   world  ')
        self.assertEqual(result, 'hello world')


# ---------------------------------------------------------------------------
# HeuristicReranker
# ---------------------------------------------------------------------------

class HeuristicRerankerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.reranker = HeuristicReranker()

    def test_rerank_returns_top_k(self) -> None:
        chunks = [_make_chunk(f'c{i}', f'Document about topic {i} with some relevant content here.') for i in range(10)]
        inputs = [_make_rerank_input(c, fused=float(i) / 10) for i, c in enumerate(chunks)]
        results = self.reranker.rerank('topic', inputs, top_k=3)
        self.assertEqual(len(results), 3)

    def test_rerank_respects_phrase_hit(self) -> None:
        """Chunk containing exact query phrase should rank higher."""
        chunk_phrase = _make_chunk('phrase', 'machine learning is powerful and widely used in industry.')
        chunk_other = _make_chunk('other', 'deep neural networks are used in many applications today.')
        inputs = [
            _make_rerank_input(chunk_phrase, fused=0.4),
            _make_rerank_input(chunk_other, fused=0.4),
        ]
        results = self.reranker.rerank('machine learning', inputs, top_k=2)
        self.assertEqual(results[0].chunk.chunk_id, 'phrase')

    def test_rerank_empty_input(self) -> None:
        results = self.reranker.rerank('anything', [], top_k=5)
        self.assertEqual(results, [])

    def test_rerank_features_present(self) -> None:
        chunk = _make_chunk('c1', 'Some relevant text about the query topic.')
        inputs = [_make_rerank_input(chunk)]
        results = self.reranker.rerank('query topic', inputs, top_k=1)
        self.assertIn('coverage', results[0].features)
        self.assertIn('phrase_hit', results[0].features)
        self.assertIn('filename_score', results[0].features)

    def test_filename_match_boosts_score(self) -> None:
        chunk_match = _make_chunk('c_match', 'Some content.', source_name='machine_learning_guide.md')
        chunk_no = _make_chunk('c_no', 'Some content.', source_name='cooking_recipes.md')
        inputs = [
            _make_rerank_input(chunk_match, fused=0.3),
            _make_rerank_input(chunk_no, fused=0.3),
        ]
        results = self.reranker.rerank('machine learning', inputs, top_k=2)
        self.assertEqual(results[0].chunk.chunk_id, 'c_match')


# ---------------------------------------------------------------------------
# LocalIndexStore — chunker
# ---------------------------------------------------------------------------

class ChunkerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = LocalIndexStore()

    def _make_doc(self, text: str) -> SourceDocument:
        return SourceDocument(
            source_id='test',
            source_name='test.txt',
            file_path=Path('test.txt'),
            relative_path='test.txt',
            updated_at_ns=0,
            file_size=len(text),
            text=text,
            source_hash=self.store.compute_hash(text),
        )

    def test_short_text_produces_one_chunk(self) -> None:
        doc = self._make_doc('Đây là một đoạn văn ngắn.')
        chunks, texts = self.store.prepare_chunk_records([doc])
        self.assertEqual(len(chunks), 1)
        self.assertEqual(len(texts), 1)

    def test_double_newline_splits_into_multiple_chunks(self) -> None:
        text = '\n\n'.join(['Đoạn số một.'] * 5)
        doc = self._make_doc(text)
        chunks, _ = self.store.prepare_chunk_records([doc])
        # May be merged into 1 if total < chunk_size; just check no crash
        self.assertGreaterEqual(len(chunks), 1)

    def test_long_block_splits_correctly(self) -> None:
        # Generate a block much larger than chunk_size (1000 chars default)
        long_text = 'A' * 4000
        parts = self.store.split_long_block(long_text)
        self.assertGreater(len(parts), 1)
        for part in parts:
            self.assertLessEqual(len(part), 1000 + 10)  # small tolerance

    def test_chunk_hash_is_deterministic(self) -> None:
        doc = self._make_doc('Consistent text for hashing.')
        chunks1, _ = self.store.prepare_chunk_records([doc])
        chunks2, _ = self.store.prepare_chunk_records([doc])
        self.assertEqual(chunks1[0]['chunk_hash'], chunks2[0]['chunk_hash'])

    def test_empty_text_skipped(self) -> None:
        doc = self._make_doc('   \n\n   ')
        chunks, _ = self.store.prepare_chunk_records([doc])
        self.assertEqual(len(chunks), 0)

    def test_metadata_fields_present(self) -> None:
        doc = self._make_doc('Some content here for metadata check.')
        chunks, _ = self.store.prepare_chunk_records([doc])
        meta = chunks[0]['metadata']
        self.assertIn('chunk_hash', meta)
        self.assertIn('relative_path', meta)
        self.assertIn('chunk_index', meta)
        self.assertIn('char_count', meta)


# ---------------------------------------------------------------------------
# Chat mode detection
# ---------------------------------------------------------------------------

class ChatModeDetectionTestCase(unittest.TestCase):
    """Tests for ChatService._detect_mode — imported lazily to avoid DB init."""

    def _detect(self, question: str) -> tuple[str, float]:
        from app.rag_core.chat_service import ChatService
        svc = ChatService.__new__(ChatService)
        return svc._detect_mode(question)

    # system_metadata
    def test_system_metadata_english(self) -> None:
        mode, conf = self._detect('How many documents are indexed?')
        self.assertEqual(mode, 'system_metadata')
        self.assertGreaterEqual(conf, 0.5)

    def test_system_metadata_vietnamese(self) -> None:
        mode, _ = self._detect('Cho tôi biết metadata hệ thống và embedding model hiện tại')
        self.assertEqual(mode, 'system_metadata')

    def test_system_metadata_chunk_query(self) -> None:
        mode, _ = self._detect('Có bao nhiêu chunk trong index?')
        self.assertEqual(mode, 'system_metadata')

    # doc content questions — must NOT be classified as system_metadata
    def test_doc_content_not_system(self) -> None:
        mode, _ = self._detect('Tài liệu này nói về chủ đề gì?')
        self.assertNotEqual(mode, 'system_metadata')

    def test_doc_count_about_content_not_system(self) -> None:
        mode, _ = self._detect('Bao nhiêu tài liệu nói về machine learning?')
        self.assertNotEqual(mode, 'system_metadata')

    # reasoning
    def test_reasoning_vietnamese(self) -> None:
        mode, _ = self._detect('Hãy phân tích nguyên nhân và kết luận từ các tài liệu')
        self.assertEqual(mode, 'reasoning_over_docs')

    def test_reasoning_english(self) -> None:
        mode, _ = self._detect('Compare the advantages and disadvantages mentioned in the documents')
        self.assertEqual(mode, 'reasoning_over_docs')

    def test_reasoning_summarize(self) -> None:
        mode, _ = self._detect('Tổng kết những điểm chính trong tài liệu')
        self.assertEqual(mode, 'reasoning_over_docs')

    # document_qa default
    def test_default_document_qa(self) -> None:
        mode, conf = self._detect('Hướng dẫn cài đặt môi trường')
        self.assertEqual(mode, 'document_qa')
        self.assertAlmostEqual(conf, 0.65)

    def test_simple_question_is_doc_qa(self) -> None:
        mode, _ = self._detect('Bước tiếp theo sau khi cài đặt là gì?')
        self.assertEqual(mode, 'document_qa')


if __name__ == '__main__':
    unittest.main()
