# Quy trình Xây dựng Pipeline Ingest Dữ liệu cho Hệ thống Chatbot RAG

Trong kiến trúc của hệ thống Retrieval-Augmented Generation (RAG), giai đoạn chuẩn bị và ingest dữ liệu đóng vai trò quyết định đến độ chính xác và hiệu quả của các câu trả lời do mô hình ngôn ngữ lớn (LLM) sinh ra. Bài viết này trình bày chi tiết về quy trình kỹ thuật trong việc xây dựng pipeline ingest dữ liệu, từ khâu tiếp nhận tài liệu thô đến khâu lưu trữ trong cơ sở dữ liệu vector.

---

## 1. Tổng quan về Kiến trúc Pipeline

Quy trình ingest dữ liệu được thiết kế theo mô hình tuyến tính gồm ba giai đoạn chính:
1. **Tiếp nhận và Trích xuất (Loading):** Thu thập tài liệu từ các định dạng lưu trữ khác nhau.
2. **Phân đoạn Văn bản (Splitting):** Chia nhỏ dữ liệu nhằm tối ưu hóa khả năng truy xuất và tuân thủ giới hạn context window của LLM.
3. **Số hóa và Lưu trữ (Indexing):** Chuyển đổi văn bản thành các vector đặc trưng và lưu trữ vào Vector Database.

---

## 2. Chi tiết các Bước Thực hiện

### Bước 1: Tiếp nhận và Trích xuất Dữ liệu (Document Loading)

Để đảm bảo khả năng xử lý đa dạng các loại tài liệu như PDF, DOCX, Markdown và TXT, hệ thống sử dụng giải pháp nạp dữ liệu từ thư mục. Quy trình này được điều phối bởi các thành phần kỹ thuật sau:

*   **DirectoryLoader:** Thành phần chịu trách nhiệm quét và quản lý việc nạp dữ liệu từ một thư mục cụ thể trên hệ thống lưu trữ.
*   **UnstructuredFileLoader:** Một công cụ xử lý mạnh mẽ giúp trích xuất nội dung văn bản thuần túy từ nhiều định dạng tập tin khác nhau mà không làm mất đi thông tin văn bản cốt lõi.
*   **Glob Pattern:** Sử dụng bộ lọc mẫu để xác định chính xác các loại tập tin cần thu thập (ví dụ: tất cả các tập tin trong thư mục và thư mục con).
*   **Multithreading (Đa luồng):** Kỹ thuật cho phép hệ thống xử lý song song nhiều tập tin cùng một lúc. Điều này giúp tối ưu hóa tài nguyên phần cứng (CPU) và giảm thiểu đáng kể thời gian chờ đợi khi khối lượng tài liệu lên tới hàng trăm hoặc hàng nghìn tệp.

---

### Bước 2: Phân đoạn Văn bản (Text Splitting)

Văn bản sau khi trích xuất thường quá dài để mô hình ngôn ngữ có thể xử lý hiệu quả trong một lần truy vấn. Do đó, việc chia nhỏ văn bản thành các đoạn (chunks) là bắt buộc, dựa trên các thuật toán phân tách thông minh:

*   **RecursiveCharacterTextSplitter:** Thuật toán phân đoạn văn bản theo hướng đệ quy. Thay vì cắt ngang văn bản một cách ngẫu nhiên, thuật toán này sẽ ưu tiên tìm kiếm các điểm ngắt tự nhiên như dấu xuống dòng của tiêu đề, đoạn văn hoặc dấu chấm câu. Điều này giúp giữ cho mỗi phân đoạn văn bản luôn mang một ý nghĩa hoàn chỉnh.
*   **Chunk Size (Kích thước đoạn):** Thông số xác định độ dài tối đa của mỗi đoạn văn bản sau khi chia. Việc lựa chọn kích thước phù hợp giúp AI dễ dàng xử lý mà không bị quá tải thông tin.
*   **Chunk Overlap (Độ gối đầu):** Một phần nội dung ở cuối đoạn trước sẽ được lặp lại ở đầu đoạn sau. Kỹ thuật này đóng vai trò như một "sợi dây liên kết" ngữ nghĩa, đảm bảo rằng thông tin quan trọng nằm ở biên giới giữa hai đoạn không bị mất đi ý nghĩa khi bị chia cắt.
*   **Separators (Dấu phân tách):** Các ký hiệu đặc biệt được định nghĩa trước (như định dạng tiêu đề Markdown, mã nguồn, hoặc các dấu xuống dòng) để hướng dẫn thuật toán nơi nên ưu tiên thực hiện việc ngắt đoạn.

---

### Bước 3: Số hóa và Lưu trữ Vector (Vector Indexing)

Đây là giai đoạn chuyển đổi trí tuệ của con người thành ngôn ngữ toán học mà máy tính có thể hiểu được thông qua quy trình định danh vector:

*   **OllamaEmbeddings:** Sử dụng mô hình ngôn ngữ (như Llama 3) để thực hiện tác vụ "nhúng" (embedding). Quá trình này chuyển hóa mỗi đoạn văn bản thành một chuỗi các con số (vector) đại diện cho ý nghĩa ngữ nghĩa của nó trong không gian đa chiều.
*   **Vector Store (Chroma):** Một cơ sở dữ liệu chuyên dụng để lưu trữ các vector này. Khác với cơ sở dữ liệu truyền thống tìm kiếm theo từ khóa chính xác, Vector Store cho phép tìm kiếm theo "ý nghĩa" (Similarity Search). Khi người dùng đặt câu hỏi, hệ thống sẽ tìm trong kho lưu trữ này những đoạn văn bản có vector gần giống nhất với ý đồ của câu hỏi đó.
*   **Persistence (Lưu trữ bền vững):** Thiết lập cơ chế lưu trữ dữ liệu vector xuống ổ đĩa vật lý, cho phép hệ thống có thể truy xuất lại dữ liệu đã xử lý bất cứ lúc nào mà không cần thực hiện lại quy trình số hóa từ đầu.

---

## 3. Đánh giá và Kiểm thử

Sau khi hoàn tất quá trình lưu trữ, hệ thống sẽ thực hiện các truy vấn thực nghiệm để kiểm tra độ chính xác của các đoạn văn bản được trả về. Một pipeline chất lượng cao sẽ cho ra các kết quả có sự tương đồng lớn về mặt ý nghĩa với câu hỏi, từ đó cung cấp một ngữ cảnh đầu vào sạch và đầy đủ nhất cho mô hình ngôn ngữ lớn (LLM) để sinh câu trả lời.
