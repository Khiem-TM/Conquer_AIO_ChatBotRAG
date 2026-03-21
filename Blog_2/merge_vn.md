# Retrieval: Chiếc Chìa Khóa Vạn Năng Trong Kỷ Nguyên AI (Bản Merge Full VN)

> File này là bản merge toàn bộ nội dung các phần 2, 3, 4, 5.

---

## 2. Từ Keyword đến “Hiểu Ý Nghĩa”: AI đã thay đổi cách tìm kiếm như thế nào?  
*(Góc nhìn của kỹ sư NLP)*

Hãy thử tưởng tượng bạn lên Google và gõ “cách giảm cân hiệu quả”. Đây là một ví dụ rất quen thuộc, nhưng nó giúp chúng ta hiểu rõ cách hệ thống tìm kiếm đã thay đổi theo thời gian.

### Cách tìm kiếm “kiểu cũ” (Keyword Search)

Trước đây, hệ thống sẽ hoạt động theo một nguyên tắc khá đơn giản: nó đi tìm những bài viết có chứa đúng các từ mà bạn nhập vào, ví dụ như “giảm cân” hoặc “hiệu quả”.

- Những bài có nhiều lần xuất hiện của các từ khóa này thường sẽ được ưu tiên hiển thị cao hơn.
- Những bài không chứa các từ khóa đó, dù nội dung có thể liên quan, vẫn dễ bị xếp hạng thấp hoặc bị bỏ qua hoàn toàn.

Nói cách khác, hệ thống chủ yếu nhìn vào “mặt chữ” chứ chưa thực sự hiểu nội dung bên trong.

### Vấn đề của cách tiếp cận này

Giả sử có một bài viết với tiêu đề “Làm sao để giữ vóc dáng và đốt mỡ an toàn?”. Nội dung của bài này thực chất rất liên quan đến việc giảm cân và cải thiện sức khỏe.

Tuy nhiên, vì không xuất hiện đúng cụm từ “giảm cân”, hệ thống tìm kiếm kiểu cũ có thể không đánh giá cao bài viết này. Điều này dẫn đến việc người dùng có thể bỏ lỡ những thông tin hữu ích chỉ vì khác cách diễn đạt.

### Cách mới: tìm kiếm theo ý nghĩa (Semantic Search)

Các hệ thống hiện đại đã chuyển sang một cách tiếp cận khác: thay vì chỉ so khớp từng từ, chúng cố gắng hiểu ý định thực sự của người dùng khi đặt câu hỏi.

- Khi bạn tìm “giảm cân”, hệ thống có thể hiểu rộng hơn là bạn đang quan tâm đến việc đốt mỡ, ăn uống lành mạnh hoặc tập luyện.
- Nhờ đó, nó có thể trả về những kết quả không trùng từ nhưng vẫn đúng nội dung bạn cần.

Điểm khác biệt lớn nhất ở đây là hệ thống không chỉ “đọc chữ” mà bắt đầu “hiểu ý”.

### Hình dung một cách đơn giản

Một cách dễ hiểu là bạn có thể tưởng tượng mỗi câu hoặc mỗi đoạn văn đều được biểu diễn dựa trên ý nghĩa của nó.

- Những nội dung có ý nghĩa giống nhau sẽ được đặt gần nhau.
- Những nội dung khác chủ đề sẽ nằm xa nhau.

Ví dụ, các cụm như “giảm cân”, “đốt mỡ” hay “eat clean” đều liên quan đến cùng một chủ đề nên được xem là gần nhau, dù cách viết hoàn toàn khác nhau.

### So sánh nhanh hai cách tìm kiếm

| Cách tìm | Đặc điểm chính | Khi nào hiệu quả |
|---------|--------------|-----------------|
| Keyword (cũ) | Dựa trên việc so khớp từ khóa chính xác | Khi cần tìm thông tin cụ thể như tên sản phẩm, đoạn code |
| Semantic (mới) | Dựa trên việc hiểu ý nghĩa của câu | Khi tìm kiếm kiến thức, đặt câu hỏi hoặc khám phá thông tin |

