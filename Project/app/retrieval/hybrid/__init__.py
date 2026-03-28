from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
import hashlib
import math
from typing import Any

from app.indexing import IndexingService
from app.indexing.embeddings import EmbeddingService
from app.retrieval.reranker import HeuristicReranker, RerankInput, RerankResult
from app.retrieval.text_utils import normalize_text, tokenize
from app.retrieval.types import IndexedChunk
from app.shared.configs import settings
from app.shared.utils import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class HybridRetrievalConfig:
    candidate_top_k: int = settings.retrieval_candidate_top_k
    rerank_pool_k: int = settings.retrieval_rerank_pool_k

    keyword_weight: float = settings.retrieval_keyword_weight
    vector_weight: float = settings.retrieval_vector_weight
    rrf_k: int = settings.retrieval_rrf_k

    min_context_score: float = settings.retrieval_min_context_score
    dedup_jaccard_threshold: float = settings.retrieval_dedup_jaccard_threshold
    source_priority_enabled: bool = settings.retrieval_source_priority_enabled
    source_priority_min_score: float = settings.retrieval_source_priority_min_score
    source_mismatch_penalty_factor: float = settings.retrieval_source_mismatch_penalty_factor

    debug: bool = settings.retrieval_debug


@dataclass(slots=True)
class KeywordSearchResult:
    chunk: IndexedChunk
    score: float


@dataclass(slots=True)
class VectorSearchResult:
    chunk: IndexedChunk
    score: float


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    source_id: str
    source_name: str
    text: str
    final_score: float
    fused_score: float
    keyword_score: float
    vector_score: float
    keyword_rank: int | None = None
    vector_rank: int | None = None
    metadata: dict[str, str | int] = field(default_factory=dict)
    features: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalDebugInfo:
    query: str
    indexed_chunks: int
    candidate_top_k: int
    keyword_hits: int
    vector_hits: int
    fused_hits: int
    dedup_dropped: int
    threshold_dropped: int
    final_returned: int
    miss_reason: str | None
    top_keyword_chunk_ids: list[str] = field(default_factory=list)
    top_vector_chunk_ids: list[str] = field(default_factory=list)
    top_fused_chunk_ids: list[str] = field(default_factory=list)
    top_final_chunk_ids: list[str] = field(default_factory=list)
    expanded_queries: list[str] = field(default_factory=list)
    variant_stats: list[dict[str, int | float | str]] = field(default_factory=list)


@dataclass(slots=True)
class RetrievalOutput:
    query: str
    chunks: list[RetrievedChunk]
    debug: RetrievalDebugInfo | None = None


