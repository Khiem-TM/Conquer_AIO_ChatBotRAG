## Phần 5 - Eval/DevOps + Frontend nhẹ Owner: Bảo đảm hệ thống chạy được end-to-end

Trong một dự án chatbot RAG thực tế, “chạy được từ đầu đến cuối” quan trọng không kém “thuật toán hay” hay “mô hình mạnh”. **Người 5 (Eval/DevOps + Frontend nhẹ)** chính là người:

- đảm bảo hệ thống có thể **chạy local** hoặc bằng **Docker**,
- có **kiểm thử tối thiểu** để tránh demo lỗi,
- và có một **giao diện web đủ dùng** để người mới có thể thử nghiệm nhanh.

---

### 1. Bức tranh tổng thể: Backend + Frontend trong repo GitHub

Trong repository `Conquer_AIO_ChatBotRAG`:

- **Backend** (API + pipeline RAG) nằm trong thư mục `Project/`, sử dụng **FastAPI** để:
  - expose endpoint chat,
  - quản lý ingest/ingest status,
  - hỗ trợ upload file.
- **Frontend** nằm trong thư mục `frontend/`, được xây dựng bằng:
  - **React 18**,
  - **TypeScript**,
  - **Vite**,
  - **Tailwind CSS** cho UI hiện đại.

Nhiệm vụ của Người 5 là “nối” hai phần này lại:

- backend nói chuyện được với LLM (Ollama),
- frontend nói chuyện được với backend,
- tất cả được bọc trong một trải nghiệm “bấm chạy là dùng được”.

---

### 2. DevOps: Dùng Docker Compose để khởi chạy hệ thống

Trong thư mục `Project/docker` có file `docker-compose.yml`, hỗ trợ chạy:

1. **Dịch vụ Ollama** – cung cấp LLM:
   - chạy container `ollama/ollama`,
   - publish cổng `11434`,
   - có healthcheck (`/api/tags`) để kiểm tra đã sẵn sàng chưa.
2. **Dịch vụ init model Ollama** – tải model về trước:
   - container phụ `ollama-init`,
   - chờ Ollama `healthy` rồi gọi lệnh pull model (ví dụ `llama3.1:8b`).
3. **Dịch vụ API** – backend FastAPI:
   - build từ Dockerfile,
   - set biến môi trường (ví dụ `OLLAMA_BASE_URL=http://ollama:11434`),
   - mount các thư mục `app`, `data_input`, `data`,
   - có healthcheck gọi `/health` để biết API đã chạy.

Với người mới, điểm quan trọng là:

- Không cần nhớ từng lệnh chạy lắt nhắt,
- chỉ cần `docker compose up` là có:
  - LLM,
  - backend,
  - healthcheck đảm bảo các dịch vụ lên đúng thứ tự.

---

### 3. Health Check: Làm sao biết backend đang “sống”?

Backend cung cấp một endpoint `/health`:

- trả về trạng thái như:
  - `status` – `"ok"` nếu hệ thống đang chạy,
  - `service` – tên service (ví dụ `rag-chatbot-api`),
  - `model` – tên model LLM đang dùng,
  - `timestamp` – thời gian hiện tại.

Endpoint này phục vụ nhiều mục đích:

- **Docker healthcheck** – nếu `/health` không trả về đúng, container bị coi là “fail”.
- **Tự kiểm tra khi dev** – bạn có thể vào trình duyệt gõ `http://localhost:8000/health` để xem API đã sẵn sàng chưa.
- **Script kiểm thử** – có thể dùng trong các script như `test_system.py`, `quickstart.py` để tự động kiểm tra.

Việc có health check rõ ràng giúp:

- phát hiện sớm lỗi cấu hình (ví dụ kết nối Ollama),
- giảm thời gian “đoán xem API đã chạy chưa”.

---

### 4. Eval: Smoke test và system check cho RAG Chatbot

Người 5 không nhất thiết phải viết test unit phức tạp, nhưng cần có **smoke test** và **system check**:

1. **Kiểm tra môi trường Python**:
   - phiên bản Python (ví dụ 3.11+),
   - đã cài đủ các thư viện chính (FastAPI, Uvicorn, httpx, langchain, qdrant_client, pypdf…).
2. **Kiểm tra Ollama**:
   - thử gọi `http://localhost:11434/api/tags`,
   - liệt kê các model khả dụng,
   - nếu không kết nối được, gợi ý chạy `ollama serve` hoặc dùng Docker.
3. **Kiểm tra dữ liệu**:
   - thư mục `data_input` có tồn tại không,
   - có ít nhất một vài file mẫu để ingest hay chưa.