Mỗi cách đều có ưu điểm riêng và cũng có những hạn chế nhất định.

### Thực tế hiện nay

Trong các hệ thống hiện đại, người ta thường không chỉ sử dụng một cách duy nhất mà kết hợp cả hai phương pháp.

- Việc kiểm tra từ khóa giúp đảm bảo độ chính xác ở mức bề mặt.
- Việc hiểu ý nghĩa giúp mở rộng phạm vi tìm kiếm và tăng độ liên quan của kết quả.

Sự kết hợp này giúp hệ thống vừa chính xác vừa linh hoạt hơn trong nhiều tình huống khác nhau.

### Kết luận phần này

Sự chuyển đổi từ tìm kiếm dựa trên từ khóa sang tìm kiếm dựa trên ý nghĩa là một bước tiến rất quan trọng. Nó giúp máy tính không chỉ xử lý văn bản mà còn tiến gần hơn đến việc hiểu được nội dung mà con người thực sự muốn tìm kiếm.

Đây cũng chính là nền tảng cho các hệ thống AI hiện đại như chatbot hay trợ lý ảo, nơi việc hiểu đúng câu hỏi quan trọng không kém việc đưa ra câu trả lời.

---

# 3. Quy Trình "Sơ Chế" Dữ Liệu (Góc nhìn của Data Architect)

Nếu Retrieval là “cỗ máy tìm kiếm”, thì dữ liệu chính là “nguyên liệu đầu vào”. Và giống như trong nấu ăn, nguyên liệu không được sơ chế kỹ thì dù bếp có xịn đến đâu, món ăn vẫn khó ngon.

Một hệ thống Retrieval hiệu quả không bắt đầu từ model, mà bắt đầu từ cách bạn **chuẩn bị dữ liệu**. Quy trình này thường xoay quanh 3 bước cốt lõi: **Chunking → Embedding → Indexing**.

## 3.1. Chunking – Chia nhỏ để giữ trọn ý nghĩa

Các mô hình AI không “đọc” văn bản như con người. Nếu bạn đưa cho hệ thống một tài liệu dài hàng chục trang, rất dễ xảy ra hai vấn đề:

* **Quá tải ngữ cảnh** (context overflow)
* **Làm loãng thông tin quan trọng**

Vì vậy, bước đầu tiên là **chia nhỏ tài liệu thành các đoạn (chunks)**.

**Các phương pháp chunking phổ biến:**

1. **Fixed-size chunking**  

<p align="center"><img src="phan3_HoangAnh/img3.1.png" width="700"></p>

Chia văn bản theo kích thước cố định (ký tự/từ/token), thường thêm `overlap` để giảm đứt mạch nội dung.  
Ưu điểm: Dễ triển khai, xử lý hàng loạt tốt.  
Nhược điểm: Dễ cắt ngang câu hoặc ý quan trọng.

2. **Semantic chunking**  

<p align="center"><img src="phan3_HoangAnh/img3.2.png" width="700"></p>

Chia theo đơn vị ngữ nghĩa (câu/đoạn), dùng embedding + similarity để gộp các phần liên quan.
Ưu điểm: Chunk mạch lạc hơn, retrieval chính xác hơn.
Nhược điểm: Phụ thuộc ngưỡng similarity và tốn compute hơn.

3. **Recursive chunking**

<p align="center"><img src="phan3_HoangAnh/img3.3.png" width="700"></p>

Tách theo ranh giới tự nhiên (`\n\n`, `\n`, khoảng trắng), nếu còn quá dài thì tách đệ quy tiếp.  
Ưu điểm: Cân bằng giữa ngữ nghĩa và giới hạn kích thước.  
Nhược điểm: Triển khai phức tạp hơn fixed-size.

4. **Document structure-based chunking**  


<p align="center"><img src="phan3_HoangAnh/img3.4.png" width="700"></p>

Tận dụng cấu trúc tài liệu (heading, section, list, table, paragraph) để xác định ranh giới chunk.
Ưu điểm: Giữ tốt logic tài liệu gốc.
Nhược điểm: Phụ thuộc tài liệu có cấu trúc rõ; chunk có thể không đồng đều.

