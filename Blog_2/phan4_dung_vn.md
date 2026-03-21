# 4. RAG — Đỉnh cao thực tiễn của Retrieval (Góc nhìn của AI Developer)

Nếu Phần 2 nói về **sự tiến hóa của tìm kiếm**, Phần 3 nói về **quy trình chuẩn bị dữ liệu**, thì Phần 4 là nơi mọi thứ hội tụ trong sản phẩm thực tế:

**RAG (Retrieval-Augmented Generation)**.

RAG không phải là một model hoàn toàn mới, mà là một kiến trúc kết hợp:
- **Retriever** (truy xuất tri thức liên quan)
- **Generator** (LLM tạo câu trả lời)

Thay vì buộc LLM phải “nhớ hết”, ta cho LLM khả năng “đọc tài liệu đúng lúc”.

---

## 4.1. Vì sao RAG quan trọng trong sản phẩm thật

Khi chỉ dùng LLM thuần, thường gặp 3 vấn đề:
1. **Hallucination**: trả lời trôi chảy nhưng sai.
2. **Giới hạn tri thức**: model không biết dữ liệu mới hoặc dữ liệu nội bộ.
3. **Thiếu truy vết nguồn**: khó biết câu trả lời dựa trên tài liệu nào.

RAG giải quyết trực tiếp:
- Neo câu trả lời vào tài liệu được truy xuất.
- Cập nhật tri thức bằng cách cập nhật kho dữ liệu, không cần train lại model.
- Có thể hiển thị trích dẫn để tăng độ tin cậy.

---

## 4.2. Luồng RAG cốt lõi (end-to-end)

```text
Câu hỏi người dùng
   ↓
Embedding query
   ↓
Truy xuất từ Vector DB (top-k chunks)
   ↓
(Tùy chọn) Rerank kết quả
   ↓
Tạo prompt cuối cùng với context
   ↓
LLM sinh câu trả lời + nguồn tham chiếu
```

Trong triển khai, RAG thường gồm 4 khối:
- `ingestion`: chunk + embedding + indexing tài liệu.
- `retrieval`: lấy các chunks liên quan theo query.
- `prompting`: ghép instruction + context + câu hỏi.
- `generation`: gọi LLM và định dạng output.

---

## 4.3. Blueprint triển khai tối thiểu

### Bước A — Lấy context
- Biến câu hỏi thành embedding vector.
- Tìm kiếm trên vector database (`top_k = 5` hoặc `10`).
- Lọc theo metadata (sản phẩm, ngôn ngữ, thời gian).

### Bước B — Ghép prompt an toàn
- Đặt rule hệ thống rõ ràng: “Chỉ trả lời dựa trên context cung cấp.”
- Đưa các chunk vào khối `CONTEXT`.
- Thêm hành vi fallback: “Nếu không đủ thông tin, hãy nói rõ.”

### Bước C — Sinh câu trả lời + trích dẫn
- Yêu cầu model trả về:
  - câu trả lời ngắn gọn
  - nguồn tham chiếu (`doc_id`, tiêu đề, link)

Cấu trúc này giúp giảm mạnh các câu trả lời “nghe hợp lý nhưng sai”.

---

## 4.4. Ví dụ thực tế

**Người dùng hỏi:**
> “Chính sách hoàn tiền 30 ngày cho sản phẩm số hoạt động thế nào?”

**Retriever trả về:**
- `policy_refund_v2.md` (điều kiện hoàn tiền)
- `faq_payments.md` (các ngoại lệ)
- `terms_service.md` (giới hạn theo khu vực)

**LLM nhận prompt chứa các chunk này** và trả lời:
- áp dụng hoàn tiền trong 30 ngày nếu thỏa điều kiện sử dụng,
- nêu các gói bị loại trừ,
- đính kèm link chính sách chính thức.

Nếu không dùng RAG, model có thể trả lời chung chung. Có RAG, câu trả lời bám sát tài liệu thật của hệ thống.

---

## 4.5. Những đánh đổi kỹ thuật sẽ gặp

1. **Latency vs chất lượng**
   - Lấy nhiều chunk hơn có thể tăng recall nhưng chậm hơn.
2. **Kích thước chunk vs toàn vẹn ngữ cảnh**
   - Chunk quá nhỏ mất ý; chunk quá lớn tốn token.
3. **Chi phí vs độ tin cậy**
   - Reranking và context lớn tăng chất lượng nhưng tăng cost.

Một cấu hình production phổ biến:
- Hybrid retrieval (BM25 + vector)
- Recall top 20 → rerank còn top 5
- Prompt có grounding + output có citation

---

## 4.6. Đánh giá hệ thống RAG như thế nào

Không nên chỉ đánh giá kiểu “câu trả lời nghe hay”. Hãy đo:
- **Retrieval Recall@k**: có lấy được chunk thật sự liên quan không?
- **Groundedness/Faithfulness**: câu trả lời có bám context không?
- **Độ chính xác trích dẫn**: nguồn có đúng và hữu ích không?
- **Latency (P95)** và **chi phí mỗi request**.

RAG tốt là bài toán hệ thống, không chỉ là bài toán model.

---

## Kết luận phần 4

RAG là cây cầu nối giữa tri thức doanh nghiệp và năng lực suy luận của LLM.

Từ góc nhìn AI Developer, thông điệp cốt lõi là:
> Câu trả lời tốt nhất không phải câu trả lời trôi chảy nhất, mà là câu trả lời **đúng, có căn cứ, và truy vết được**.

Đó là lý do RAG vẫn là ứng dụng Retrieval thực tiễn và hiệu quả nhất trong các sản phẩm AI hiện đại.

