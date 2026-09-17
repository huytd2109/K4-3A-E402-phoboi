# Blockers & External Inputs Needed for Production

Để triển khai bot lên môi trường production, chúng ta cần cung cấp các thông tin sau:

- **Discord guild ID**: ID của server Discord.
- **Authorized channel IDs**: Các kênh được phép trích xuất thông tin official.
- **Authorized role IDs**: Các role có thẩm quyền đưa ra thông báo chính thức.
- **TA role ID and handoff channel**: Kênh và role của TA để bot chuyển giao khi gặp conflict hoặc không tìm thấy nguồn.
- **Real deadline announcement URLs/message IDs**: Nguồn thật sự chứa thông báo deadline để bot theo dõi.
- **Discord bot token**: Cần lưu trong `.env` (không bao giờ commit lên git).

## Khuyến nghị xử lý dữ liệu
- File `survey.csv` đang bị track bởi git (được thêm vào trước khi có rule `*.csv` trong gitignore). **Khuyến nghị**: Di chuyển file vào thư mục `data/` (đã được gitignore) hoặc giữ nguyên nếu cần thiết, nhưng không tự động xóa.
- Thư mục `data/discord-pack/` đang chứa dữ liệu thực tế đã được commit. Theo chính sách dữ liệu, thông tin này không nên để public. **Khuyến nghị**: Xóa khỏi lịch sử git công khai.
