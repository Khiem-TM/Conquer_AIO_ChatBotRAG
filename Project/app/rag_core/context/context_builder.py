from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from app.indexing.embeddings import EmbeddingService
from app.indexing.index_service import IndexingService


@dataclass
class RetrievedChunk:
    source_id: str
    source_name: str | None
    chunk_id: str | None
    text: str
    score: float


class ContextBuilder:
    def __init__(
        self,
        indexing_service: IndexingService | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.indexing_service = indexing_service or IndexingService()
        self.embedding_service = embedding_service or EmbeddingService()

    async def retrieve(self, question: str, top_k: int) -> list[RetrievedChunk]:
        index_data = await self.indexing_service.get_index_snapshot()
        chunks: list[dict[str, Any]] = index_data.get('chunks', [])
        if not chunks:
            return []

        backend = index_data.get('embedding_backend', 'simple')
        query_vector = await self.embedding_service.embed_query(question, backend)
        query_terms = set(self._tokenize(question))

        scored: list[RetrievedChunk] = []
        for chunk in chunks:
            text = str(chunk.get('text', '')).strip()
            if not text:
                continue

            vector_score = self._cosine_similarity(query_vector, chunk.get('vector', []))
            keyword_score = self._keyword_overlap_score(query_terms, self._tokenize(text))
            score = (0.7 * vector_score) + (0.3 * keyword_score)

            scored.append(
                RetrievedChunk(
                    source_id=str(chunk.get('source_id', 'unknown')),
                    source_name=chunk.get('source_name'),
                    chunk_id=chunk.get('chunk_id'),
                    text=text,
                    score=round(score, 6),
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        limit = max(1, top_k)
        return scored[:limit]

    def _keyword_overlap_score(self, query_terms: set[str], doc_terms: list[str]) -> float:
        if not query_terms or not doc_terms:
            return 0.0
        doc_set = set(doc_terms)
        overlap = len(query_terms.intersection(doc_set))
        return overlap / max(1, len(query_terms))

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _tokenize(self, text: str) -> list[str]:
        return [token for token in re.findall(r'\w+', text.lower()) if len(token) > 1]

