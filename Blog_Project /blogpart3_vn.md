# Phần 3 - Retrieval Owner: Thiết kế Hybrid Retrieval cho RAG Chatbot

## 1. Vai trò của Retrieval trong project

<p align="center"><img src="imgpart3.png" width="760"></p>
<p align="center"><em>Hình 3.1. Retrival.</em></p>

Trong kiến trúc của project này, Retrieval là tầng đứng giữa **Indexing** và **RAG Core**:

1. Nhận `index snapshot` từ `IndexingService`.
2. Truy xuất các chunk liên quan nhất cho câu hỏi người dùng.
3. Xếp hạng lại để giảm nhiễu trước khi đưa vào prompt cho LLM.

Điểm bàn giao sang RAG Core nằm ở `app/rag_core/context/context_builder.py`: chỉ lấy ra các chunk cuối cùng với `source_id`, `source_name`, `chunk_id`, `text`, `score`.

## 2. Pipeline retrieval đã triển khai

Triển khai chính nằm trong `app/retrieval/hybrid/__init__.py` với class `HybridRetriever`.

### Bước 1: Build/refresh chỉ mục nội bộ cho retrieval

- Gọi `indexing_service.sync_index()` để đồng bộ dữ liệu mới nhất.
- Lấy snapshot bằng `get_index_snapshot()`.
- Chuẩn hóa dữ liệu chunk sang `IndexedChunk` (`chunk_id`, `source_id`, `source_name`, `text`, `vector`, `metadata`).
- Xóa exact duplicate bằng fingerprint `sha1(normalize_text(text))`.
- Rebuild thống kê cho kênh keyword: term frequency, IDF, average document length.

### Bước 2: Query expansion (mở rộng truy vấn)

Retriever có rule-based query expansion (`QUERY_EXPANSION_RULES`) để tăng recall cho các cụm domain cụ thể như:

- `giấy phép` -> `license`, `licensed`
- `khóa học` -> `course`, `curriculum`
- `mô đun/module` -> `resume`, `cover letter`, `interview`, ...

### Bước 3: Hybrid retrieval (Keyword + Vector)

Hybrid search là sự kết hợp giữa kết quả tìm kiếm được từ keyword search và kết quả của vector search. Ưu điểm to lớn của nó chính là: 

- Hiệu suất tìm kiếm: Sparse retrieval (keyword search) thường được sử dụng để tìm kiếm theo từ khóa và trả về các kết quả dựa trên độ tương đồng từ khoá. Trong khi đó, dense retrieval (vector search) sử dụng mô hình dữ liệu phức tạp hơn như mạng neural để đánh giá độ tương đồng giữa các văn bản.
- Độ chính xác: Sparse retrieval thường có độ chính xác cao trong việc đánh giá sự tương đồng giữa các từ khóa và văn bản, trong khi dense retrieval có thể cung cấp kết quả chính xác hơn bằng cách tính toán các biểu diễn mặc định hoặc được học từ dữ liệu.
- Đa dạng kết quả: Khi kết hợp cả sparse và dense retrieval, hệ thống có khả năng trả về một loạt các kết quả phong phú, từ các kết quả dựa trên từ khóa đến các kết quả dựa trên sự tương đồng ngữ nghĩa. Điều này giúp cung cấp thông tin đa dạng và phong phú hơn.
- Tính linh hoạt: Có thể điều chỉnh tỷ lệ giữa sparse và dense retrieval tùy thuộc vào yêu cầu cụ thể của ứng dụng hoặc loại dữ liệu.

#### 3.1 Keyword search

- Dùng BM25 lightweight tự cài đặt (`_keyword_search`), không phụ thuộc thư viện ngoài.
- Tokenization đi qua `normalize_text()` + regex `\w+` (file `app/retrieval/text_utils.py`).

#### 3.2 Vector search

Đây là kỹ thuật tìm kiếm nội dung bằng cách sử dụng vector embedding để tính similarity.

- Embedding query bằng `EmbeddingService.embed_query()` theo đúng backend đã dùng lúc indexing.
- Tính cosine similarity với vector của từng chunk (`_cosine_similarity`).

### Bước 4: Fusion bằng Weighted RRF

Hai kênh được hợp nhất bằng Reciprocal Rank Fusion có trọng số:

