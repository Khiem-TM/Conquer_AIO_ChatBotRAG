# Nghiên cứu và Thực hiện Trực quan hóa Dữ liệu bằng Python

## 1. Mở đầu: Tầm quan trọng của trực quan hóa dữ liệu

Trong phân tích dữ liệu hiện đại, trực quan hóa không đơn thuần là việc trình bày các con số dưới dạng hình ảnh, mà là một quy trình thiết yếu để chuyển hóa thông tin thô thành tri thức hữu dụng. Như Cole Nussbaumer Knaflic đã khẳng định trong tác phẩm *Storytelling With Data: A Data Visualization Guide for Business Professionals*:

> "Trực quan hóa dữ liệu là sự giao thoa giữa khoa học và nghệ thuật. Nó không chỉ đơn giản là tạo ra những biểu đồ đẹp mắt, mà là hiểu rõ bối cảnh, lựa chọn cách hiển thị phù hợp và loại bỏ những yếu tố gây nhiễu để tập trung vào thông điệp cốt lõi."

Việc bỏ qua bước trực quan hóa và chỉ dựa vào các chỉ số thống kê tổng hợp có thể dẫn đến những sai lầm nghiêm trọng trong việc nhận diện bản chất của hiện tượng và đưa ra quyết định sai lệch.

### 1.1. Phân tích thực nghiệm qua Bộ tứ Anscombe (Anscombe's Quartet)

Để minh chứng cho tầm quan trọng của việc quan sát dữ liệu bằng hình ảnh, nhà thống kê Francis Anscombe đã xây dựng bốn bộ dữ liệu (được ký hiệu là I, II, III, IV). Mặc dù các bộ dữ liệu này có cấu trúc điểm dữ liệu khác nhau hoàn toàn, chúng lại sở hữu các đặc trưng thống kê mô tả gần như đồng nhất.

#### Dữ liệu thô và Thống kê mô tả
Trước khi quan sát bằng biểu đồ, việc xem xét dữ liệu thô và các chỉ số thống kê là bước đầu tiên trong quy trình phân tích. Bảng dưới đây trình bày chi tiết các cặp giá trị $(x, y)$ của bốn tập dữ liệu:

| STT | Tập I (x) | Tập I (y) | Tập II (x) | Tập II (y) | Tập III (x) | Tập III (y) | Tập IV (x) | Tập IV (y) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 10.0 | 8.04 | 10.0 | 9.14 | 10.0 | 7.46 | 8.0 | 6.58 |
| 2 | 8.0 | 6.95 | 8.0 | 8.14 | 8.0 | 6.77 | 8.0 | 5.76 |
| 3 | 13.0 | 7.58 | 13.0 | 8.74 | 13.0 | 12.74 | 8.0 | 7.71 |
| 4 | 9.0 | 8.81 | 9.0 | 8.77 | 9.0 | 7.11 | 8.0 | 8.84 |
| 5 | 11.0 | 8.33 | 11.0 | 9.26 | 11.0 | 7.81 | 8.0 | 8.47 |
| 6 | 14.0 | 9.96 | 14.0 | 8.10 | 14.0 | 8.84 | 8.0 | 7.04 |
| 7 | 6.0 | 7.24 | 6.0 | 6.13 | 6.0 | 6.08 | 8.0 | 5.25 |
| 8 | 4.0 | 4.26 | 4.0 | 3.10 | 4.0 | 5.39 | 19.0 | 12.50 |
| 9 | 12.0 | 10.84 | 12.0 | 9.13 | 12.0 | 8.15 | 8.0 | 5.56 |
| 10 | 7.0 | 4.82 | 7.0 | 7.26 | 7.0 | 6.42 | 8.0 | 7.91 |
| 11 | 5.0 | 5.68 | 5.0 | 4.74 | 5.0 | 5.73 | 8.0 | 6.89 |

Kết quả tính toán các chỉ số cơ bản trên cả bốn bộ dữ liệu cho thấy sự tương đồng tới chữ số thập phân thứ hai:

| Chỉ số thống kê | Giá trị |
| :--- | :--- |
| Số lượng quan sát ($n$) | 11 |
| Giá trị trung bình của biến $x$ ($\bar{x}$) | 9.0 |
| Giá trị trung bình của biến $y$ ($\bar{y}$) | 7.50 |
| Phương sai của biến $x$ ($s^2_x$) | 11.0 |
| Phương sai của biến $y$ ($s^2_y$) | 4.12 |
| Hệ số tương quan Pearson ($r$) | 0.816 |
| Phương trình hồi quy tuyến tính | $y = 3.00 + 0.500x$ |

#### Kết quả trực quan hóa
Tuy nhiên, khi thực hiện vẽ biểu đồ phân tán (Scatter Plot) kết hợp đường hồi quy, sự khác biệt về bản chất của các tập dữ liệu được bộc lộ rõ rệt:



