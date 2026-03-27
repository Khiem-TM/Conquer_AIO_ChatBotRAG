from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

from app.retrieval.hybrid import HybridRetriever, RetrievalOutput
from app.retrieval.text_utils import tokenize
from app.shared.configs import settings
from app.shared.utils import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class BenchmarkSample:
    question: str
    expected_keywords: list[str] = field(default_factory=list)
    expected_source_names: list[str] = field(default_factory=list)
    expected_chunk_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SampleReport:
    question: str
    hit: bool
    first_relevant_rank: int | None
    relevant_in_top_k: int
    top_chunks: list[dict[str, str | float]]
    miss_reason: str | None = None
    retrieval_debug: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class BenchmarkReport:
    total_questions: int
    top_k: int
    hit_rate_at_k: float
    precision_at_k: float
    mean_reciprocal_rank: float
    passes_quality_gate: bool
    quality_gate: dict[str, float]
    stable_across_runs: bool
    stability_runs: int
    miss_buckets: dict[str, int]
    details: list[SampleReport]


class RetrievalBenchmark:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever

    async def run(self, samples: list[BenchmarkSample], top_k: int) -> BenchmarkReport:
        if not samples:
            return BenchmarkReport(
                total_questions=0,
                top_k=top_k,
                hit_rate_at_k=0.0,
                precision_at_k=0.0,
                mean_reciprocal_rank=0.0,
                passes_quality_gate=False,
                quality_gate={
                    'hit_rate_threshold': settings.retrieval_quality_hit_rate_threshold,
                    'mrr_threshold': settings.retrieval_quality_mrr_threshold,
                },
                stable_across_runs=True,
                stability_runs=1,
                miss_buckets={},
                details=[],
            )

        reports: list[SampleReport] = []
        hit_count = 0
        precision_sum = 0.0
        reciprocal_sum = 0.0
        miss_buckets: dict[str, int] = {}

        for sample in samples:
            retrieval = await self.retriever.retrieve(query=sample.question, top_k=top_k, debug=True)
            sample_report = self._evaluate_sample(sample=sample, retrieval=retrieval, top_k=top_k)
            reports.append(sample_report)

            if sample_report.hit:
                hit_count += 1
            precision_sum += sample_report.relevant_in_top_k / max(1, top_k)
            if sample_report.first_relevant_rank:
                reciprocal_sum += 1.0 / sample_report.first_relevant_rank

            if sample_report.miss_reason:
                miss_buckets[sample_report.miss_reason] = miss_buckets.get(sample_report.miss_reason, 0) + 1

        hit_rate = hit_count / len(samples)
        mrr = reciprocal_sum / len(samples)
        quality_gate = {
            'hit_rate_threshold': settings.retrieval_quality_hit_rate_threshold,
            'mrr_threshold': settings.retrieval_quality_mrr_threshold,
        }
        passed = (
            hit_rate >= quality_gate['hit_rate_threshold']
            and mrr >= quality_gate['mrr_threshold']
        )

        return BenchmarkReport(
            total_questions=len(samples),
            top_k=top_k,
            hit_rate_at_k=hit_rate,
            precision_at_k=precision_sum / len(samples),
            mean_reciprocal_rank=mrr,
            passes_quality_gate=passed,
            quality_gate=quality_gate,
            stable_across_runs=True,
            stability_runs=1,
            miss_buckets=miss_buckets,
            details=reports,
        )

    def _evaluate_sample(
        self,
        sample: BenchmarkSample,
        retrieval: RetrievalOutput,
        top_k: int,
    ) -> SampleReport:
        first_rank: int | None = None
        relevant_count = 0
        top_chunks: list[dict[str, str | float]] = []

        for rank, chunk in enumerate(retrieval.chunks[:top_k], start=1):
            is_relevant = self._is_relevant(sample, chunk)
            if is_relevant:
                relevant_count += 1
                if first_rank is None:
                    first_rank = rank

            top_chunks.append(
                {
                    'chunk_id': chunk.chunk_id,
                    'source_name': chunk.source_name,
                    'score': round(chunk.final_score, 4),
                }
            )

        miss_reason = None
        if first_rank is None:
            miss_reason = self._infer_miss_reason(sample=sample, retrieval=retrieval)

        return SampleReport(
            question=sample.question,
            hit=first_rank is not None,
            first_relevant_rank=first_rank,
            relevant_in_top_k=relevant_count,
            top_chunks=top_chunks,
            miss_reason=miss_reason,
            retrieval_debug=asdict(retrieval.debug) if retrieval.debug is not None else {},
        )

    def _infer_miss_reason(self, sample: BenchmarkSample, retrieval: RetrievalOutput) -> str:
        if not retrieval.chunks:
            if retrieval.debug and retrieval.debug.miss_reason:
                return retrieval.debug.miss_reason
            return 'no_chunk_returned'

        if sample.expected_source_names:
            expected_sources = {source.lower() for source in sample.expected_source_names}
            has_source_match = any(
                any(expected in (chunk.source_name or '').lower() for expected in expected_sources)
                for chunk in retrieval.chunks
            )
            if not has_source_match:
                return 'source_not_hit'

        if sample.expected_keywords:
            keyword_hits = 0
            for chunk in retrieval.chunks:
                text = str(getattr(chunk, 'text', ''))
                keyword_hits += self._count_keyword_hits(
                    expected_keywords=sample.expected_keywords,
                    text_norm=text.lower(),
                    text_tokens=set(tokenize(text)),
                )
            if keyword_hits == 0:
                return 'keyword_not_hit'

        if retrieval.debug and retrieval.debug.miss_reason:
            return retrieval.debug.miss_reason
        return 'relevant_chunk_outside_top_k'

    def _is_relevant(self, sample: BenchmarkSample, chunk: object) -> bool:
        chunk_id = getattr(chunk, 'chunk_id', '')
        source_name = str(getattr(chunk, 'source_name', '')).lower()
        text = str(getattr(chunk, 'text', ''))
        text_norm = text.lower()
        text_tokens = set(tokenize(text))
        source_match = False

        if sample.expected_chunk_ids and chunk_id in set(sample.expected_chunk_ids):
            return True

        if sample.expected_source_names:
            for source in sample.expected_source_names:
                if source.lower() in source_name:
                    source_match = True
                    break

        keyword_match = False
        matched = 0
        if sample.expected_keywords:
            matched = self._count_keyword_hits(
                expected_keywords=sample.expected_keywords,
                text_norm=text_norm,
                text_tokens=text_tokens,
            )
            keyword_match = matched >= max(1, len(sample.expected_keywords) // 2)

        if sample.expected_source_names and sample.expected_keywords:
            return source_match and (keyword_match or matched >= 1)
        if sample.expected_source_names:
            return source_match
        if sample.expected_keywords:
            return keyword_match

        return False

    def _count_keyword_hits(
        self,
        expected_keywords: list[str],
        text_norm: str,
        text_tokens: set[str],
    ) -> int:
        matched = 0
        for keyword in expected_keywords:
            keyword_norm = keyword.lower().strip()
            if not keyword_norm:
                continue
            if keyword_norm in text_norm:
                matched += 1
                continue

            keyword_tokens = tokenize(keyword)
            if not keyword_tokens:
                continue
            overlap = sum(1 for token in keyword_tokens if token in text_tokens)
            overlap_ratio = overlap / max(1, len(keyword_tokens))
            if overlap >= 1 and overlap_ratio >= 0.6:
                matched += 1

        return matched


async def arun_benchmark(
    retriever: HybridRetriever | None = None,
    samples_path: str | None = None,
    top_k: int | None = None,
    output_path: str | None = None,
) -> BenchmarkReport:
    retriever = retriever or HybridRetriever()
    await retriever.build_index(force_rebuild=True)

    samples = load_benchmark_samples(samples_path)
    evaluator = RetrievalBenchmark(retriever=retriever)
    effective_top_k = top_k or settings.retrieval_benchmark_top_k
    report = await evaluator.run(samples=samples, top_k=effective_top_k)

    stability_runs = max(1, settings.retrieval_stability_runs)
    stable = await _check_stability(retriever=retriever, samples=samples, top_k=effective_top_k, runs=stability_runs)
    report.stability_runs = stability_runs
    report.stable_across_runs = stable

    logger.info(
        'Benchmark done | total=%s top_k=%s hit_rate=%.3f mrr=%.3f pass=%s stable=%s miss=%s',
        report.total_questions,
        report.top_k,
        report.hit_rate_at_k,
        report.mean_reciprocal_rank,
        report.passes_quality_gate,
        report.stable_across_runs,
        report.miss_buckets,
    )

    if output_path:
        path = save_benchmark_report(report, output_path)
        logger.info('Benchmark report saved: %s', path)

    return report


def run_benchmark(
    retriever: HybridRetriever | None = None,
    samples_path: str | None = None,
    top_k: int | None = None,
    output_path: str | None = None,
) -> BenchmarkReport:
    return asyncio.run(
        arun_benchmark(
            retriever=retriever,
            samples_path=samples_path,
            top_k=top_k,
            output_path=output_path,
        )
    )


async def _check_stability(
    retriever: HybridRetriever,
    samples: list[BenchmarkSample],
    top_k: int,
    runs: int,
) -> bool:
    signatures: list[tuple[tuple[str, ...], ...]] = []
    for _ in range(runs):
        run_signature: list[tuple[str, ...]] = []
        for sample in samples:
            output = await retriever.retrieve(query=sample.question, top_k=top_k, debug=False)
            run_signature.append(tuple(chunk.chunk_id for chunk in output.chunks[:top_k]))
        signatures.append(tuple(run_signature))

    return all(signature == signatures[0] for signature in signatures[1:]) if signatures else True


def load_benchmark_samples(path: str | None = None) -> list[BenchmarkSample]:
    benchmark_path = _resolve_benchmark_path(path or settings.retrieval_benchmark_path)

    if benchmark_path.exists():
        payload = json.loads(benchmark_path.read_text(encoding='utf-8'))
        return [BenchmarkSample(**sample) for sample in payload]

    logger.warning('Benchmark sample file not found at %s. Fallback to built-in samples.', benchmark_path)
    return default_samples()


def _resolve_benchmark_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    fallback_candidates = [
        Path.cwd() / path,
        Path(__file__).resolve().parents[3] / path,
        Path(__file__).resolve().parent / 'samples.json',
    ]
    for item in fallback_candidates:
        if item.exists():
            return item

    return fallback_candidates[0]


def default_samples() -> list[BenchmarkSample]:
    return [
        BenchmarkSample(
            question='Bộ tứ Anscombe cho thấy điều gì trong phân tích dữ liệu?',
            expected_keywords=['anscombe', 'trực quan hóa', 'thống kê'],
            expected_source_names=['Part1-4_Minh_VN.md'],
        ),
        BenchmarkSample(
            question='V-Green cam kết mức chia sẻ doanh thu bao nhiêu?',
            expected_keywords=['750 đồng', 'kwh', 'chia sẻ doanh thu'],
            expected_source_names=['test.txt.txt'],
        ),
        BenchmarkSample(
            question='Nguyên tắc Data-Ink ratio nhấn mạnh điều gì?',
            expected_keywords=['data-ink', 'chartjunk', 'tối giản'],
            expected_source_names=['Part1-4_Minh_VN.md'],
        ),
        BenchmarkSample(
            question='What is the recommended alternative when pie chart has too many categories?',
            expected_keywords=['horizontal bar chart', 'pie chart'],
            expected_source_names=['Part1-4_Minh_EN.md'],
        ),
    ]


def save_benchmark_report(report: BenchmarkReport, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    serializable = asdict(report)
    output.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding='utf-8')
    return output


__all__ = [
    'BenchmarkReport',
    'BenchmarkSample',
    'RetrievalBenchmark',
    'SampleReport',
    'arun_benchmark',
    'default_samples',
    'load_benchmark_samples',
    'run_benchmark',
    'save_benchmark_report',
]
