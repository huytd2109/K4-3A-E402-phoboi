# Ngữ cảnh chat demo

Giao diện tạo UUID riêng cho mỗi lần mở khung chat và gửi `session_id` cùng
`message` tới `/api/chat`. Backend lưu tối đa 128 phiên trong RAM, loại phiên
không hoạt động sau 30 phút khi nhận lượt truy cập tiếp theo. Tải lại giao diện
hoặc khởi động lại backend bắt đầu hội thoại mới. Client cũ không gửi session ID
vẫn được hỗ trợ nhưng không giữ ngữ cảnh giữa các yêu cầu.

Mỗi phiên giữ 6 tin nhắn gần nhất, tối đa 220 ký tự đã che dữ liệu nhạy cảm mỗi
tin. Prompt dùng lịch sử để hiểu câu nối tiếp; deadline/link vẫn do source store
và policy xác minh. Lịch sử không phải nguồn chính thức hay chỉ dẫn cho model.

Câu bổ sung task độc lập như `Lab 6` kế thừa loại câu hỏi logistics gần nhất.
Câu hỏi mới được model phân loại cùng lịch sử; tin hiện tại được ưu tiên.
Sau khi chuyển sang học tập, ngoài phạm vi, dữ liệu cá nhân hoặc chào hỏi,
trạng thái logistics cũ bị xóa. Lỗi provider không ghi thêm lượt hay tiêu thụ
trạng thái chờ làm rõ. Các yêu cầu cùng phiên được xử lý tuần tự.

Kiểm thử tự động: `tests/test_conversation.py`. Luồng thử thủ công:
`Hạn nộp lab khi nào?` → `Lab 6` → `Link nộp thì sao?`.

Đây là bộ nhớ trong một tiến trình cho ứng dụng demo. Nếu triển khai nhiều
backend hoặc có tài khoản người dùng, cần kho phiên dùng chung và ràng buộc
quyền sở hữu phiên với tài khoản đã xác thực.
