# CP4 — Nội dung nộp và kịch bản gặp TA

## Nội dung điền form

- **Tên đội:** phoboi
- **Đội trưởng:** Nguyễn Hoàng Sơn
- **Mã học viên:** 2A202602457
- **Phòng:** E402
- **Link spec:**
  `https://github.com/huytd2109/K4-3A-E402-phoboi/blob/tong-hop-cp2/spec.md`

### Chuẩn “đạt” đã khóa

Đạt khi ít nhất 95% toàn bộ 48 golden case qua, đồng thời số deadline sai bằng
0, deadline thiếu nguồn bằng 0, câu trả lời làm lộ dữ liệu cá nhân bằng 0, conflict
không được xử lý bằng 0 và 4/4 hard tests đạt. Trong live eval, case rơi về
rule-based fallback không được tính đạt. Nhóm không hạ chuẩn này sau CP4.

### Phần chưa hoàn thành

Nhóm có survey 22 phản hồi; theo tiêu chí bảo thủ, 18/22 người (81,8%) xác nhận
ít nhất một hậu quả. Tuy nhiên CSV không có tên/mã/vai trò nên chưa tự chứng minh
người trả lời ngoài nhóm; Câu 7 và Câu 12 chỉ có 1/22 câu trả lời mở. Nhóm đã xác
nhận hai willing users là Nguyễn Văn Việt và Hà Huy Nhất, nhưng họ chưa trực tiếp
dùng thử và chưa có quan sát/quote thực tế. Nguồn chính thức trong demo vẫn là fixture,
Discord bot chưa được chứng minh deploy production. Lượt Gemini thật gần nhất
đạt 4/48 do 44 case rơi về fallback, nên chưa đạt quality bar 95%. Nhóm chưa làm
multi-prototype có user test.

## Kịch bản show TA trong 2 phút

1. Mở `spec.md` §1: chỉ survey 22 người, kết quả 18/22 xác nhận pain, phương pháp
   mining 14 tin/12 tác giả và 6 quote.
2. Mở §2: chỉ bảng impact ba ứng viên và lý do loại điểm danh/XP dù có nhiều câu
   hỏi hơn.
3. Mở §4: nói rõ prototype là Mock và automation là Conditional.
4. Mở §4b và §5: chỉ ≥4 nguyên tắc có vị trí áp dụng cùng 4 lớp/8 kịch bản.
5. Mở §7: đọc quality bar 95% và bảng kết quả 48/48 offline so với 4/48 live.
6. Mở §8: chỉ danh sách phần chưa hoàn thành và kế hoạch validation/dry run.

## Câu trình bày ngắn

“Nhóm phoboi chọn học viên K4 đang hỏi deadline trên Discord. Mining 779 tin do
người viết trong gần ba ngày cho thấy 14 câu hỏi logistics từ 12 tác giả, 7 câu
tag bot trực tiếp. Nhóm dùng Conditional automation: Gemini chỉ phân loại intent
và entity; policy chỉ trả lời khi có đúng một nguồn, còn thiếu hoặc conflict thì
hỏi lại/chuyển TA. Golden set có 48 case phủ bốn lớp rủi ro. Quality bar khóa tại
CP4 là 95% cùng bốn zero-gate và 4/4 hard tests. Lượt offline đạt 48/48 nhưng lượt
Gemini thật mới 4/48 do 44 fallback, nên nhóm khai trạng thái HOLD và không hạ
quality bar.”
