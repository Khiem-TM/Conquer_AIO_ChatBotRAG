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

## Chú thích trong code

Để teammate mở file ra là hiểu nhanh, các file code chính đã được thêm:

- module docstring ở đầu file để mô tả vai trò của file
- comment ngắn ở các đoạn dễ gây khó hiểu như:
  - fallback từ Ollama sang hashed embedding
  - logic sync theo `updated_at_ns`
  - lý do phải rebuild khi backend embedding thay đổi
  - cách chunk dài được tách có overlap

Mục tiêu của phần chú thích này là giúp đọc nhanh, không phải thay đổi logic.

## Note nhanh theo file

| File | Dùng để làm gì | Input chính | Output chính | Ghi chú |
|---|---|---|---|---|
| `config.py` | Chứa toàn bộ setting riêng của người 2 | Biến môi trường như `EMBEDDING_MODEL`, `INDEX_STORAGE_PATH` | `settings: IndexingSettings` | Tách khỏi `app/shared/configs` để không đụng lane của người khác |
| `schemas.py` | Định nghĩa model kết quả nội bộ cho indexing | Dữ liệu trạng thái index | `IndexStatus`, `IndexOperationResult` | Chỉ dùng trong `app/indexing` |
| `embeddings/embedding_service.py` | Tạo embedding cho text | `texts: list[str]`, `question: str` | `list[list[float]]`, `embedding_backend` | Ưu tiên Ollama, fallback hashed embedding |
| `vectorstore/local_index_store.py` | Quản lý dữ liệu index local | File nguồn, `index_data`, đường dẫn lưu | Chunk records, sources payload, file `index_store.json` | Đây là local store tối giản để demo |
| `index_service.py` | Điều phối lifecycle của index | File nguồn từ `data_input`, cấu hình embedding | Kết quả `rebuild/sync/status/delete/snapshot` | Đây là file chính của người 2 |
| `cli.py` | Chạy phần indexing độc lập | Lệnh CLI như `status`, `rebuild`, `sync` | JSON in ra terminal | Dùng để test/demo mà không cần sửa API |

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

## Settings note

| Setting | Default | Dùng để làm gì |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Địa chỉ service Ollama để gọi embedding |
| `EMBEDDING_MODEL` | `llama3.1:8b` | Model embedding mặc định của người 2 |
| `REQUEST_TIMEOUT_SECONDS` | `120` | Timeout khi gọi HTTP tới Ollama |
| `INDEX_DATA_INPUT_DIR` | `data_input` | Thư mục dữ liệu đầu vào mà người 2 đang đọc để build index |
| `INDEX_STORAGE_PATH` | `data/index_store.json` | File JSON lưu local index |
| `EMBEDDING_DIMENSIONS` | `128` | Số chiều của fallback hashed embedding |
| `INDEX_CHUNK_SIZE` | `900` | Độ dài chunk tối đa khi chia text |
| `INDEX_CHUNK_OVERLAP` | `120` | Số ký tự overlap giữa các chunk dài |

## Input và output của từng file

### `config.py`

- Input:
  - Biến môi trường của hệ thống
- Output:
  - Object `settings`
- Ý nghĩa:
  - Đây là nơi gom toàn bộ setting của người 2 để không phải chạm vào setting chung của project

### `schemas.py`

- Input:
  - Dữ liệu trạng thái hoặc kết quả thao tác index
- Output:
  - `IndexStatus`
  - `IndexOperationResult`
- Ý nghĩa:
  - Chuẩn hóa dữ liệu trả về cho CLI hoặc khi người khác cần đọc trạng thái index

### `embeddings/embedding_service.py`

- Input:
  - `embed_texts(texts)` nhận danh sách đoạn text
  - `embed_query(question, embedding_backend)` nhận 1 câu hỏi
- Output:
  - Vector embedding
  - Backend đang dùng: `ollama` hoặc `simple`
- Ý nghĩa:
  - Đây là lớp biến text thành vector
  - Nếu Ollama sẵn sàng thì dùng Ollama
  - Nếu chưa sẵn thì fallback sang hashed embedding để demo vẫn chạy được

### `vectorstore/local_index_store.py`

- Input:
  - File `.md`, `.txt` trong thư mục input
  - `index_data` để đọc/ghi trạng thái index
- Output:
  - `raw_chunks`
  - `texts`
  - `sources`
  - `IndexStatus`
  - `IndexOperationResult`
  - File `index_store.json`
- Ý nghĩa:
  - Đây là nơi quản lý dữ liệu index ở local
  - Chịu trách nhiệm quét file, chia chunk, ghi file JSON, build payload metadata

### `index_service.py`

- Input:
  - File nguồn từ `LocalIndexStore`
  - Vector từ `EmbeddingService`
- Output:
  - `get_status()` -> trạng thái hiện tại của index
  - `rebuild_index()` -> build lại toàn bộ index
  - `sync_index()` -> cập nhật index theo thay đổi mới
  - `delete_source()` -> xóa một nguồn dữ liệu trong index
  - `get_index_snapshot()` -> snapshot bàn giao cho người 3
- Ý nghĩa:
  - Đây là service điều phối chính
  - Nếu cần review nhanh phần của người 2 thì nên đọc file này trước

### `cli.py`

- Input:
  - Lệnh dòng lệnh
- Output:
  - JSON in ra terminal
- Ý nghĩa:
  - Dùng để demo nhanh hoặc test logic indexing mà không phải đụng API

## Giải thích theo từng hàm

### `config.py`