class HybridRetriever:
    """Hybrid retrieval pipeline: keyword + vector + fusion + dedup + rerank."""

    QUERY_EXPANSION_RULES: dict[str, tuple[str, ...]] = {
        'tài trợ': ('sponsored', 'sponsor', 'funding'),
        'quản trị': ('administered', 'managed'),
        'giấy phép': ('license', 'licensed'),
        'cấp phép': ('license', 'licensed'),
        'khóa học': ('course', 'curriculum'),
        'syllabus': ('english for career development', 'course overview'),
        'open': ('online professional english network',),
        'mô đun': ('module', 'resume', 'cover letter', 'interview'),
        'module': ('resume', 'cover letter', 'networking', 'interview'),
        'nội dung': ('focus on', 'cover', 'topic'),
    }
    SOURCE_PRIORITY_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
        (
            (
                'syllabus',
                'english for career development',
                'u.s. department of state',
                'fhi 360',
                'creative commons',
                'open',
            ),
            ('english for career development syllabus 2023.pdf',),
        ),
        (
            ('v-green', 'vinfast', 'kwh', 'trạm sạc', 'xe điện'),
            ('test.txt.txt',),
        ),
        (
            (
                'phương án b',
                'retrieval owner',
                'embedding + indexing',
                'definition of done',
                'workflow nghiệp vụ',
                'lane',
                'deliverable',
            ),
            ('docs_phan_chia_cong_viec_chatbot_rag.docx',),
        ),
        (
            ('anscombe', 'data-ink', 'chartjunk', 'seaborn', 'matplotlib', 'biểu đồ', 'trực quan'),
            ('part1-4_minh_vn.md', 'part1-4_minh_en.md'),
        ),
    )

    def __init__(
        self,
        config: HybridRetrievalConfig | None = None,
        indexing_service: IndexingService | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.config = config or HybridRetrievalConfig()
        self.indexing_service = indexing_service or IndexingService()
        self.embedding_service = embedding_service or EmbeddingService()
        self._reranker = HeuristicReranker(
            source_mismatch_penalty_factor=self.config.source_mismatch_penalty_factor
        )

        self._chunks: list[IndexedChunk] = []
        self._chunk_by_id: dict[str, IndexedChunk] = {}
        self._chunk_token_cache: dict[str, set[str]] = {}
        self._chunk_term_freq: dict[str, Counter[str]] = {}
        self._idf: dict[str, float] = {}
        self._avg_doc_len: float = 0.0
        self._embedding_backend: str = 'simple'
        self._index_signature: str = ''
        self._is_ready = False

    async def build_index(self, force_rebuild: bool = False) -> None:
        index_data = await self.indexing_service.get_index_snapshot()
        signature = self._build_signature(index_data)
        if self._is_ready and not force_rebuild and signature == self._index_signature:
            return

        prepared_chunks = self._prepare_chunks(index_data.get('chunks', []))
        self._chunks = prepared_chunks
        self._chunk_by_id = {chunk.chunk_id: chunk for chunk in prepared_chunks}
        self._chunk_token_cache = {chunk.chunk_id: set(tokenize(chunk.text)) for chunk in prepared_chunks}
        self._chunk_term_freq = {chunk.chunk_id: Counter(tokenize(chunk.text)) for chunk in prepared_chunks}
        self._rebuild_idf_stats()

        self._embedding_backend = str(index_data.get('embedding_backend', 'simple'))
        self._index_signature = signature
        self._is_ready = True

        logger.info(
            'Hybrid index built | chunks=%s backend=%s signature=%s',
            len(self._chunks),
            self._embedding_backend,
            self._index_signature,
        )

    async def retrieve(self, query: str, top_k: int | None = None, debug: bool | None = None) -> RetrievalOutput:
        await self.build_index()

        effective_top_k = max(1, top_k or settings.retrieval_top_k)
        debug_enabled = self.config.debug if debug is None else debug

        if not self._chunks:
            debug_info = RetrievalDebugInfo(
                query=query,
                indexed_chunks=0,
                candidate_top_k=self.config.candidate_top_k,
                keyword_hits=0,
                vector_hits=0,
                fused_hits=0,
                dedup_dropped=0,
                threshold_dropped=0,
                final_returned=0,
                miss_reason='no_indexed_chunks',
            )
            return RetrievalOutput(query=query, chunks=[], debug=debug_info if debug_enabled else None)

        query_variants = self._expand_query_variants(query)
        rerank_query = query_variants[-1][0] if query_variants else query

        search_batches: list[tuple[list[KeywordSearchResult], list[VectorSearchResult], float]] = []
        variant_stats: list[dict[str, int | float | str]] = []
        for variant_query, variant_weight in query_variants:
            query_tokens = tokenize(variant_query)
            keyword_variant = self._keyword_search(query_tokens, self.config.candidate_top_k)

            query_vector = await self.embedding_service.embed_query(variant_query, self._embedding_backend)
            vector_variant = self._vector_search(query_vector, self.config.candidate_top_k)

            search_batches.append((keyword_variant, vector_variant, variant_weight))
            variant_stats.append(
                {
                    'query': variant_query,
                    'weight': variant_weight,
                    'keyword_hits': len(keyword_variant),
                    'vector_hits': len(vector_variant),
                }
            )

        keyword_results = search_batches[0][0] if search_batches else []
        vector_results = search_batches[0][1] if search_batches else []

        fused_map = self._fuse_candidates(search_batches)
        fused_candidates = sorted(
            fused_map.values(),
            key=lambda item: float(item['fused_score']),
            reverse=True,
        )

        deduped_candidates, dedup_dropped = self._drop_near_duplicates(fused_candidates)

        rerank_inputs = [
            RerankInput(
                chunk=item['chunk'],
                fused_score=float(item['fused_score']),
                keyword_score=float(item['keyword_score']),
                vector_score=float(item['vector_score']),
                keyword_rank=item['keyword_rank'],
                vector_rank=item['vector_rank'],
            )
            for item in deduped_candidates[: self.config.rerank_pool_k]
            if isinstance(item.get('chunk'), IndexedChunk)
        ]

        reranked = self._reranker.rerank(
            query=rerank_query,
            candidates=rerank_inputs,
            top_k=max(effective_top_k * 3, self.config.rerank_pool_k),
        )

        filtered = [candidate for candidate in reranked if candidate.final_score >= self.config.min_context_score]
        threshold_dropped = max(0, len(reranked) - len(filtered))
        if not filtered:
            filtered = reranked[:effective_top_k]

        prioritized = self._apply_source_priority(
            query=rerank_query,
            filtered_candidates=filtered,
            reranked_candidates=reranked,
            top_k=effective_top_k,
            enabled=self.config.source_priority_enabled,
            min_score=self.config.source_priority_min_score,
        )
        final = prioritized[:effective_top_k]
        output_chunks = [self._to_retrieved_chunk(item) for item in final]

        miss_reason = self._build_miss_reason(output_chunks, keyword_results, vector_results, threshold_dropped)

        debug_info = None
        if debug_enabled:
            debug_info = RetrievalDebugInfo(
                query=query,
                indexed_chunks=len(self._chunks),
                candidate_top_k=self.config.candidate_top_k,
                keyword_hits=len(keyword_results),
                vector_hits=len(vector_results),
                fused_hits=len(fused_candidates),
                dedup_dropped=dedup_dropped,
                threshold_dropped=threshold_dropped,
                final_returned=len(output_chunks),
                miss_reason=miss_reason,
                top_keyword_chunk_ids=[item.chunk.chunk_id for item in keyword_results[:10]],
                top_vector_chunk_ids=[item.chunk.chunk_id for item in vector_results[:10]],
                top_fused_chunk_ids=[
                    item['chunk'].chunk_id
                    for item in fused_candidates[:10]
                    if isinstance(item.get('chunk'), IndexedChunk)
                ],
                top_final_chunk_ids=[item.chunk_id for item in output_chunks],
                expanded_queries=[item[0] for item in query_variants],
                variant_stats=variant_stats,
            )
            logger.info('Retrieval debug: %s', asdict(debug_info))

        return RetrievalOutput(query=query, chunks=output_chunks, debug=debug_info)

    def _build_signature(self, index_data: dict[str, Any]) -> str:
        built_at = str(index_data.get('built_at', 'none'))
        chunks_count = len(index_data.get('chunks', []))
        model = str(index_data.get('embedding_model', 'unknown'))
        backend = str(index_data.get('embedding_backend', 'unknown'))
        return f'{built_at}|{chunks_count}|{model}|{backend}'

    def _prepare_chunks(self, chunks_payload: list[dict[str, Any]]) -> list[IndexedChunk]:
        prepared: list[IndexedChunk] = []
        seen_fingerprints: set[str] = set()

        for index, payload in enumerate(chunks_payload, start=1):
            text = str(payload.get('text', '')).strip()
            if not text:
                continue

            source_id = str(payload.get('source_id', 'unknown'))
            source_name = str(payload.get('source_name', source_id))
            chunk_id = str(payload.get('chunk_id', f'{source_id}_chunk_{index:03d}'))
            vector_payload = payload.get('vector', [])
            if not isinstance(vector_payload, list):
                vector_payload = []

            fingerprint = hashlib.sha1(normalize_text(text).encode('utf-8')).hexdigest()
            if fingerprint in seen_fingerprints:
                continue
            seen_fingerprints.add(fingerprint)

            prepared.append(
                IndexedChunk(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    source_name=source_name,
                    text=text,
                    vector=[float(value) for value in vector_payload],
                    metadata=payload.get('metadata', {}),
                )
            )

        return prepared

    def _rebuild_idf_stats(self) -> None:
        if not self._chunks:
            self._avg_doc_len = 0.0
            self._idf = {}
            return

        total_terms = 0
        doc_freq: dict[str, int] = {}
        for chunk in self._chunks:
            term_counter = self._chunk_term_freq.get(chunk.chunk_id, Counter())
            total_terms += sum(term_counter.values())
            for term in term_counter.keys():
                doc_freq[term] = doc_freq.get(term, 0) + 1

        num_docs = max(1, len(self._chunks))
        self._avg_doc_len = total_terms / num_docs if num_docs else 0.0
        self._idf = {
            term: math.log(1 + (num_docs - df + 0.5) / (df + 0.5))
            for term, df in doc_freq.items()
            if df > 0
        }

    def _keyword_search(self, query_terms: list[str], top_k: int) -> list[KeywordSearchResult]:
        if not query_terms:
            return []

        k1 = 1.2
        b = 0.75
        avg_doc_len = max(1.0, self._avg_doc_len)
        scores: list[KeywordSearchResult] = []

        for chunk in self._chunks:
            term_counter = self._chunk_term_freq.get(chunk.chunk_id, Counter())
            doc_len = max(1, sum(term_counter.values()))
            score = 0.0

            for term in query_terms:
                tf = term_counter.get(term, 0)
                if tf <= 0:
                    continue
                idf = self._idf.get(term, 0.0)
                denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
                score += idf * ((tf * (k1 + 1)) / max(1e-9, denominator))

            if score > 0:
                scores.append(KeywordSearchResult(chunk=chunk, score=score))

        scores.sort(key=lambda item: item.score, reverse=True)
        return scores[: max(1, top_k)]

    def _vector_search(self, query_vector: list[float], top_k: int) -> list[VectorSearchResult]:
        if not query_vector:
            return []

        scores: list[VectorSearchResult] = []
        for chunk in self._chunks:
            score = self._cosine_similarity(query_vector, chunk.vector)
            if score <= 0:
                continue
            scores.append(VectorSearchResult(chunk=chunk, score=score))

        scores.sort(key=lambda item: item.score, reverse=True)
        return scores[: max(1, top_k)]

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0

        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(v * v for v in left))
        right_norm = math.sqrt(sum(v * v for v in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    def _fuse_candidates(
        self,
        search_batches: list[tuple[list[KeywordSearchResult], list[VectorSearchResult], float]],
    ) -> dict[str, dict[str, object]]:
        fused: dict[str, dict[str, object]] = {}

        for batch_index, (keyword_results, vector_results, variant_weight) in enumerate(search_batches):
            for rank, item in enumerate(keyword_results, start=1):
                state = fused.setdefault(
                    item.chunk.chunk_id,
                    {
                        'chunk': item.chunk,
                        'fused_score': 0.0,
                        'keyword_score': 0.0,
                        'vector_score': 0.0,
                        'keyword_rank': None,
                        'vector_rank': None,
                    },
                )
                state['keyword_score'] = max(float(state['keyword_score']), item.score)
                if batch_index == 0:
                    state['keyword_rank'] = rank
                state['fused_score'] = float(state['fused_score']) + (
                    variant_weight * self.config.keyword_weight / (self.config.rrf_k + rank)
                )

            for rank, item in enumerate(vector_results, start=1):
                state = fused.setdefault(
                    item.chunk.chunk_id,
                    {
                        'chunk': item.chunk,
                        'fused_score': 0.0,
                        'keyword_score': 0.0,
                        'vector_score': 0.0,
                        'keyword_rank': None,
                        'vector_rank': None,
                    },
                )
                state['vector_score'] = max(float(state['vector_score']), item.score)
                if batch_index == 0:
                    state['vector_rank'] = rank
                state['fused_score'] = float(state['fused_score']) + (
                    variant_weight * self.config.vector_weight / (self.config.rrf_k + rank)
                )

        return fused

    def _expand_query_variants(self, query: str) -> list[tuple[str, float]]:
        normalized_query = normalize_text(query)
        expansion_terms: list[str] = []
        for trigger, mapped_terms in self.QUERY_EXPANSION_RULES.items():
            if trigger in normalized_query:
                expansion_terms.extend(mapped_terms)

        if 'mo dun' in normalized_query:
            expansion_terms.extend(('module', 'resume', 'cover letter', 'interview'))

        if not expansion_terms:
            return [(query, 1.0)]

        dedup_terms = list(dict.fromkeys(expansion_terms))
        expanded_query = f"{query} {' '.join(dedup_terms)}"
        return [(query, 1.0), (expanded_query, 0.9)]

    def _apply_source_priority(
        self,
        query: str,
        filtered_candidates: list[RerankResult],
        reranked_candidates: list[RerankResult],
        top_k: int,
        enabled: bool,
        min_score: float,
    ) -> list[RerankResult]:
        if not enabled:
            return filtered_candidates

        preferred_patterns = self._get_preferred_source_patterns(query)
        if not preferred_patterns:
            return filtered_candidates

        prioritized: list[RerankResult] = []
        seen_chunk_ids: set[str] = set()

        def add_if_new(candidate: RerankResult) -> None:
            if candidate.chunk.chunk_id in seen_chunk_ids:
                return
            prioritized.append(candidate)
            seen_chunk_ids.add(candidate.chunk.chunk_id)

        soft_threshold = max(0.0, min_score)
        for candidate in reranked_candidates:
            source_norm = normalize_text(candidate.chunk.source_name)
            if candidate.final_score < soft_threshold:
                continue
            if any(pattern in source_norm for pattern in preferred_patterns):
                add_if_new(candidate)
            if len(prioritized) >= top_k:
                return prioritized

        for candidate in filtered_candidates:
            add_if_new(candidate)
            if len(prioritized) >= top_k:
                return prioritized

        for candidate in reranked_candidates:
            add_if_new(candidate)
            if len(prioritized) >= top_k:
                return prioritized

        return prioritized

    def _get_preferred_source_patterns(self, query: str) -> list[str]:
        query_norm = normalize_text(query)
        patterns: list[str] = []
        for triggers, source_patterns in self.SOURCE_PRIORITY_RULES:
            if any(trigger in query_norm for trigger in triggers):
                patterns.extend(source_patterns)
        return list(dict.fromkeys(patterns))

    def _drop_near_duplicates(
        self,
        fused_candidates: list[dict[str, object]],
    ) -> tuple[list[dict[str, object]], int]:
        deduped: list[dict[str, object]] = []
        dropped = 0

        for candidate in fused_candidates:
            chunk = candidate['chunk']
            if not isinstance(chunk, IndexedChunk):
                continue

            if any(self._is_near_duplicate(chunk, existing['chunk']) for existing in deduped):
                dropped += 1
                continue
            deduped.append(candidate)

        return deduped, dropped

    def _is_near_duplicate(self, chunk_a: IndexedChunk, chunk_b: IndexedChunk) -> bool:
        if chunk_a.chunk_id == chunk_b.chunk_id:
            return True

        if chunk_a.source_id != chunk_b.source_id:
            return False

        tokens_a = self._chunk_token_cache.get(chunk_a.chunk_id, set())
        tokens_b = self._chunk_token_cache.get(chunk_b.chunk_id, set())
        if not tokens_a or not tokens_b:
            return False

        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        jaccard = intersection / max(1, union)
        return jaccard >= self.config.dedup_jaccard_threshold

    def _to_retrieved_chunk(self, candidate: RerankResult) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=candidate.chunk.chunk_id,
            source_id=candidate.chunk.source_id,
            source_name=candidate.chunk.source_name,
            text=candidate.chunk.text,
            final_score=candidate.final_score,
            fused_score=candidate.fused_score,
            keyword_score=candidate.keyword_score,
            vector_score=candidate.vector_score,
            keyword_rank=candidate.keyword_rank,
            vector_rank=candidate.vector_rank,
            metadata=candidate.chunk.metadata,
            features=candidate.features,
        )

    def _build_miss_reason(
        self,
        output_chunks: list[RetrievedChunk],
        keyword_results: list[KeywordSearchResult],
        vector_results: list[VectorSearchResult],
        threshold_dropped: int,
    ) -> str | None:
        if output_chunks:
            return None
        if not keyword_results and not vector_results:
            return 'no_keyword_or_vector_hits'
        if threshold_dropped > 0:
            return 'all_candidates_below_threshold'
        if not vector_results:
            return 'vector_channel_empty'
        if not keyword_results:
            return 'keyword_channel_empty'
        return 'rerank_removed_all_candidates'


__all__ = [
    'HybridRetriever',
    'HybridRetrievalConfig',
    'KeywordSearchResult',
    'VectorSearchResult',
    'RetrievedChunk',
    'RetrievalDebugInfo',
    'RetrievalOutput',
]