4. **Kiểm tra cấu hình (.env)**:
   - đọc ra các biến quan trọng (`OLLAMA_BASE_URL`, `CORS_ORIGINS`, …),
   - thông báo nếu thiếu nhưng vẫn có default để chạy MVP.

Các script như `quickstart.py`, `test_system.py` chính là hiện thân của tư duy:

> “Đừng chờ đến lúc demo mới phát hiện ra backend chưa kết nối được với LLM.”

---

### 5. Frontend: Giao diện chat và quản lý tài liệu cho người mới

Frontend của project được thiết kế để:

1. **Giao diện Chat**:
   - hiển thị câu hỏi và câu trả lời theo dạng hội thoại,
   - có hiệu ứng “đang gõ/streaming” khi chờ model trả lời,
   - lưu lịch sử chat (history) để người dùng xem lại.
2. **Citation UI**:
   - khi backend trả về `citations`, frontend hiển thị dưới dạng thẻ nhỏ,
   - người dùng có thể rê chuột để xem snippet, score, và source id.
3. **Upload tài liệu**:
   - hỗ trợ kéo–thả/chọn file PDF, DOCX, TXT, MD,
   - gửi file lên endpoint upload của backend,
   - backend lưu file vào `data_input/` để sẵn sàng ingest.
4. **Trạng thái ingest** (tùy mức tích hợp):
   - gọi API bắt đầu ingest,
   - gọi API query trạng thái ingest (pending/processing/done/failed),
   - hiển thị thông báo cho người dùng.

Nhờ vậy, người mới chỉ cần:

- mở web app,
- tải tài liệu lên,
- đợi ingest/index,
- và bắt đầu hỏi chatbot về chính những tài liệu đó.

---

### 6. Tích hợp API: Cách frontend giao tiếp với backend

Frontend sử dụng một lớp client (ví dụ `api.ts`) để gọi các endpoint chính:

- `GET /health` – kiểm tra backend đang chạy.
- `POST /api/v1/chat` – gửi câu hỏi, nhận lại:
  - `answer`,
  - `citations`,
  - `model`,
  - `latency_ms`,
  - `conversation_id`.
- `GET /api/v1/history` – lấy lịch sử hội thoại.
- `DELETE /api/v1/history` – xóa toàn bộ lịch sử.
- `POST /api/v1/upload` – upload file tài liệu vào thư mục `data_input/`.
- `POST /api/v1/ingest` và `GET /api/v1/ingest/status/{id}` – bắt đầu ingest và kiểm tra tiến độ (tùy phiên bản backend bạn đang dùng).

Phần này giúp:

- tách riêng **logic UI** và **logic gọi API**,
- dễ thay đổi backend mà không phải sửa toàn bộ component React.

---

### 7. End-to-End Flow: Từ góc nhìn người dùng cuối

Nếu bạn viết blog cho người mới, có thể mô tả luồng sử dụng như sau:

1. **Chuẩn bị môi trường**:
   - Chạy Docker Compose hoặc khởi động backend + Ollama thủ công.
   - Xác nhận `/health` trả về `status: ok`.
2. **Mở frontend**:
   - Chạy `npm install` và `npm run dev` (hoặc build & deploy).
   - Truy cập `http://localhost:3000`.
3. **Tải tài liệu (Upload)**:
   - Chọn hoặc kéo–thả file PDF/DOCX/TXT/MD.
   - Đợi thông báo tải lên thành công.
4. **Ingest & Index**:
   - Gọi ingest (tự động hoặc qua UI),
   - đợi hệ thống đọc, parse, chia chunk, embedding, build index.
5. **Hỏi đáp**:
   - Nhập câu hỏi về nội dung tài liệu vừa tải,
   - xem câu trả lời kèm citation,
   - click/hover vào citation để xem snippet nguồn.

Cuối cùng, có thể chạy các script kiểm tra tổng thể để:

- chắc chắn backend + Ollama + dữ liệu + config đều ổn,
- trước khi mang demo cho người khác.

---

### 8. Tóm tắt phần việc của Người 5 cho người mới bắt đầu

Bạn có thể gói gọn lane 5 trong 3 ý:

1. **Eval** – có smoke test, system check để đảm bảo “mọi mảnh ghép đều đang chạy”.
2. **DevOps** – chuẩn hóa cách khởi động hệ thống (Docker, healthcheck, hướng dẫn môi trường).
3. **Frontend nhẹ** – cung cấp một UI đơn giản nhưng đầy đủ:
   - upload tài liệu,
   - theo dõi ingest/integration,
   - chat với tài liệu và xem citation.

Nhờ Người 5, dự án chatbot RAG không chỉ “đẹp trên giấy” mà thực sự trở thành một sản phẩm người mới có thể chạy, dùng và đánh giá chất lượng end‑to‑end.

