from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from app.retrieval.text_utils import normalize_text, tokenize
from app.retrieval.types import IndexedChunk
from app.shared.configs import settings
from app.shared.utils import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class RerankInput:
    chunk: IndexedChunk
    fused_score: float
    keyword_score: float
    vector_score: float
    keyword_rank: int | None = None
    vector_rank: int | None = None


@dataclass(slots=True)
class RerankResult:
    chunk: IndexedChunk
    final_score: float
    fused_score: float
    keyword_score: float
    vector_score: float
    keyword_rank: int | None = None
    vector_rank: int | None = None
    features: dict[str, float] = field(default_factory=dict)


class HeuristicReranker:
    """Generic lightweight reranker for local-first RAG usage."""

    def __init__(
        self,
        fused_weight: float = 0.45,
        coverage_weight: float = 0.25,
        phrase_weight: float = 0.1,
        filename_weight: float = 0.15,
        length_weight: float = 0.05,
    ) -> None:
        self.fused_weight = fused_weight
        self.coverage_weight = coverage_weight
        self.phrase_weight = phrase_weight
        self.filename_weight = filename_weight
        self.length_weight = length_weight

    def rerank(self, query: str, candidates: list[RerankInput], top_k: int) -> list[RerankResult]:
        if not candidates:
            return []

        query_norm = normalize_text(query)
        query_terms = set(tokenize(query))
        max_fused = max(candidate.fused_score for candidate in candidates) or 1.0
        min_fused = min(candidate.fused_score for candidate in candidates)
        # Fix: khi chỉ có 1 chunk hoặc tất cả chunk có cùng score,
        # (max - min) ≈ 0 nên fused_norm = 0 → final_score rất thấp → bị filter hết.
        # Khi score_range quá nhỏ, coi fused_norm = 1.0 (chunk đó là tốt nhất).
        score_range = max_fused - min_fused

        reranked: list[RerankResult] = []
        for candidate in candidates:
            text_norm = normalize_text(candidate.chunk.text)
            doc_terms = set(tokenize(candidate.chunk.text))
            coverage = len(query_terms & doc_terms) / max(1, len(query_terms))
            phrase_hit = 1.0 if query_norm and query_norm in text_norm else 0.0
            filename_score = self._filename_match_score(query_norm, candidate.chunk)
            length_score = self._length_score(candidate.chunk.text)
            fused_norm = (
                (candidate.fused_score - min_fused) / score_range
                if score_range > 1e-6
                else 1.0
            )
            final_score = (
                self.fused_weight * fused_norm
                + self.coverage_weight * coverage
                + self.phrase_weight * phrase_hit
                + self.filename_weight * filename_score
                + self.length_weight * length_score
            )
            reranked.append(
                RerankResult(
                    chunk=candidate.chunk,
                    final_score=final_score,
                    fused_score=candidate.fused_score,
                    keyword_score=candidate.keyword_score,
                    vector_score=candidate.vector_score,
                    keyword_rank=candidate.keyword_rank,
                    vector_rank=candidate.vector_rank,
                    features={
                        'coverage': coverage,
                        'phrase_hit': phrase_hit,
                        'filename_score': filename_score,
                        'length_score': length_score,
                        'fused_norm': fused_norm,
                    },
                )
            )

        reranked.sort(key=lambda item: item.final_score, reverse=True)
        return reranked[:top_k]

    def _filename_match_score(self, query_norm: str, chunk: IndexedChunk) -> float:
        if not query_norm:
            return 0.0
        source_name = normalize_text(chunk.source_name or '')
        relative_path = normalize_text(str(chunk.metadata.get('relative_path', '')))
        haystack = f'{source_name} {relative_path}'.strip()
        if not haystack:
            return 0.0
        if query_norm in haystack:
            return 1.0
        query_terms = set(tokenize(query_norm))
        file_terms = set(tokenize(haystack))
        if not query_terms or not file_terms:
            return 0.0
        return len(query_terms & file_terms) / len(query_terms)

    def _length_score(self, text: str) -> float:
        length = len(text)
        if length < 120:
            return 0.2
        if length <= 1400:
            return 1.0
        if length <= 2200:
            return 0.7
        return 0.45


class LlmReranker:
    """Optional local Ollama reranker. Disabled by default for better local DX."""

    def __init__(self) -> None:
        self._enabled = bool(settings.retrieval_enable_llm_reranker)

    async def score(self, query: str, chunk: IndexedChunk) -> float:
        if not self._enabled:
            return 0.0

        prompt = (
            'You are a strict retrieval reranker. '
            'Given QUERY and PASSAGE, return only one float number in [0,1].\n\n'
            f'QUERY: {query}\n\n'
            f'PASSAGE: {chunk.text[:1200]}\n\n'
            'Output format: 0.00'
        )
        try:
            timeout = max(8, min(20, settings.request_timeout_seconds))
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/generate",
                    json={
                        'model': settings.ollama_reranker_model,
                        'prompt': prompt,
                        'stream': False,
                        'options': {'temperature': 0.0, 'num_predict': 8},
                    },
                )
                response.raise_for_status()
                raw = str(response.json().get('response', '')).strip()
            value = float(raw.split()[0])
            return max(0.0, min(1.0, value))
        except Exception as exc:
            logger.warning('LLM reranker scoring failed for chunk=%s: %r', chunk.chunk_id, exc)
            return 0.0


__all__ = ['HeuristicReranker', 'LlmReranker', 'RerankInput', 'RerankResult']
