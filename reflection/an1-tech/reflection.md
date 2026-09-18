# Individual Reflection — Đỗ Quốc An
## Thông tin cá nhân

- Họ và tên: Đỗ Quốc An
- Mã học viên: 2A202602892
- GitHub username: `an1-tech`
- Nhóm: Phoboi — lớp 3A, phòng E402, Track B1
- Vai trò: UX & Documentation
- Phần việc chính: Docs, README, CLI demo, UI mockup

---

## 1. Tôi đã tham gia vào phần nào?

| Hoạt động | Tôi đã làm gì? | Kết quả / ảnh hưởng tới nhóm |
|---|---|---|
| User flow | Chuyển policy kỹ thuật thành luồng người dùng dễ hiểu: hỏi → phân tích → verified answer, clarify, restrict hoặc handoff | Demo thể hiện được cả happy path lẫn các nhánh an toàn thay vì chỉ có một câu trả lời đẹp |
| UI mockup | Hoàn thiện giao diện React/Vite cho trải nghiệm hội thoại và trạng thái kết quả | Nhóm có prototype bấm được để trình bày ở checkpoint và thu feedback từ người dùng |
| Minh bạch dữ liệu demo | Thay tên giống người thật bằng persona demo, đổi badge dễ gây hiểu nhầm và thêm banner synthetic cố định | Người xem không nhầm deadline/URL trong fixture với thông tin khóa học thật |
| CLI demo | Chuẩn bị kịch bản chạy `chat`, `analyze-data`, `report` và `eval`, gồm cả câu hỏi hợp lệ, thiếu task, conflict và no-source | Nhóm có đường demo dự phòng minh bạch, dễ tái hiện nếu UI hoặc mạng gặp vấn đề |
| Documentation | Biên soạn README, hướng dẫn nguồn, kiến trúc, fixture và checklist validation | Người ngoài có thể hiểu cách chạy, source mode, giới hạn và vị trí bằng chứng mà không phải đọc toàn bộ code |
| UX writing | Viết nội dung clarify đúng một câu, handoff có lý do và badge nguồn rõ ràng | Các trạng thái “không trả lời” vẫn giúp người dùng biết phải làm gì tiếp theo |
| Feedback | Tổng hợp phản hồi người dùng và liên kết phản hồi với quyết định UX | Nhóm có bằng chứng usability định tính, đồng thời ghi rõ nó không thay thế evaluation kỹ thuật |

**Dấu tay rõ nhất của tôi trong artifact cuối:**

```text
Dấu tay rõ nhất của tôi là cách trình bày sự khác nhau giữa VERIFIED, DỮ LIỆU DEMO, CLARIFY và HANDOFF trên UI, CLI và tài liệu. Tôi giúp biến boundary kỹ thuật của nhóm thành tín hiệu mà người dùng có thể nhìn thấy và hành động đúng.
```

---

## 2. Bảng dùng AI

| Giai đoạn | Tôi dùng AI để làm gì? | AI hữu ích ở đâu? | AI sai / hời hợt ở đâu? | Tôi sửa gì bằng nhận định của mình? |
|---|---|---|---|---|
| UX flow | Gợi ý các trạng thái và microcopy cho answer, clarify, restrict, handoff | Giúp tạo nhanh nhiều phương án diễn đạt | Có xu hướng làm lời nhắn dài, trấn an quá mức hoặc che mất lý do không trả lời | Rút gọn thông điệp, nêu rõ trạng thái và next action trước |
| UI mockup | Gợi ý bố cục chat, badge, source card và trạng thái loading/error | Tăng tốc xây prototype có thể bấm thử | Dễ tạo badge “official/verified” quá thuyết phục cho fixture giả lập | Đổi nhãn, persona và thêm banner `DỮ LIỆU DEMO` cố định |
| Documentation | Hỗ trợ lập dàn ý README và diễn giải module kỹ thuật | Giúp tài liệu nhất quán, dễ đọc hơn | Đôi lúc tự suy diễn tính năng đã hoàn thành hoặc bỏ qua giới hạn live | Kiểm tra từng claim với code, test report và source policy trước khi giữ lại |
| Demo script | Gợi ý chuỗi câu hỏi để đi qua nhiều nhánh trong thời gian ngắn | Giúp demo có mở đầu, cao trào và kết luận rõ | Thường ưu tiên happy path, ít nói về conflict/quota/no-source | Bổ sung failure path và chuẩn bị CLI làm phương án dự phòng |

> AI hỗ trợ viết nháp và tạo phương án; toàn bộ claim về tính năng, kết quả, nguồn và trạng thái demo đều được đối chiếu với artifact chạy thật.

---

## 3. Reflection câu hỏi mở

**Reflection:**

```text
Qua dự án này, tôi nhận ra UX của một sản phẩm AI không chỉ là làm giao diện đẹp hoặc câu trả lời tự nhiên. Với thông tin deadline, người dùng cần nhìn thấy vì sao câu trả lời đáng tin và phải làm gì khi hệ thống không đủ bằng chứng. Ban đầu tôi muốn tối giản giao diện bằng cách chỉ hiển thị nội dung trả lời, nhưng cách đó làm mất provenance và che giấu sự khác nhau giữa dữ liệu thật với fixture demo. Sau khi trao đổi với nhóm, tôi thêm badge trạng thái, source card và banner demo cố định. Tôi cũng học được rằng clarify và handoff không phải failure UX nếu lời nhắn ngắn, nói rõ lý do và cho người dùng một bước tiếp theo. Phần tôi đóng góp rõ nhất là chuyển các khái niệm kỹ thuật như source mode, conflict và fail-closed thành tín hiệu dễ hiểu trên UI, CLI và tài liệu. Việc chuẩn bị CLI demo giúp nhóm không phụ thuộc hoàn toàn vào giao diện hoặc kết nối mạng trong buổi trình bày. Khi rà tài liệu, tôi thấy một claim viết trôi chảy vẫn có thể sai nếu không kiểm tra lại code và báo cáo evaluation. Vì vậy tôi giữ rõ giới hạn: feedback người dùng là bằng chứng định tính, còn fixture không phải thông tin khóa học chính thức. Nếu làm lại, tôi sẽ tổ chức usability test theo task cụ thể và ghi nguyên văn quote, điểm kẹt, thời gian hoàn thành ngay từ vòng prototype đầu. Tôi cũng sẽ bổ sung accessibility và responsive review sớm hơn thay vì để gần lúc demo mới kiểm tra.
```

---

## 4. Tự kiểm cuối bài

- [x] Nêu rõ vai trò UX, documentation và demo
- [x] Thể hiện các trạng thái answer, clarify, restrict và handoff
- [x] Phân biệt rõ dữ liệu thật với synthetic fixture
- [x] Không dùng feedback định tính thay cho kết quả evaluation
- [x] Có artifact cụ thể trên UI, CLI và tài liệu
- [x] Có bài học và kế hoạch cải thiện trải nghiệm người dùng

