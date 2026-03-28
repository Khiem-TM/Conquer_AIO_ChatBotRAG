# Quy chế Nội bộ & Tuân thủ Pháp lý (Bản thử nghiệm cho RAG)

## 1. Mục đích tài liệu
Tài liệu này mô tả bộ quy tắc nội bộ của Công ty Cổ phần Dịch vụ Số Ánh Dương (gọi tắt là "Công ty") nhằm kiểm thử hệ thống RAG theo các tiêu chí: chunking văn bản dài, truy hồi ngữ cảnh chính xác, và trả lời có trích dẫn.

Mục tiêu tuân thủ gồm:
- Tuân thủ Bộ luật Lao động 2019.
- Tuân thủ Luật An ninh mạng 2018.
- Tuân thủ Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân.
- Tuân thủ quy định nội bộ về bảo mật, làm việc từ xa, và quản lý tài sản số.

## 2. Phạm vi áp dụng
2.1. Áp dụng cho toàn bộ nhân sự chính thức, thử việc, cộng tác viên có quyền truy cập hệ thống thông tin của Công ty.
2.2. Áp dụng cho toàn bộ thiết bị do Công ty cấp và thiết bị cá nhân có đăng nhập tài khoản Công ty.
2.3. Áp dụng tại văn phòng chính, chi nhánh, và môi trường làm việc từ xa.

## 3. Định nghĩa
3.1. "Dữ liệu cá nhân" là thông tin dưới dạng ký hiệu, chữ viết, số, hình ảnh, âm thanh hoặc dạng tương tự gắn với một cá nhân cụ thể.
3.2. "Dữ liệu nhạy cảm" bao gồm nhưng không giới hạn: thông tin sức khỏe, tài chính, sinh trắc học, vị trí thời gian thực.
3.3. "Sự cố an toàn thông tin" là mọi sự kiện làm mất tính bảo mật, toàn vẹn hoặc sẵn sàng của dữ liệu/hệ thống.

## 4. Nguyên tắc xử lý dữ liệu
4.1. Chỉ thu thập dữ liệu phù hợp mục đích công việc và theo nguyên tắc tối thiểu cần thiết.
4.2. Mọi hoạt động xử lý dữ liệu cá nhân phải có căn cứ pháp lý rõ ràng (đồng ý, nghĩa vụ hợp đồng, nghĩa vụ pháp luật...).
4.3. Dữ liệu phải được phân loại theo 4 mức: Công khai, Nội bộ, Mật, Tuyệt mật.
4.4. Dữ liệu mức Mật và Tuyệt mật bắt buộc mã hóa khi lưu trữ và truyền tải.

## 5. Quy định lưu trữ và thời hạn
5.1. Hồ sơ nhân sự: lưu tối thiểu 10 năm kể từ ngày chấm dứt hợp đồng lao động.
5.2. Nhật ký truy cập hệ thống (system access logs): lưu tối thiểu 24 tháng.
5.3. Hồ sơ sự cố an toàn thông tin: lưu tối thiểu 05 năm.
5.4. Dữ liệu khách hàng không còn mục đích xử lý phải được xóa hoặc ẩn danh trong vòng 30 ngày.

## 6. Kiểm soát truy cập
6.1. Mọi tài khoản nội bộ phải bật xác thực đa yếu tố (MFA).
6.2. Không dùng chung tài khoản; mỗi người dùng một định danh riêng.
6.3. Quyền truy cập cấp theo nguyên tắc "ít quyền nhất" (least privilege).
6.4. Rà soát quyền truy cập thực hiện định kỳ mỗi quý.

## 7. Làm việc từ xa
7.1. Nhân sự làm việc từ xa phải kết nối VPN do Công ty cấp.
7.2. Cấm sao chép dữ liệu mức Mật/Tuyệt mật sang USB cá nhân.
7.3. Không sử dụng Wi-Fi công cộng không mật khẩu cho công việc.
7.4. Màn hình phải khóa tự động tối đa sau 05 phút không hoạt động.

## 8. Quy trình báo cáo sự cố
8.1. Khi phát hiện sự cố, nhân sự phải báo ngay trong vòng 30 phút qua kênh #sec-incident hoặc hotline SOC nội bộ.
8.2. Bộ phận An toàn thông tin (ATTT) phân loại mức độ sự cố trong vòng 02 giờ.
8.3. Sự cố mức Nghiêm trọng phải báo cáo Ban Điều hành trong vòng 04 giờ.
8.4. Sau khắc phục, phải có báo cáo hậu kiểm (post-incident report) trong vòng 07 ngày.

## 9. Trách nhiệm các bên
9.1. Nhân sự: tuân thủ chính sách, bảo mật thông tin xác thực, báo cáo sự cố đúng hạn.
9.2. Quản lý trực tiếp: phê duyệt quyền truy cập, giám sát tuân thủ tại đơn vị.
9.3. Bộ phận Nhân sự: truyền thông chính sách, lưu trữ hồ sơ kỷ luật.
9.4. Bộ phận ATTT: giám sát, điều tra, khuyến nghị biện pháp phòng ngừa.

## 10. Chế tài xử lý vi phạm
10.1. Vi phạm mức nhẹ: nhắc nhở bằng văn bản và đào tạo lại bắt buộc.
10.2. Vi phạm mức trung bình: cảnh cáo, tạm đình chỉ quyền hệ thống từ 03 đến 30 ngày.
10.3. Vi phạm nghiêm trọng: xem xét chấm dứt hợp đồng và bồi thường thiệt hại theo pháp luật.
10.4. Trường hợp có dấu hiệu hình sự, Công ty chuyển hồ sơ cho cơ quan có thẩm quyền.

## 11. Điều khoản kiểm thử RAG (phục vụ demo)
11.1. Câu hỏi mẫu 1: "Thời gian báo cáo sự cố ban đầu là bao lâu?"
Trả lời mong đợi: trong vòng 30 phút.

11.2. Câu hỏi mẫu 2: "Nhật ký truy cập hệ thống lưu bao lâu?"
Trả lời mong đợi: tối thiểu 24 tháng.

11.3. Câu hỏi mẫu 3: "Dữ liệu khách hàng không còn mục đích xử lý thì khi nào xóa/ẩn danh?"
Trả lời mong đợi: trong vòng 30 ngày.

11.4. Câu hỏi mẫu 4: "Sự cố mức nghiêm trọng báo Ban Điều hành trong bao lâu?"
Trả lời mong đợi: trong vòng 04 giờ.

## 12. Điều khoản hiệu lực
12.1. Tài liệu có hiệu lực từ ngày 01/01/2026.
12.2. Phiên bản hiện tại: v1.3-test-rag.
12.3. Chủ sở hữu tài liệu: Phòng Pháp chế & Tuân thủ phối hợp với Phòng ATTT.

