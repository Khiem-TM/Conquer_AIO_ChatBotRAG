## Phần 2 - Embedding + Indexing Owner: Xây dựng chỉ mục để tìm đúng đoạn văn

Trong kiến trúc của hệ thống Chatbot RAG, phần việc của **Người 2 (Embedding + Indexing)** là chiếc cầu nối giữa dữ liệu đã ingest và tầng Retrieval. Nếu Người 1 lo “đưa tài liệu vào hệ thống và chuẩn hóa”, thì Người 2 chịu trách nhiệm biến những đoạn văn bản đó thành **vector có thể tìm kiếm được** và lưu chúng vào một **chỉ mục (index)** nhất quán, sẵn sàng cho việc truy xuất.

---

### 1. Embedding là gì và dùng để làm gì?

**Embedding** là quá trình biến mỗi đoạn văn (chunk) thành một vector số thực có kích thước cố định. Ý tưởng quan trọng:

- Các đoạn văn có nội dung **giống nhau về mặt nghĩa** sẽ có vector **gần nhau** trong không gian.
- Câu hỏi của người dùng cũng được embedding thành vector, để có thể so sánh với vector của từng chunk.

Bạn có thể hình dung embedding như việc “dịch một đoạn chữ sang tọa độ trong không gian nhiều chiều”. Khi người dùng đặt câu hỏi, hệ thống:

1. Chuyển câu hỏi thành một vector.
2. So sánh vector này với vector của tất cả chunk trong index.
3. Chọn ra những chunk có vector “gần” nhất (tức là có ý nghĩa tương đồng nhất).

Đây là nền tảng cho **semantic search** – tìm theo ý nghĩa thay vì chỉ dựa vào trùng từ khóa.

---

### 2. Vì sao phải có Indexing?

Nếu chỉ có embedding mà không có indexing, mỗi lần người dùng hỏi, hệ thống sẽ phải:

- đọc lại toàn bộ tài liệu,
- chia chunk lại,
- embedding lại hết,
- rồi mới so sánh vector.

Điều này **rất chậm** và không thực tế khi số tài liệu lớn.

**Indexing** giải quyết vấn đề đó bằng cách:

- lưu sẵn:
  - `chunk_id` → `text` (đoạn nội dung gốc),
  - `chunk_id` → `vector` (vector embedding),
  - `source_id`, `source_name`, metadata khác (tài liệu nguồn là file nào, đường dẫn, thời điểm cập nhật…).
- tổ chức tất cả thông tin này thành một **snapshot index** mà Retrieval có thể tải lên và sử dụng ngay.

Trong project, phần index có thể được lưu ở dạng **JSON local** hoặc dùng backend như **Qdrant**. Dù cách lưu trữ thay đổi, tư duy cốt lõi vẫn là:

> “Mọi chunk trong hệ thống đều có vector, metadata rõ ràng, và được lưu vào một cấu trúc nhất quán để retrieval tra cứu nhanh.”

---

### 3. Nguyên tắc quan trọng: Nhất quán giữa Embedding và Index

Một yêu cầu mà Người 2 phải luôn để ý là **tính nhất quán**:

- Vector của chunk và vector của câu hỏi phải được sinh ra bởi **cùng một kiểu embedding**:
  - cùng mô hình (ví dụ: `llama3.1:8b`),
  - cùng backend (ví dụ: `ollama` hay một backend đơn giản khác).
- Nếu bạn đổi mô hình embedding mà **không** build lại index, các vector cũ và mới sẽ **không còn cùng hệ trục**, khiến việc so sánh trở nên kém ý nghĩa.

Trong tài liệu phân chia công việc, đây chính là phần:

- “Chốt mô hình embedding, số chiều vector…”
- “Chỉ mục được tạo đúng sau ingest; xóa/cập nhật không gây lệch index; có phương án rebuild rõ ràng…”

Nói cách khác, Người 2 phải kiểm soát:

- Khi nào cần **rebuild** toàn bộ index.
- Khi nào đủ để **sync** một phần (incremental update).

---

### 4. Vòng đời của Index: Full Rebuild và Incremental Sync

Trong thực tế, index không phải chỉ được tạo một lần rồi bỏ đó. Nó có cả một **vòng đời (lifecycle)**:

#### 4.1. Full rebuild – Xây lại chỉ mục từ đầu

Đây là thao tác “làm lại tất cả”:

- Quét toàn bộ thư mục `data_input`.
- Đọc nội dung từng file, chia chunk.
- Gọi Embedding để tạo vector cho **mọi** chunk.
- Ghi snapshot index mới, ghi đè snapshot cũ.