5. **LLM-based chunking**

<p align="center"><img src="phan3_HoangAnh/img3.5.png" width="700"></p>

Dùng LLM xác định ranh giới chunk theo chủ đề/ý nghĩa hoàn chỉnh.  
Ưu điểm: Tiềm năng tốt nhất về chất lượng ngữ nghĩa.  
Nhược điểm: Chi phí cao, chậm hơn, phụ thuộc prompt và context window.

**Insight quan trọng:** Không có phương pháp “tốt nhất tuyệt đối”. Thực tế thường dùng **hybrid chunking** để cân bằng chất lượng, tốc độ và chi phí.

## 3.2. Embedding – Biến ngôn ngữ thành tọa độ

Sau khi có các chunks, bước tiếp theo là chuyển chúng thành dạng mà máy có thể “hiểu” và so sánh: **vector embeddings**.

Embedding model (ví dụ như `text-embedding-3`) sẽ biến mỗi đoạn văn thành một vector trong không gian nhiều chiều.

Điều này cho phép hệ thống:

* Đo lường **độ tương đồng ngữ nghĩa**
* Tìm các đoạn “có nghĩa giống nhau” dù không trùng từ

**Ví dụ thực tế (Embedding):**

Giả sử hệ thống có 3 chunks:

* `C1`: “Cách nấu phở bò tại nhà”
* `C2`: “Hướng dẫn nấu phở truyền thống”
* `C3`: “Mẹo bảo dưỡng xe máy mùa mưa”

Với query: “Làm sao nấu phở bò ngon?”

* `sim(query, C1) = 0.91`
* `sim(query, C2) = 0.88`
* `sim(query, C3) = 0.15`

Kết quả: hệ thống ưu tiên `C1`, `C2` vì gần nghĩa, dù câu chữ không trùng hoàn toàn.


<p align="center"><img src="phan3_HoangAnh/img3.6.png" width="700"></p>

**Insight quan trọng:**
Embedding chính là cầu nối giữa **ngôn ngữ con người** và **toán học của máy học**.


## 3.3. Indexing – Tổ chức để tìm kiếm trong mili-giây

Sau khi có vector, bạn cần một nơi để lưu trữ và truy xuất chúng thật nhanh — đó là lúc **Vector Database** xuất hiện.

Một số hệ phổ biến:

* Pinecone
* Milvus
* Weaviate

Khác với database truyền thống (SQL), vector database được tối ưu cho:

* **Tìm kiếm gần đúng (Approximate Nearest Neighbor - ANN)**
* Xử lý hàng triệu đến hàng tỷ vector với độ trễ thấp

**Quy trình indexing gồm:**

* Lưu vector + metadata (nguồn, tiêu đề, timestamp…)
* Tạo cấu trúc chỉ mục (index structure) để tăng tốc tìm kiếm
* Tối ưu cho truy vấn similarity (cosine similarity, dot product…)

**Ví dụ thực tế (Indexing + Retrieval):**

Giả sử bạn đã index 1 triệu chunks tài liệu nội bộ. Khi có câu hỏi “Chính sách hoàn tiền trong 30 ngày hoạt động thế nào?”:

1. Câu hỏi được embedding thành `q_vector`
2. Vector DB dùng ANN index để tìm `top-k` vector gần nhất trong mili-giây
3. Trả về các chunk liên quan nhất, ví dụ:
   * `chunk_2451` (score `0.93`) - mục hoàn tiền sản phẩm
   * `chunk_8712` (score `0.89`) - điều kiện áp dụng
   * `chunk_1022` (score `0.84`) - các trường hợp ngoại lệ

Các chunk này sẽ được đưa vào context cho LLM để tạo câu trả lời cuối cùng.

<p align="center"><img src="phan3_HoangAnh/img3.7.png" width="700"></p>

Khi người dùng đặt câu hỏi:

1. Câu hỏi được embedding thành vector
2. Hệ thống tìm các vector gần nhất trong database
3. Trả về các chunks liên quan nhất


## Retrieval tốt bắt đầu từ dữ liệu tốt

