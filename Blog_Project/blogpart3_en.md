# Part 3 - Retrieval Owner: Designing Hybrid Retrieval for the RAG Chatbot

## 1. The role of Retrieval in this project

<p align="center"><img src="imgpart3.png" width="760"></p>
<p align="center"><em>Figure 3.1. Retrieval.</em></p>

In this project architecture, Retrieval is the layer between **Indexing** and **RAG Core**:

1. Receive the `index snapshot` from `IndexingService`.
2. Retrieve the most relevant chunks for the user question.
3. Re-rank results to reduce noise before passing context to the LLM prompt.

The handoff to RAG Core happens in `app/rag_core/context/context_builder.py`: it only returns final chunks with `source_id`, `source_name`, `chunk_id`, `text`, and `score`.

## 2. Implemented retrieval pipeline

The main implementation is in `app/retrieval/hybrid/__init__.py` with the `HybridRetriever` class.

### Step 1: Build/refresh the retrieval internal index

- Call `indexing_service.sync_index()` to synchronize the latest data.
- Get the snapshot via `get_index_snapshot()`.
- Normalize chunk payloads into `IndexedChunk` (`chunk_id`, `source_id`, `source_name`, `text`, `vector`, `metadata`).
- Remove exact duplicates with fingerprint `sha1(normalize_text(text))`.
- Rebuild keyword-channel statistics: term frequency, IDF, and average document length.

### Step 2: Query expansion

The retriever uses rule-based query expansion (`QUERY_EXPANSION_RULES`) to improve recall for specific domain phrases such as:

- `giấy phép` -> `license`, `licensed`
- `khóa học` -> `course`, `curriculum`
- `mô đun/module` -> `resume`, `cover letter`, `interview`, ...

### Step 3: Hybrid retrieval (Keyword + Vector)

Hybrid search combines keyword-search results and vector-search results. Its main advantages are:

- Search efficiency: Sparse retrieval (keyword search) finds results based on lexical overlap, while dense retrieval (vector search) uses more complex representations (for example neural embeddings) to compare texts.
- Accuracy: Sparse retrieval is often strong for exact term matching, while dense retrieval can provide better semantic matching from learned representations.
- Result diversity: Combining sparse and dense retrieval provides a richer set of results, from lexical matches to semantic matches.
- Flexibility: The balance between sparse and dense retrieval can be tuned based on application needs and data characteristics.

#### 3.1 Keyword search

- Uses a lightweight in-house BM25 implementation (`_keyword_search`), without external dependencies.
- Tokenization goes through `normalize_text()` + regex `\w+` (file `app/retrieval/text_utils.py`).

#### 3.2 Vector search

This is a content search technique using vector embeddings to compute similarity.

- Embed the query using `EmbeddingService.embed_query()` with the same backend used during indexing.
- Compute cosine similarity against each chunk vector (`_cosine_similarity`).

### Step 4: Fusion with weighted RRF

The two channels are fused with weighted Reciprocal Rank Fusion:

- `keyword_weight = 0.45`
- `vector_weight = 0.55`
- `rrf_k = 60`

Idea: a chunk ranked high in either channel gets rewarded, making ranking more stable than relying on one absolute score.

### Step 5: Noise reduction before reranking

1. **Near-duplicate removal** using token-level Jaccard (`dedup_jaccard_threshold = 0.88`) within the same source.
2. **Candidate pool** limited by `rerank_pool_k`.

### Step 6: Heuristic rerank

The reranker in `app/retrieval/reranker/__init__.py` scores by feature combination:

- `fused_norm`: normalized fusion score
- `coverage`: query token coverage inside the chunk
- `phrase_hit`: whether the normalized query appears as an exact phrase in the chunk
- `source_score`: source relevance score from rules
- `length_score`: preference for reasonable chunk length

Current linear formula:

`final_score = 0.44*fused_norm + 0.22*coverage + 0.08*phrase_hit + 0.22*source_score + 0.04*length_score`

Besides boosting the right domain source, the system also applies a **mismatch penalty** (`source_mismatch_penalty_factor = 0.15`) when a query triggers a source hint but the chunk source is off-domain.

### Step 7: Threshold + source priority + fallback

- Filter by `min_context_score = 0.08`.
- If filtered results are empty: fallback to top reranked candidates to avoid empty context.
- `source_priority_enabled = True`: when query matches source-priority rules, preferred-domain sources are promoted if they pass `source_priority_min_score = 0.14`.

### Step 8: Output to RAG Core

Final output is a list of `RetrievedChunk` including:

- `chunk_id`, `source_id`, `source_name`, `text`
- `final_score`
- component scores: `fused_score`, `keyword_score`, `vector_score`
- per-channel ranks + `features` for debugging

## 3. Official retrieval configuration (default)

Defined in `app/shared/configs/settings.py`:

- `retrieval_top_k = 5`
- `retrieval_candidate_top_k = 30`
- `retrieval_rerank_pool_k = 20`
- `retrieval_keyword_weight = 0.45`
- `retrieval_vector_weight = 0.55`
- `retrieval_rrf_k = 60`
- `retrieval_min_context_score = 0.08`
- `retrieval_dedup_jaccard_threshold = 0.88`
- `retrieval_source_priority_enabled = True`
- `retrieval_source_priority_min_score = 0.14`
- `retrieval_source_mismatch_penalty_factor = 0.15`
- `retrieval_debug = False`

Benchmark/quality gate:

- `retrieval_benchmark_top_k = 5`
- `retrieval_quality_hit_rate_threshold = 0.75`
- `retrieval_quality_mrr_threshold = 0.55`
- `retrieval_stability_runs = 2`

## 4. Benchmark and Definition of Done

Benchmark script: `app/retrieval/benchmark`.

Run command:

```bash
python3 -m app.retrieval.benchmark --top-k 5 --output reports/retrieval_report.json
```

Current sample report at `Project/reports/retrieval_report.json`:

- `total_questions`: **31**
- `hit_rate_at_k`: **0.9355**
- `precision_at_k`: **0.4258**
- `mean_reciprocal_rank (MRR)`: **0.9032**
- `passes_quality_gate`: **true**
- `stable_across_runs`: **true** (`stability_runs = 2`)
- `miss_buckets`: `source_not_hit: 1`, `keyword_not_hit: 1`


## 5. Hit/miss debugging mechanism

When `debug=True`, `HybridRetriever` returns `RetrievalDebugInfo` including:

- Hit counts per channel: keyword/vector/fused
- Number of chunks dropped by dedup and threshold
- Top chunk IDs at each stage
- Used query variants
- `miss_reason` when no relevant output is found

Main `miss_reason` values in code:

- `no_indexed_chunks`
- `no_keyword_or_vector_hits`
- `all_candidates_below_threshold`
- `vector_channel_empty`
- `keyword_channel_empty`
- `rerank_removed_all_candidates`

Additionally, the benchmark layer assigns analysis buckets such as `source_not_hit`, `keyword_not_hit`, and `relevant_chunk_outside_top_k`.

## 6. Conclusion from the Retrieval Owner perspective

The retrieval part of this project follows a practical MVP approach while staying extensible:

- **Hybrid search** balances precision and semantic recall.
- **Fusion + rerank + dedup + source-priority** reduce noisy context.
- **Benchmark + quality gate + stability check** provide measurable quality tracking.