| Hàm / thành phần | Giải thích |
|---|---|
| `_get_int_env(name, default)` | Đọc biến môi trường và ép kiểu sang `int`. Nếu không đọc được thì dùng giá trị mặc định để tránh crash khi khởi động. |
| `IndexingSettings` | Gom toàn bộ setting riêng của người 2 vào một chỗ. |
| `settings` | Object config dùng chung cho toàn bộ package `app/indexing`. |

### `embeddings/embedding_service.py`

| Hàm | Giải thích |
|---|---|
| `embed_texts(texts)` | Hàm chính để tạo embedding cho danh sách chunk text. Tự chọn giữa Ollama thật hoặc fallback hashed embedding. |
| `embed_query(question, embedding_backend)` | Tạo embedding cho query/câu hỏi đơn lẻ, ưu tiên dùng cùng backend với lúc build index. |
| `_embed_texts_with_ollama(texts)` | Gọi API embedding của Ollama. Hỗ trợ cả endpoint mới và endpoint cũ. |
| `_embed_texts_with_hashing(texts)` | Tạo embedding giả lập bằng cách hash token vào vector cố định số chiều. |
| `_tokenize(text)` | Tách text thành token đơn giản để phục vụ hashed embedding. |
| `_normalize_vector(vector)` | Chuẩn hóa vector để độ dài vector ổn định, thuận lợi cho việc so sánh về sau. |

### `vectorstore/local_index_store.py`

| Hàm | Giải thích |
|---|---|
| `__init__()` | Khởi tạo cache bộ nhớ và xác định thư mục gốc của project để resolve path. |
| `load_index_data()` | Đọc snapshot index từ file JSON hoặc từ cache nếu đã có sẵn trong RAM. |
| `write_index_data(index_data)` | Ghi snapshot index xuống file JSON và đồng bộ lại cache trong bộ nhớ. |
| `scan_source_files()` | Quét thư mục input, lấy các file `.md` và `.txt` hợp lệ để đưa vào index. |
| `prepare_chunk_records(source_files)` | Đọc file, chia chunk, tạo metadata chunk và trả thêm danh sách text để đi embedding. |
| `build_sources_payload(source_files)` | Tạo metadata ở cấp source như tên file, đường dẫn và thời điểm cập nhật. |
| `build_status_response(index_data)` | Rút gọn snapshot thành thông tin trạng thái dễ đọc. |
| `build_operation_response(...)` | Tạo kết quả đầy đủ cho các thao tác như rebuild, sync, delete. |
| `empty_index_data()` | Tạo snapshot rỗng khi index chưa tồn tại. |
| `build_source_id(file_path)` | Sinh `source_id` ổn định từ path tương đối của file. |
| `read_source_text(file_path)` | Đọc text từ file, có fallback khi gặp lỗi encoding. |
| `split_text(text)` | Chia văn bản thành các chunk theo block/đoạn trước khi phải cắt cứng. |
| `split_long_block(text)` | Cắt một block dài thành nhiều chunk có overlap để giữ ngữ cảnh. |
| `get_data_input_dir()` | Trả về đường dẫn tuyệt đối tới thư mục dữ liệu đầu vào. |
| `get_storage_path()` | Trả về đường dẫn tuyệt đối tới file lưu snapshot index. |
| `utc_now()` | Tạo timestamp UTC ở dạng ISO string để lưu vào metadata. |
| `resolve_path(value)` | Chuẩn hóa path tương đối hoặc tuyệt đối để dùng nhất quán trong mọi môi trường chạy. |

### `index_service.py`

| Hàm | Giải thích |
|---|---|
| `__init__(...)` | Tiêm các dependency chính và tạo `asyncio.Lock()` để tránh thao tác index chạy chồng nhau. |
| `get_status()` | Lấy trạng thái hiện tại của index mà không build lại dữ liệu. |
| `rebuild_index()` | Build lại toàn bộ index từ đầu. |
| `sync_index()` | Chỉ cập nhật các source mới/thay đổi và xóa source cũ không còn tồn tại. |
| `delete_source(source_id)` | Xóa một source cụ thể khỏi index mà không phải rebuild hết. |
| `get_index_snapshot()` | Lấy snapshot hoàn chỉnh của index để bàn giao cho người 3. |
| `_build_index_data(source_files)` | Hàm nội bộ để biến danh sách file nguồn thành snapshot index hoàn chỉnh. |

### `cli.py`

| Hàm | Giải thích |
|---|---|
| `_run_command(args)` | Nhận lệnh từ CLI và gọi đúng hàm tương ứng trong `IndexingService`. |
| `build_parser()` | Khai báo các lệnh CLI như `status`, `rebuild`, `sync`, `snapshot`, `delete-source`. |
| `main()` | Điểm vào chính khi chạy bằng terminal; parse args, chạy command và in JSON kết quả. |

## Input chuẩn và output bàn giao

### Input mà người 2 đang kỳ vọng

- Dữ liệu text đã tương đối sạch
- Hiện tại đọc từ `data_input`
- Phù hợp nhất khi người 1 bàn giao text hoặc chunk-ready text

### Output mà người 2 bàn giao cho người 3

- File index local tại `data/index_store.json`
- Snapshot từ `get_index_snapshot()`
- Metadata gồm:
  - `source_id`
  - `source_name`
  - `chunk_id`
  - `text`
  - `vector`
  - `embedding_backend`
  - `embedding_model`

## Nên đọc file nào trước

Nếu teammate cần đọc nhanh phần của người 2:

1. `index_service.py`
2. `README.md`
3. `embeddings/embedding_service.py`
4. `vectorstore/local_index_store.py`
5. `cli.py`

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
