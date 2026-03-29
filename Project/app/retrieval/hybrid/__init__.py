from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
import math
from typing import Any

from app.indexing import IndexingService
from app.indexing.embeddings import EmbeddingService
from app.retrieval.reranker import HeuristicReranker, LlmReranker, RerankInput
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
    debug: bool = False


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


@dataclass(slots=True)
class RetrievalOutput:
    query: str
    chunks: list[RetrievedChunk]
    debug: RetrievalDebugInfo | None = None


class HybridRetriever:
    """Generic local-first hybrid retriever.

    Design goals:
    - no dataset-specific filename rules
    - predictable local behavior
    - lightweight keyword + vector fusion
    - enough debug info to diagnose misses
    """

    def __init__(
        self,
        config: HybridRetrievalConfig | None = None,
        indexing_service: IndexingService | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.config = config or HybridRetrievalConfig()
        self.indexing_service = indexing_service or IndexingService()
        self.embedding_service = embedding_service or EmbeddingService()
        self._reranker = HeuristicReranker()
        self._llm_reranker = LlmReranker()
        self._chunks: list[IndexedChunk] = []
        self._chunk_tokens: dict[str, list[str]] = {}
        self._chunk_term_freq: dict[str, Counter[str]] = {}
        self._idf: dict[str, float] = {}
        self._avg_doc_len: float = 0.0
        self._index_signature: str = ''
        self._embedding_backend: str = 'simple'

    async def build_index(self, force_rebuild: bool = False) -> None:
        index_data = await self.indexing_service.get_index_snapshot()
        signature = self._build_signature(index_data)
        if not force_rebuild and signature == self._index_signature:
            return

        payload_chunks = list(index_data.get('chunks', []))
        self._chunks = []
        self._chunk_tokens.clear()
        self._chunk_term_freq.clear()

        for item in payload_chunks:
            metadata = dict(item.get('metadata', {}) or {})
            chunk = IndexedChunk(
                chunk_id=str(item.get('chunk_id', '')),
                source_id=str(item.get('source_id', '')),
                source_name=str(item.get('source_name', '')),
                text=str(item.get('text', '')),
                vector=list(item.get('vector', [])),
                metadata=metadata,
            )
            self._chunks.append(chunk)
            tokens = tokenize(chunk.text)
            self._chunk_tokens[chunk.chunk_id] = tokens
            self._chunk_term_freq[chunk.chunk_id] = Counter(tokens)

        self._embedding_backend = str(index_data.get('embedding_backend', 'simple'))
        self._rebuild_idf_stats()
        self._index_signature = signature
        logger.info('Hybrid index built | chunks=%s backend=%s', len(self._chunks), self._embedding_backend)

    async def retrieve(self, query: str, top_k: int | None = None, debug: bool | None = None) -> RetrievalOutput:
        await self.build_index()
        effective_top_k = max(1, top_k or settings.retrieval_top_k)
        debug_enabled = self.config.debug if debug is None else debug

        if not self._chunks:
            info = RetrievalDebugInfo(
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
            return RetrievalOutput(query=query, chunks=[], debug=info if debug_enabled else None)

        query_tokens = tokenize(query)
        keyword_results = self._keyword_search(query_tokens, self.config.candidate_top_k)
        query_vector = await self.embedding_service.embed_query(query, self._embedding_backend)
        vector_results = self._vector_search(query_vector, self.config.candidate_top_k)
        fused = self._fuse_results(keyword_results, vector_results)
        deduped, dedup_dropped = self._drop_near_duplicates(fused)

        rerank_inputs = [
            RerankInput(
                chunk=item['chunk'],
                fused_score=float(item['fused_score']),
                keyword_score=float(item['keyword_score']),
                vector_score=float(item['vector_score']),
                keyword_rank=item['keyword_rank'],
                vector_rank=item['vector_rank'],
            )
            for item in deduped[: self.config.rerank_pool_k]
        ]
        reranked = self._reranker.rerank(query=query, candidates=rerank_inputs, top_k=effective_top_k)

        output_chunks: list[RetrievedChunk] = []
        threshold_dropped = 0
        for item in reranked:
            llm_bonus = 0.0
            if settings.retrieval_enable_llm_reranker:
                llm_bonus = 0.1 * await self._llm_reranker.score(query, item.chunk)
            final_score = item.final_score + llm_bonus
            if final_score < self.config.min_context_score:
                threshold_dropped += 1
                continue
            output_chunks.append(
                RetrievedChunk(
                    chunk_id=item.chunk.chunk_id,
                    source_id=item.chunk.source_id,
                    source_name=item.chunk.source_name,
                    text=item.chunk.text,
                    final_score=final_score,
                    fused_score=item.fused_score,
                    keyword_score=item.keyword_score,
                    vector_score=item.vector_score,
                    keyword_rank=item.keyword_rank,
                    vector_rank=item.vector_rank,
                    metadata=dict(item.chunk.metadata),
                    features={**item.features, 'llm_bonus': llm_bonus},
                )
            )

        # Fallback: nếu tất cả candidates bị filter bởi threshold nhưng index còn nhỏ
        # (ít chunks hơn top_k*3), trả về chunk tốt nhất để LLM vẫn có context thay vì trả lời mù.
        if not output_chunks and reranked and len(self._chunks) <= max(effective_top_k * 3, 10):
            best = reranked[0]
            logger.debug(
                'Small-index fallback: returning top-1 chunk (score=%.4f) below threshold=%.3f',
                best.final_score, self.config.min_context_score,
            )
            output_chunks.append(
                RetrievedChunk(
                    chunk_id=best.chunk.chunk_id,
                    source_id=best.chunk.source_id,
                    source_name=best.chunk.source_name,
                    text=best.chunk.text,
                    final_score=best.final_score,
                    fused_score=best.fused_score,
                    keyword_score=best.keyword_score,
                    vector_score=best.vector_score,
                    keyword_rank=best.keyword_rank,
                    vector_rank=best.vector_rank,
                    metadata=dict(best.chunk.metadata),
                    features={**best.features, 'fallback': 1.0},
                )
            )
            threshold_dropped = max(0, threshold_dropped - 1)

        output_chunks.sort(key=lambda item: item.final_score, reverse=True)
        output_chunks = output_chunks[:effective_top_k]

        debug_info: RetrievalDebugInfo | None = None
        if debug_enabled:
            miss_reason = None
            if not output_chunks:
                if not keyword_results and not vector_results:
                    miss_reason = 'no_keyword_or_vector_hits'
                elif threshold_dropped:
                    miss_reason = 'all_candidates_below_threshold'
                else:
                    miss_reason = 'no_final_chunks'
            debug_info = RetrievalDebugInfo(
                query=query,
                indexed_chunks=len(self._chunks),
                candidate_top_k=self.config.candidate_top_k,
                keyword_hits=len(keyword_results),
                vector_hits=len(vector_results),
                fused_hits=len(fused),
                dedup_dropped=dedup_dropped,
                threshold_dropped=threshold_dropped,
                final_returned=len(output_chunks),
                miss_reason=miss_reason,
                top_keyword_chunk_ids=[item.chunk.chunk_id for item in keyword_results[:10]],
                top_vector_chunk_ids=[item.chunk.chunk_id for item in vector_results[:10]],
                top_fused_chunk_ids=[item['chunk'].chunk_id for item in fused[:10]],
                top_final_chunk_ids=[item.chunk_id for item in output_chunks],
            )
            logger.info('Retrieval debug: %s', asdict(debug_info))

        return RetrievalOutput(query=query, chunks=output_chunks, debug=debug_info)

    def _build_signature(self, index_data: dict[str, Any]) -> str:
        return '|'.join(
            [
                str(index_data.get('built_at', 'none')),
                str(index_data.get('embedding_backend', 'pending')),
                str(index_data.get('embedding_model', 'unknown')),
                str(len(index_data.get('chunks', []))),
            ]
        )

    def _rebuild_idf_stats(self) -> None:
        docs_count = max(1, len(self._chunks))
        doc_freq: Counter[str] = Counter()
        total_doc_len = 0
        for chunk in self._chunks:
            tokens = self._chunk_tokens[chunk.chunk_id]
            total_doc_len += len(tokens)
            doc_freq.update(set(tokens))
        self._avg_doc_len = total_doc_len / docs_count if docs_count else 0.0
        self._idf = {
            term: math.log((docs_count - freq + 0.5) / (freq + 0.5) + 1.0)
            for term, freq in doc_freq.items()
        }

    def _keyword_search(self, query_tokens: list[str], top_k: int) -> list[KeywordSearchResult]:
        if not query_tokens:
            return []
        results: list[KeywordSearchResult] = []
        k1 = 1.2
        b = 0.75
        for chunk in self._chunks:
            term_freq = self._chunk_term_freq.get(chunk.chunk_id, Counter())
            doc_len = len(self._chunk_tokens.get(chunk.chunk_id, []))
            score = 0.0
            for token in query_tokens:
                tf = term_freq.get(token, 0)
                if tf == 0:
                    continue
                idf = self._idf.get(token, 0.0)
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / max(1.0, self._avg_doc_len)))
                score += idf * (numerator / denominator)
            score += self._metadata_boost(query_tokens, chunk)
            if score > 0:
                results.append(KeywordSearchResult(chunk=chunk, score=score))
        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]

    def _vector_search(self, query_vector: list[float], top_k: int) -> list[VectorSearchResult]:
        if not query_vector:
            return []
        results: list[VectorSearchResult] = []
        for chunk in self._chunks:
            if not chunk.vector:
                continue
            score = self._cosine_similarity(query_vector, chunk.vector)
            if score > 0:
                results.append(VectorSearchResult(chunk=chunk, score=score))
        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]

    def _metadata_boost(self, query_tokens: list[str], chunk: IndexedChunk) -> float:
        if not settings.retrieval_enable_metadata_boost:
            return 0.0
        if not query_tokens:
            return 0.0
        file_terms = set(tokenize(chunk.source_name)) | set(tokenize(str(chunk.metadata.get('relative_path', ''))))
        if not file_terms:
            return 0.0
        overlap = len(set(query_tokens) & file_terms)
        return 0.12 * (overlap / max(1, len(set(query_tokens))))

    def _fuse_results(
        self,
        keyword_results: list[KeywordSearchResult],
        vector_results: list[VectorSearchResult],
    ) -> list[dict[str, Any]]:
        fused: dict[str, dict[str, Any]] = {}

        for rank, item in enumerate(keyword_results, start=1):
            fused.setdefault(
                item.chunk.chunk_id,
                {
                    'chunk': item.chunk,
                    'keyword_score': 0.0,
                    'vector_score': 0.0,
                    'keyword_rank': None,
                    'vector_rank': None,
                    'fused_score': 0.0,
                },
            )
            fused[item.chunk.chunk_id]['keyword_score'] = item.score
            fused[item.chunk.chunk_id]['keyword_rank'] = rank
            fused[item.chunk.chunk_id]['fused_score'] += self.config.keyword_weight * (1 / (self.config.rrf_k + rank))

        for rank, item in enumerate(vector_results, start=1):
            fused.setdefault(
                item.chunk.chunk_id,
                {
                    'chunk': item.chunk,
                    'keyword_score': 0.0,
                    'vector_score': 0.0,
                    'keyword_rank': None,
                    'vector_rank': None,
                    'fused_score': 0.0,
                },
            )
            fused[item.chunk.chunk_id]['vector_score'] = item.score
            fused[item.chunk.chunk_id]['vector_rank'] = rank
            fused[item.chunk.chunk_id]['fused_score'] += self.config.vector_weight * (1 / (self.config.rrf_k + rank))

        return sorted(fused.values(), key=lambda item: float(item['fused_score']), reverse=True)

    def _drop_near_duplicates(self, candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        unique: list[dict[str, Any]] = []
        unique_token_sets: list[set[str]] = []
        dropped = 0
        for item in candidates:
            chunk = item['chunk']
            token_set = set(self._chunk_tokens.get(chunk.chunk_id, []))
            duplicate = False
            for existing in unique_token_sets:
                if self._jaccard(token_set, existing) >= self.config.dedup_jaccard_threshold:
                    duplicate = True
                    dropped += 1
                    break
            if duplicate:
                continue
            unique.append(item)
            unique_token_sets.append(token_set)
        return unique, dropped

    def _jaccard(self, a: set[str], b: set[str]) -> float:
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        a_norm = math.sqrt(sum(x * x for x in a))
        b_norm = math.sqrt(sum(y * y for y in b))
        if a_norm == 0 or b_norm == 0:
            return 0.0
        return dot / (a_norm * b_norm)


__all__ = [
    'HybridRetriever',
    'HybridRetrievalConfig',
    'RetrievalOutput',
    'RetrievedChunk',
    'RetrievalDebugInfo',
]