Ba bước này tạo thành nền tảng cho toàn bộ hệ thống Retrieval:

* **Chunking** → Quyết định *AI sẽ “nhìn” dữ liệu như thế nào*
* **Embedding** → Quyết định *AI “hiểu” dữ liệu ra sao*
* **Indexing** → Quyết định *AI tìm dữ liệu nhanh đến mức nào*

Nếu làm tốt phần này, bạn đã giải quyết được hơn 70% chất lượng của hệ thống RAG sau này.

Một câu nói đáng nhớ trong giới Data Architect:

> “Garbage in, garbage out — nhưng với Retrieval, nó là: *Chunk tệ, search sai; embedding kém, hiểu sai.*”


Tài liệu tham khảo: https://viblo.asia/p/toi-uu-hoa-rag-kham-pha-5-chien-luoc-chunking-hieu-qua-ban-can-biet-EvbLbPGW4nk


---

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



---

# Retrieval: Chiếc Chìa Khóa Vạn Năng Trong Kỷ Nguyên AI

---

## Phần 5: Thách Thức & Tương Lai Của Retrieval

> _Góc nhìn của Quản Lý Sản Phẩm_

---

### Dẫn Nhập

Bốn phần trước đã vẽ nên một bức tranh hoàn chỉnh về Retrieval — từ khái niệm nền tảng, sự tiến hóa của kỹ thuật tìm kiếm, quy trình xử lý dữ liệu, đến ứng dụng đỉnh cao là RAG. Nhưng không có công nghệ nào là hoàn hảo.

Là một người quản lý sản phẩm, câu hỏi tôi luôn đặt ra không phải là _"Công nghệ này hoạt động như thế nào?"_ mà là _"Công nghệ này thất bại ở đâu, và bước tiếp theo là gì?"_

---

### Những Thách Thức Hiện Tại

#### 1. Độ Trễ (Latency) — Kẻ Thù Thầm Lặng Của Trải Nghiệm Người Dùng

Một hệ thống Retrieval phải thực hiện hàng loạt tác vụ trong tích tắc:

```
[Câu hỏi của người dùng]
        ↓
  Embedding query
        ↓
  Vector similarity search
        ↓
  Fetch & rerank documents
        ↓
  Gửi context → LLM generate
        ↓
  [Câu trả lời]
```

Mỗi bước đều tốn thời gian. Nếu tổng thời gian phản hồi vượt quá 2–3 giây, người dùng bắt đầu mất kiên nhẫn. Đây là một thách thức kỹ thuật lớn, đặc biệt khi cơ sở dữ liệu có hàng triệu vector.

Hướng giải quyết đang được nghiên cứu:

- Approximate Nearest Neighbor (ANN) để tìm kiếm nhanh hơn, chấp nhận sai số nhỏ.
- Caching kết quả cho các truy vấn phổ biến.
- Streaming response để người dùng thấy câu trả lời được tạo ra theo thời gian thực.

---

#### 2. Độ Nhiễu (Noise) — "Rác Vào, Rác Ra"

Retrieval chỉ mạnh khi nó lấy đúng dữ liệu. Trên thực tế, hệ thống có thể:

- Trả về những đoạn văn bản _có vẻ liên quan_ nhưng không thực sự trả lời câu hỏi.
- Lấy phải thông tin lỗi thời hoặc mâu thuẫn nhau từ nhiều nguồn.
- Bị "đánh lừa" bởi các từ ngữ trùng hợp về mặt ngữ nghĩa nhưng khác về ngữ cảnh.

> Ví dụ thực tế: Người dùng hỏi _"Chính sách hoàn tiền trong vòng 30 ngày"_, hệ thống lại lấy về đoạn văn bản về _"Chính sách bảo hành 30 tháng"_ — hai chủ đề hoàn toàn khác nhau.

Khi LLM nhận phải context sai, nó không "biết" mình đang được cung cấp thông tin nhiễu — và sẽ trả lời sai một cách tự tin.

---

#### 3. Vấn Đề Về Chunking & Context Window