Full rebuild thường dùng khi:

- Lần đầu khởi tạo hệ thống.
- Thay đổi mô hình embedding (`embedding_model` đổi).
- Thay đổi logic chunking (cách tách đoạn, kích thước chunk…).
- Cần “làm sạch” lại dữ liệu index vì thay đổi lớn ở tầng ingest.

#### 4.2. Incremental sync – Cập nhật dần, không làm lại tất cả

Đây là thao tác giúp tiết kiệm thời gian và tài nguyên:

1. Quét thư mục `data_input` để lấy danh sách file hiện tại.
2. So sánh với snapshot index cũ:
   - Nếu file mới xuất hiện → add vào index.
   - Nếu file bị xóa → xóa các chunk tương ứng khỏi index.
   - Nếu file sửa đổi (thời gian `updated_at` khác) → chỉ re-embed và cập nhật các chunk của file đó.
3. Giữ nguyên chunk của các file không có thay đổi.

Incremental sync cho phép Người 2 đáp ứng yêu cầu trong tài liệu:

- “Chiến lược incremental update.”
- “Rebuild không rõ ràng là rủi ro cần chặn.”

Hệ thống vẫn nhanh, mà dữ liệu index vẫn đúng.

#### 4.3. Delete source – Xóa một tài liệu khỏi chỉ mục

Ngoài hai thao tác ở trên, Người 2 còn cần hỗ trợ:

- Xóa một `source_id` cụ thể khỏi index (khi người dùng muốn gỡ bớt tài liệu).
- Tự động xóa mọi chunk thuộc source đó.

Điều này giúp tránh phải rebuild toàn bộ chỉ vì muốn bỏ một vài tài liệu đơn lẻ.

---

### 5. Backend Embedding trong project: Ollama + Fallback

Trong `Conquer_AIO_ChatBotRAG`, Embedding được thiết kế để:

- **Ưu tiên dùng Ollama**:
  - Nếu endpoint `Ollama` sẵn sàng, hệ thống sẽ gọi API để sinh embedding thật.
  - Vector thu được thường có chất lượng ngữ nghĩa cao, phù hợp semantic search.
- **Fallback sang hashed embedding** khi môi trường local chưa đủ:
  - Dùng kỹ thuật hashing đơn giản để tạo vector có số chiều cố định.
  - Mục tiêu là:
    - Giữ cho **pipeline của Người 2 vẫn chạy được** trên mọi máy.
    - Tránh phụ thuộc nặng vào môi trường AI bên ngoài.

Đối với người mới:

- Hãy xem fallback như “bản demo” giúp hệ thống chạy end-to-end.
- Khi triển khai thật, bạn nên cấu hình embedding model “xịn” hơn (ví dụ Ollama với `llama3.1`).

---

### 6. Payload index và điểm bàn giao cho Retrieval (Người 3)

Khi index đã được xây xong, Người 2 cần đảm bảo:

- Snapshot index có đủ:
  - Thông tin về **sources** (mỗi file là một source, kèm tên file, đường dẫn, timestamp).
  - Danh sách **chunks**:
    - `source_id`, `source_name`,
    - `chunk_id`,
    - `text`,
    - `vector`.
  - Thông tin về `embedding_backend`, `embedding_model`, thời điểm `built_at`.

Đây chính là “hợp đồng bàn giao” từ lane 2 sang lane 3:

- Retrieval không cần biết chi tiết embedding làm sao.
- Retrieval chỉ cần:
  - một tập chunk có text + vector,
  - metadata đủ để lọc, debug, và reporting.

---

### 7. Tóm tắt dành cho người mới bắt đầu

Bạn có thể nhớ phần của Người 2 bằng 3 ý sau:

1. **Embedding**: Biến văn bản thành vector sao cho tương đồng về nghĩa → gần nhau trong không gian.
2. **Indexing**: Lưu trữ vector + metadata thành một snapshot có tổ chức, để retrieval tra cứu nhanh.
3. **Nhất quán & vòng đời**:
   - Khi đổi mô hình embedding hoặc logic chunking, cần rebuild.
   - Khi chỉ thêm/sửa/xóa một số tài liệu, dùng incremental sync.

Khi hiểu được lane 2, bạn sẽ thấy rõ hơn cách mà chatbot RAG “nhớ” nội dung tài liệu và tìm lại chúng trong vài trăm mili–giây khi người dùng đặt câu hỏi.