- `keyword_weight = 0.45`
- `vector_weight = 0.55`
- `rrf_k = 60`

Ý tưởng: chunk có thứ hạng cao ở bất kỳ kênh nào đều được cộng điểm, nên ổn định hơn so với chỉ dựa vào một score tuyệt đối.

### Bước 5: Giảm nhiễu trước khi rerank

1. **Near-duplicate removal** theo Jaccard token (`dedup_jaccard_threshold = 0.88`) trong cùng source.
2. **Candidate pool** giới hạn theo `rerank_pool_k`.

### Bước 6: Heuristic rerank

Reranker tại `app/retrieval/reranker/__init__.py` chấm điểm theo tổ hợp feature:

- `fused_norm`: điểm fusion đã chuẩn hóa
- `coverage`: độ phủ token query trong chunk
- `phrase_hit`: query chuẩn hóa có xuất hiện nguyên cụm trong chunk hay không
- `source_score`: độ phù hợp source theo rule
- `length_score`: ưu tiên chunk có độ dài phù hợp

Công thức tuyến tính hiện tại:

`final_score = 0.44*fused_norm + 0.22*coverage + 0.08*phrase_hit + 0.22*source_score + 0.04*length_score`

Ngoài boosting source đúng domain, hệ thống còn có **mismatch penalty** (`source_mismatch_penalty_factor = 0.15`) để phạt source sai khi query đã kích hoạt source hint.

### Bước 7: Threshold + source priority + fallback

- Lọc theo `min_context_score = 0.08`.
- Nếu sau lọc bị rỗng: fallback lấy top đầu từ reranked list để không trả về context rỗng.
- `source_priority_enabled = True`: khi query khớp rule source ưu tiên, hệ thống kéo source đúng domain lên trước nếu đạt `source_priority_min_score = 0.14`.

### Bước 8: Trả output cho RAG Core

Kết quả cuối là danh sách `RetrievedChunk` gồm:

- `chunk_id`, `source_id`, `source_name`, `text`
- `final_score`
- score thành phần: `fused_score`, `keyword_score`, `vector_score`
- rank theo từng kênh + `features` để debug

## 3. Cấu hình retrieval chính thức (default)

Khai báo tại `app/shared/configs/settings.py`:

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

## 4. Benchmark và Definition of Done

Script benchmark: `app/retrieval/benchmark`.

Lệnh chạy:

```bash
python3 -m app.retrieval.benchmark --top-k 5 --output reports/retrieval_report.json
```

Report mẫu hiện có tại `Project/reports/retrieval_report.json`:

- `total_questions`: **31**
- `hit_rate_at_k`: **0.9355**
- `precision_at_k`: **0.4258**
- `mean_reciprocal_rank (MRR)`: **0.9032**
- `passes_quality_gate`: **true**
- `stable_across_runs`: **true** (`stability_runs = 2`)
- `miss_buckets`: `source_not_hit: 1`, `keyword_not_hit: 1`

## 5. Cơ chế debug hit/miss

Khi bật `debug=True`, `HybridRetriever` trả `RetrievalDebugInfo` gồm:

- Số lượng hit từng kênh: keyword/vector/fused
- Số chunk bị loại do dedup và threshold
- Top chunk ID ở từng stage
- Query variants đã dùng
- `miss_reason` nếu không có kết quả phù hợp

Các `miss_reason` chính trong code:

- `no_indexed_chunks`
- `no_keyword_or_vector_hits`
- `all_candidates_below_threshold`
- `vector_channel_empty`
- `keyword_channel_empty`
- `rerank_removed_all_candidates`

Ngoài ra benchmark layer còn gán thêm các bucket phân tích chất lượng như `source_not_hit`, `keyword_not_hit`, `relevant_chunk_outside_top_k`.

## 6. Kết luận từ góc nhìn Retrieval Owner

Phần retrieval của project đã đi theo hướng thực dụng cho MVP nhưng vẫn đủ chắc để mở rộng:

- Có **hybrid search** để cân bằng precision và semantic recall.
- Có **fusion + rerank + dedup + source-priority** để giảm nhiễu context.
- Có **benchmark + quality gate + stability check** để theo dõi chất lượng định lượng.