Như đã đề cập ở Phần 3, việc chia nhỏ văn bản (chunking) là cần thiết — nhưng cũng là con dao hai lưỡi. Chunk quá nhỏ thì mất ngữ cảnh; chunk quá lớn thì loãng ý nghĩa và tốn token không cần thiết.

Hiện chưa có một công thức "vàng" nào áp dụng được cho mọi loại dữ liệu.

---

### Tương Lai Thuộc Về Ai?

#### Hybrid Search — Lấy Điểm Mạnh Của Cả Hai Thế Giới

Cộng đồng AI đang hướng tới Hybrid Search — sự kết hợp giữa:

| Phương pháp              | Điểm mạnh                                            | Điểm yếu                         |
| ------------------------ | ---------------------------------------------------- | -------------------------------- |
| Lexical Search (BM25)    | Chính xác với từ khóa cụ thể, mã sản phẩm, tên riêng | Không hiểu ngữ nghĩa             |
| Semantic Search (Vector) | Hiểu ý định, ngữ cảnh                                | Có thể bỏ sót từ khóa quan trọng |
| Hybrid Search            | Tận dụng cả hai                                      | Phức tạp hơn để triển khai       |

Hybrid Search không phải "chọn một trong hai" — mà là chạy cả hai song song, sau đó dùng thuật toán như Reciprocal Rank Fusion (RRF) để hợp nhất kết quả.

---

#### Reranking — Bộ Lọc Tinh Tế Ở Tầng Cuối

Ngay cả khi Retrieval trả về 20 đoạn văn bản, không phải tất cả đều có giá trị như nhau. Reranking là bước bổ sung, dùng một model chuyên biệt (như Cohere Rerank, Cross-encoder) để:

1. Đọc lại từng cặp (câu hỏi — đoạn văn bản).
2. Chấm điểm mức độ liên quan thực sự.
3. Sắp xếp lại thứ tự trước khi đưa vào LLM.

Reranking tốn thêm thời gian, nhưng cải thiện chất lượng câu trả lời đáng kể — đây là sự đánh đổi mà nhiều sản phẩm AI production sẵn sàng chấp nhận.

---

#### Agentic Retrieval — Khi AI Tự Quyết Định Cách Tìm Kiếm

Xu hướng mới nhất là trao cho AI khả năng tự lập kế hoạch truy xuất thông tin. Thay vì một lần tìm kiếm duy nhất, AI Agent có thể:

- Phân tích câu hỏi phức tạp và chia nhỏ thành nhiều sub-query.
- Thực hiện nhiều vòng Retrieval, mỗi vòng tinh chỉnh dựa trên kết quả trước.
- Tự đánh giá: _"Thông tin tôi có đủ để trả lời chưa?"_

Đây là hướng đi của các hệ thống như Deep Research hay Agentic RAG — và nhiều khả năng sẽ là tiêu chuẩn mới trong 1–2 năm tới.

---

### Nhìn Từ Góc Độ Sản Phẩm

Là người xây dựng sản phẩm, tôi nhận ra rằng Retrieval không chỉ là bài toán kỹ thuật — đó còn là bài toán thiết kế trải nghiệm:

- Khi nào nên hiển thị nguồn trích dẫn để người dùng tin tưởng?
- Làm thế nào để gracefully handle trường hợp không tìm thấy thông tin liên quan?
- Metrics nào để đo "độ tốt" của Retrieval trong sản phẩm thực?

> Một insight quan trọng: Người dùng không quan tâm đến vector hay embedding. Họ chỉ quan tâm đến một điều duy nhất — câu trả lời có đúng không, và có nhanh không.

---

### Kết Luận Phần 5

Retrieval đang ở giai đoạn trưởng thành nhanh chóng. Những thách thức về latency, noise, và chunking đang dần được giải quyết qua Hybrid Search, Reranking, và Agentic Retrieval.

Nhưng bài học lớn nhất từ góc nhìn quản lý sản phẩm là: công nghệ tốt nhất không phải là công nghệ phức tạp nhất — mà là công nghệ giải quyết đúng vấn đề của người dùng, một cách đáng tin cậy và nhất quán.

Retrieval là nền tảng — và nền tảng đó đang ngày càng vững chắc hơn.

---
