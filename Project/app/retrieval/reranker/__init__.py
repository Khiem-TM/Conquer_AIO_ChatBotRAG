from __future__ import annotations

from dataclasses import dataclass, field

from app.retrieval.text_utils import normalize_text, tokenize
from app.retrieval.types import IndexedChunk


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
    """Lightweight reranker to reduce noisy context before generation."""

    SOURCE_HINT_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...], float], ...] = (
        (
            ('v-green', 'vinfast', 'kwh', 'tram sac', 'trạm sạc', 'xe điện'),
            ('test.txt.txt',),
            1.0,
        ),
        (
            ('anscombe', 'chartjunk', 'data-ink', 'seaborn', 'matplotlib', 'visualization', 'trực quan'),
            ('part1-4_minh_vn.md', 'part1-4_minh_en.md'),
            0.8,
        ),
        (
            (
                'syllabus',
                'english for career development',
                'module',
                'resume',
                'cover letter',
                'interview',
                'creative commons',
                'fhi 360',
                'u.s. department of state',
                'open',
            ),
            ('english for career development syllabus 2023.pdf',),
            1.0,
        ),
        (
            (
                'phương án b',
                'retrieval owner',
                'definition of done',
                'deliverable',
                'embedding + indexing',
                'eval/devops',
                'frontend nhẹ',
                'workflow nghiệp vụ',
                'mvp',
                'lane',
            ),
            ('docs_phan_chia_cong_viec_chatbot_rag.docx',),
            1.0,
        ),
    )

    def __init__(
        self,
        fused_weight: float = 0.44,
        coverage_weight: float = 0.22,
        phrase_weight: float = 0.08,
        source_weight: float = 0.22,
        length_weight: float = 0.04,
        source_mismatch_penalty_factor: float = 0.15,
    ) -> None:
        self.fused_weight = fused_weight
        self.coverage_weight = coverage_weight
        self.phrase_weight = phrase_weight
        self.source_weight = source_weight
        self.length_weight = length_weight
        self.source_mismatch_penalty_factor = max(0.0, source_mismatch_penalty_factor)

    def rerank(
        self,
        query: str,
        candidates: list[RerankInput],
        top_k: int,
    ) -> list[RerankResult]:
        if not candidates:
            return []

        max_fused = max(candidate.fused_score for candidate in candidates) or 1.0
        min_fused = min(candidate.fused_score for candidate in candidates)

        query_terms = set(tokenize(query))
        query_norm = normalize_text(query)

        reranked: list[RerankResult] = []
        for candidate in candidates:
            text_norm = normalize_text(candidate.chunk.text)
            doc_terms = set(tokenize(candidate.chunk.text))

            intersection = len(query_terms & doc_terms)
            coverage = intersection / max(1, len(query_terms))
            phrase_hit = 1.0 if query_norm and query_norm in text_norm else 0.0
            length_score = self._length_score(candidate.chunk.text)
            source_score = self._source_score(
                query_norm=query_norm,
                query_terms=query_terms,
                source_name=candidate.chunk.source_name,
            )
            fused_norm = (candidate.fused_score - min_fused) / (max_fused - min_fused + 1e-9)

            final_score = (
                self.fused_weight * fused_norm
                + self.coverage_weight * coverage
                + self.phrase_weight * phrase_hit
                + self.source_weight * source_score
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
                        'source_score': source_score,
                        'length_score': length_score,
                        'fused_norm': fused_norm,
                    },
                )
            )

        reranked.sort(key=lambda item: item.final_score, reverse=True)
        return reranked[:top_k]

    def _length_score(self, text: str) -> float:
        length = len(text)
        if length < 120:
            return 0.2
        if length <= 1200:
            return 1.0
        if length <= 1800:
            return 0.7
        return 0.5

    def _source_score(self, query_norm: str, query_terms: set[str], source_name: str | None) -> float:
        source_name = source_name or ''
        source_terms = set(tokenize(source_name))
        base = 0.0
        if query_terms and source_terms:
            intersection = len(query_terms & source_terms)
            base = intersection / max(1, len(query_terms))

        source_norm = normalize_text(source_name)
        hint = 0.0
        matched_rule_scores: list[float] = []
        has_matching_source_hint = False
        for triggers, source_patterns, hint_score in self.SOURCE_HINT_RULES:
            if not any(trigger in query_norm for trigger in triggers):
                continue
            matched_rule_scores.append(hint_score)
            if any(pattern in source_norm for pattern in source_patterns):
                has_matching_source_hint = True
                hint = max(hint, hint_score)

        if matched_rule_scores and not has_matching_source_hint:
            strongest_rule = max(matched_rule_scores)
            hint = -self.source_mismatch_penalty_factor * strongest_rule

        return max(base, hint) if hint >= 0.0 else hint


__all__ = ['HeuristicReranker', 'RerankInput', 'RerankResult']
