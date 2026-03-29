## Phần 4 - RAG Core Owner: Ghép ngữ cảnh, thiết kế prompt và trả lời có citation

Nếu coi pipeline RAG là một dây chuyền, thì:

- Người 1 lo ingest và chuẩn hóa dữ liệu,
- Người 2 lo embedding + indexing,
- Người 3 lo retrieval (tìm đúng đoạn),
- **Người 4 (RAG Core)** là người “biên tập cuối”: ghép ngữ cảnh, viết prompt cho mô hình ngôn ngữ lớn (LLM), gọi model và trả về câu trả lời có **citation** rõ ràng.

---

### 1. Vai trò của RAG Core trong kiến trúc tổng thể

Về mặt luồng nghiệp vụ, RAG Core đứng sau Retrieval:

1. Người dùng đặt câu hỏi qua frontend.
2. Backend gọi Retrieval để lấy danh sách các chunk có liên quan nhất.
3. RAG Core:
   - ghép các chunk này thành **ngữ cảnh (context)**,
   - xây dựng một **prompt có cấu trúc**,
   - gọi LLM để sinh câu trả lời,
   - tạo danh sách **citation** để frontend hiển thị.

Điểm quan trọng: RAG Core **không cố gắng thay thế Retrieval**, mà tận dụng kết quả Retrieval để tạo ra **câu trả lời có căn cứ (grounded answer)**, bám sát nội dung tài liệu.

---

### 2. Ghép ngữ cảnh (Context Assembly)

Retrieval trả về một danh sách các chunk, mỗi chunk thường có:

- `source_id`, `source_name` – tài liệu nguồn,
- `chunk_id` – định danh của đoạn,
- `text` – nội dung đoạn,
- `score` – mức độ liên quan.

RAG Core cần:

1. Chọn ra một số chunk “đủ dùng” (top-k) để không vượt quá giới hạn context window của LLM.
2. Sắp xếp các chunk này thành một **block ngữ cảnh** rõ ràng, thường có:
   - nhãn [1], [2], …,
   - thông tin nguồn, chunk id, score,
   - nội dung text của từng chunk.

Mục tiêu của bước này:

- LLM có một vùng ngữ cảnh **đủ nhiều thông tin**, nhưng không bị “ngộp” vì quá dài.
- Người 4 kiểm soát được “thông tin nào được đưa vào prompt”.

---

### 3. Thiết kế Prompt: Cách nói chuyện với LLM để tránh hallucination

Prompt là “bản hướng dẫn” cho LLM. Một prompt tốt thường có cấu trúc:

1. **Vai trò của model** – ví dụ:
   - “Bạn là trợ lý AI cho hệ thống RAG…”
   - “Hãy trả lời bám sát ngữ cảnh…”
2. **Câu hỏi (Question)** – chính là input của người dùng.
3. **Ngữ cảnh (Context)** – các chunk được retrieval chọn.
4. **Yêu cầu trả lời (Instructions)** – ví dụ:
   - Trả lời bằng tiếng Việt.
   - Ưu tiên dùng thông tin trong ngữ cảnh.
   - Nếu ngữ cảnh không đủ, phải nêu rõ mức độ không chắc chắn.
   - Không bịa thêm thông tin ngoài ngữ cảnh.

Những ràng buộc này là vũ khí chính để **giảm hallucination**:

- LLM được “khuyên” không nên bịa,
- được “ép” phải dựa trên nguồn đã cho,
- được “cho phép” nói “không chắc” nếu thiếu dữ liệu.

Về mặt lane trong tài liệu PDF, đây chính là:

- “Thiết kế prompt chính thức và cơ chế context assembly.”
- “Giảm hallucination bằng ràng buộc ngữ cảnh…”

---

### 4. Gọi mô hình (LLM Generation) và cơ chế Timeout/Fallback

Sau khi có prompt, RAG Core sẽ:

1. Gửi prompt đến LLM (ví dụ model chạy qua Ollama).
2. Đợi kết quả trả lời trong một khoảng thời gian giới hạn (timeout).

Nếu LLM trả lời kịp:

- Hệ thống lấy text trả lời làm `answer`.