* **Bộ dữ liệu I:** Tuân thủ mô hình tuyến tính với một độ lệch chuẩn nhất định xung quanh đường hồi quy. Đây là trường hợp lý tưởng cho các thuật toán hồi quy đơn giản.
* **Bộ dữ liệu II:** Dữ liệu có mối quan hệ phi tuyến tính rõ rệt (dạng parabol). Việc áp dụng mô hình tuyến tính ở đây là không phù hợp và dẫn đến sai số dự báo lớn.
* **Bộ dữ liệu III:** Tồn tại một mối quan hệ tuyến tính hoàn hảo nhưng bị sai lệch bởi một điểm dữ liệu ngoại lai (outlier) nằm xa trục chính, làm thay đổi đáng kể hệ số góc của đường hồi quy.
* **Bộ dữ liệu IV:** Cho thấy cấu trúc dữ liệu không bình thường khi các giá trị $x$ không đổi (ngoại trừ một điểm), khiến mô hình hồi quy không phản ánh đúng xu hướng thực tế của phần lớn dữ liệu.

Kết luận từ thực nghiệm này khẳng định rằng: Trực quan hóa dữ liệu là bước bắt buộc để kiểm chứng các giả định thống kê trước khi tiến hành các phân tích chuyên sâu.

### 1.2. Hệ sinh thái thư viện Python: Matplotlib và Seaborn

Trong môi trường lập trình Python, việc triển khai trực quan hóa được hỗ trợ chủ yếu bởi hai thư viện trọng tâm:

* **Matplotlib:** Đóng vai trò là thư viện nền tảng (low-level), cung cấp các giao diện lập trình để điều chỉnh chi tiết cấu trúc biểu đồ, từ trục tọa độ cho đến các thuộc tính hình học phức tạp.
* **Seaborn:** Là thư viện bậc cao (high-level) được xây dựng trên nền tảng Matplotlib. Thư viện này tối ưu hóa cho các phân tích thống kê, hỗ trợ trực tiếp cấu trúc dữ liệu DataFrame của Pandas và tự động hóa việc thiết lập thẩm mỹ đồ họa, giúp quy trình làm việc trở nên hiệu quả hơn.

## 5. Kết luận và Các nguyên tắc tối ưu hóa

### 5.1. Lựa chọn loại hình biểu đồ phù hợp
Việc lựa chọn sai dạng biểu đồ có thể dẫn đến sự hiểu lầm về quy mô hoặc mối quan hệ của dữ liệu. 
* **Hạn chế biểu đồ tròn (Pie Chart):** Trong phân tích chuyên sâu, biểu đồ tròn thường bị hạn chế, đặc biệt khi số lượng danh mục vượt quá 3-5 nhóm. Khả năng nhận diện sự khác biệt về diện tích góc của mắt người kém hơn so với việc so sánh độ dài (biểu đồ cột). 
* **Khuyến nghị:** Sử dụng biểu đồ cột ngang (Horizontal Bar Chart) để thay thế khi có nhiều danh mục hoặc tên danh mục dài, giúp đảm bảo tính dễ đọc và so sánh chính xác.

### 5.2. Nguyên tắc tối giản và loại bỏ yếu tố gây nhiễu (Chartjunk)
Dựa trên lý thuyết của Edward Tufte, hiệu suất của một biểu đồ được đo bằng tỷ lệ "Mực-Dữ liệu" (Data-Ink ratio).
* **Loại bỏ Chartjunk:** Cần lược bỏ các đường lưới (gridlines) quá đậm, các hiệu ứng đổ bóng 3D không cần thiết, hoặc các khung viền rườm rà. 
* **Tập trung vào thông tin cốt lõi:** Việc giữ cho biểu đồ sạch sẽ giúp người xem tập trung ngay lập tức vào các xu hướng hoặc điểm dữ liệu ngoại lai quan trọng.

### 5.3. Chiến lược sử dụng màu sắc và bảng màu (Palettes)
Màu sắc trong Seaborn và Matplotlib không chỉ mang tính thẩm mỹ mà còn mang tính chức năng:
* **Sử dụng Color Palettes:** Cần chọn bảng màu phù hợp với tính chất dữ liệu:
    * *Qualitative palettes:* Dùng cho dữ liệu phân loại không có thứ tự.
    * *Sequential palettes:* Dùng cho dữ liệu có sự biến thiên liên tục (thấp đến cao).
    * *Diverging palettes:* Dùng để nhấn mạnh sự khác biệt từ một điểm trung tâm (ví dụ: tăng trưởng âm và dương).


### 5.4. Tổng kết
Trực quan hóa dữ liệu bằng Seaborn và Matplotlib không chỉ dừng lại ở việc thực thi mã nguồn, mà là quá trình tư duy để lựa chọn phương thức biểu đạt trung thực nhất đối với bản chất của dữ liệu. Việc tuân thủ các nguyên tắc về sự đơn giản và tính chính xác sẽ giúp nhà phân tích chuyển đổi các tập dữ liệu phức tạp thành những thông tin có giá trị thực tiễn cao.