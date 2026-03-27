# Người 2 - Embedding + Indexing

## Mục tiêu

Thư mục `Project/app/indexing` là phần độc lập dành cho người 2 theo file PDF:

- chọn model embedding
- tạo vector từ dữ liệu đầu vào
- quản lý lifecycle của index
- bàn giao index cho tầng retrieval

Phần này được giữ tách biệt khỏi `api`, `rag_core`, `docker` để tránh conflict khi merge với các bạn khác.

## Nguyên tắc triển khai

- Không dùng LangChain
- Ưu tiên `Ollama 8B`
- Code chỉ nằm trong `app/indexing`
- Không sửa logic của người 3, người 4, người 5

## Cấu trúc hiện tại

### `config.py`

Cấu hình riêng cho indexing:

- `OLLAMA_BASE_URL`
- `EMBEDDING_MODEL`
- `REQUEST_TIMEOUT_SECONDS`
- `INDEX_DATA_INPUT_DIR`
- `INDEX_STORAGE_PATH`
- `EMBEDDING_DIMENSIONS`
- `INDEX_CHUNK_SIZE`
- `INDEX_CHUNK_OVERLAP`

### `schemas.py`

Định nghĩa response nội bộ của người 2:

- `IndexStatus`
- `IndexOperationResult`

Không phụ thuộc vào `app/shared/schemas` để tránh đụng phần contract của người khác.

### `embeddings/embedding_service.py`

Phần này chịu trách nhiệm tạo embedding:

- ưu tiên gọi Ollama
- nếu embedding endpoint chưa sẵn sàng thì fallback sang hashed embedding bằng Python thuần

### `vectorstore/local_index_store.py`

Phần này là local vector store tối giản:

- đọc dữ liệu nguồn
- chuẩn bị chunk records
- ghi index xuống file JSON
- quản lý payload của vector index

### `index_service.py`

Đây là lớp điều phối chính của người 2:

- `get_status()`
- `rebuild_index()`
- `sync_index()`
- `delete_source()`
- `get_index_snapshot()`

### `cli.py`

CLI độc lập để chạy phần indexing mà không cần sửa API của người khác.

## Model được chọn

Mặc định:

- `EMBEDDING_MODEL=llama3.1:8b`

Lý do:

- miễn phí khi chạy local với Ollama
- dễ cài đặt
- phù hợp yêu cầu đề bài

## Lifecycle của index

### `rebuild`

Dùng khi:

- thay đổi model embedding
- thay đổi logic chunk/index
- cần build lại toàn bộ

### `sync`

Dùng khi:

- có file mới
- file cũ thay đổi
- cần cập nhật index theo dữ liệu hiện tại

### `delete_source`

Xóa một `source_id` khỏi index để tránh lệch dữ liệu.

### `get_status`

Kiểm tra:

- số lượng source
- số lượng chunk
- model embedding
- thời điểm build gần nhất

### `get_index_snapshot`

Đây là điểm bàn giao cho người 3. Người 3 có thể lấy snapshot index này để làm retrieval, rerank và benchmark.

## Cách chạy độc lập

Từ thư mục `Project`:

```bash
python -m app.indexing.cli status
python -m app.indexing.cli rebuild
python -m app.indexing.cli sync
python -m app.indexing.cli snapshot
python -m app.indexing.cli delete-source <source_id>
```

## Ranh giới với các thành viên khác

### Người 1

Người 1 chuẩn hóa dữ liệu đầu vào. Người 2 chỉ tập trung vào embedding và index lifecycle.

### Người 3

Người 3 sẽ nhận `index snapshot` hoặc dữ liệu từ vector index để làm retrieval, fusion, rerank và benchmark.

### Người 4

Người 4 sẽ dùng output từ retrieval để ghép context, làm prompt và gọi model chat.

### Người 5

Người 5 phụ trách Docker, smoke test, local startup và UI. Phần của người 2 không chỉnh vào các file đó để tránh conflict.

## Kết luận

Phiên bản hiện tại là bản `person-2-only`:

- giữ đúng ownership theo PDF
- có code riêng cho embedding + indexing
- có tài liệu mô tả
- có CLI để demo độc lập
- hạn chế tối đa khả năng xung đột khi merge branch