Nếu LLM chậm hoặc lỗi (timeout):

- RAG Core trả về một **fallback an toàn**, ví dụ:
  - Thông báo model đang xử lý quá lâu.
  - Gợi ý người dùng thử với câu hỏi ngắn hơn hoặc giảm `top_k`.

Đây là phần rất quan trọng từ góc nhìn “Owner lane 4”:

- Không để hệ thống treo vĩnh viễn khi model phản hồi chậm.
- Luôn có một câu trả lời tử tế gửi lại frontend, giúp trải nghiệm người dùng mượt hơn.

---

### 5. Xây dựng Citation: Giúp người dùng “kiểm chứng” câu trả lời

Một câu trả lời RAG tốt **không chỉ nói đúng** mà còn:

- chỉ ra **nó lấy căn cứ từ đâu**.

Đó là lý do lane 4 phải tạo ra danh sách **citation**. Mỗi citation thường chứa:

- `source_id`, `source_name` – nhận diện tài liệu gốc,
- `chunk_id` – đoạn cụ thể trong tài liệu,
- `score` – độ liên quan,
- `snippet` – một phần nội dung được rút gọn (ngắn, dễ đọc).

Lý do nên dùng **snippet thay vì full text**:

- UI sẽ gọn gàng hơn,
- người dùng có “preview” đủ để kiểm tra,
- nếu cần, họ vẫn có thể mở tài liệu gốc (mọi trường hợp đều biết rõ nguồn).

Trong project, citation chính là contract bàn giao từ RAG Core sang frontend:

- Backend trả về danh sách citation,
- Frontend render các thẻ citation để người dùng rê chuột và xem snippet.

---

### 6. Hợp đồng API với Frontend: Cách lane 4 nói chuyện với UI

Từ góc độ frontend, endpoint chat (ví dụ `/api/v1/chat`) trả về một response chứa:

- `answer`: câu trả lời cuối cùng,
- `citations`: danh sách citation (nếu người dùng bật chế độ này),
- `model`: tên model LLM đang dùng,
- `latency_ms`: thời gian xử lý,
- `conversation_id`: mã cuộc hội thoại (giúp front lưu lịch sử).

Nhờ contract rõ ràng này:

- Frontend chỉ cần render đúng các field là có một UI chat hoàn chỉnh.
- Lane 4 có thể thay đổi “cách build prompt” hoặc “logic context” bên trong mà không làm vỡ giao diện.

---

### 7. Giảm hallucination: RAG Core làm gì ngoài prompt?

Prompt tốt là điều kiện cần, nhưng lane 4 còn có thể:

- Giới hạn số lượng chunk đưa vào LLM (tránh context lan man).
- Ưu tiên các chunk có score cao và nguồn đáng tin cậy.
- Thiết kế fallback khi:
  - Retrieval không trả về kết quả đủ tốt,
  - LLM không phản hồi hoặc phản hồi lỗi.

Về lâu dài, Người 4 có thể phối hợp với Người 3 và Người 5 để:

- Đặt ra chuẩn “grounded answer”,
- Xây dựng bộ câu hỏi demo để kiểm tra chất lượng,
- Gắn thêm log/benchmark để hiểu khi nào model hallucinate.

---

### 8. Tóm tắt phần việc của Người 4 cho người mới bắt đầu

Bạn có thể nhớ lane RAG Core bằng 4 từ khóa:

1. **Context** – nhận các chunk đã được retrieval sắp hạng và ghép thành block ngữ cảnh.
2. **Prompt** – viết một prompt rõ ràng, ràng buộc model phải bám sát ngữ cảnh.
3. **LLM** – gọi mô hình sinh câu trả lời, kèm cơ chế timeout và fallback an toàn.
4. **Citation** – trả về danh sách nguồn (snippet + metadata) để người dùng kiểm chứng.

Khi hiểu rõ vai trò của Người 4, bạn sẽ thấy pipeline RAG không chỉ là “gọi LLM với tài liệu”, mà là một luồng có trách nhiệm rõ ràng: **từ ngữ cảnh → prompt → câu trả lời có căn cứ**.

