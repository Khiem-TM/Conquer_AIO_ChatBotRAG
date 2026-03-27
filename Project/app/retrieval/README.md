# Retrieval Owner - Hybrid + Fusion + Rerank

## Mục tiêu

Tối ưu khả năng truy xuất đúng đoạn văn bản liên quan trước khi sinh câu trả lời.

## Luồng chính đã triển khai

1. Đồng bộ và đọc snapshot index từ `app/indexing` qua `IndexingService`.
2. Hybrid retrieval gồm:
- Keyword channel (BM25 nhẹ trên tập chunk đã index).
- Vector channel (cosine similarity trên vector đã được indexing lưu).
3. Fusion bằng RRF có trọng số `keyword_weight` và `vector_weight`.
4. Giảm nhiễu:
- Xóa exact-duplicate theo fingerprint chuẩn hóa text.
- Loại near-duplicate theo ngưỡng Jaccard token.
- Lọc theo `min_context_score`.
5. Rerank heuristic để ưu tiên ngữ cảnh đúng ý hỏi.
6. Bàn giao chunk đã xếp hạng cho RAG Core qua `ContextBuilder`.

## Cấu hình retrieval chính thức

Các tham số được cấu hình tại `app/shared/configs/settings.py`:

- `retrieval_top_k`
- `retrieval_candidate_top_k`
- `retrieval_rerank_pool_k`
- `retrieval_keyword_weight`
- `retrieval_vector_weight`
- `retrieval_rrf_k`
- `retrieval_min_context_score`
- `retrieval_dedup_jaccard_threshold`
- `retrieval_source_priority_enabled`
- `retrieval_source_priority_min_score`
- `retrieval_source_mismatch_penalty_factor`
- `retrieval_debug`

Thiết lập benchmark/DoD:

- `retrieval_benchmark_path`
- `retrieval_benchmark_top_k`
- `retrieval_quality_hit_rate_threshold`
- `retrieval_quality_mrr_threshold`
- `retrieval_stability_runs`

## Benchmark retrieval

Chạy benchmark:

```bash
python3 -m app.retrieval.benchmark --top-k 5 --output reports/retrieval_report.json
```

Output chứa:

- `hit_rate_at_k`, `precision_at_k`, `mean_reciprocal_rank`
- `passes_quality_gate` theo ngưỡng quality gate
- `stable_across_runs` cho kiểm tra ổn định nhiều lần chạy
- `miss_buckets` để phân tích hit/miss
- `details` theo từng câu hỏi

## Cơ chế debug hit/miss

Mỗi truy vấn benchmark lấy `retrieval_debug` gồm:

- số lượng hit theo keyword/vector/fusion
- số chunk bị loại do dedup và threshold
- top chunk id theo từng giai đoạn
- `miss_reason` để truy vết nguyên nhân miss

Các `miss_reason` chính:

- `no_indexed_chunks`
- `no_keyword_or_vector_hits`
- `all_candidates_below_threshold`
- `source_not_hit`
- `keyword_not_hit`
- `relevant_chunk_outside_top_k`
