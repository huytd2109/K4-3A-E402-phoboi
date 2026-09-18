# Individual Reflection — Nguyễn Hoàng Sơn
## Thông tin cá nhân

- Họ và tên: Nguyễn Hoàng Sơn
- Mã học viên: 2A202602457
- GitHub username: `sown101`
- Nhóm: Phoboi — lớp 3A, phòng E402, Track B1
- Vai trò: AI Engineer
- Phần việc chính: Spec, evidence mining, core pipeline, evaluation

---

## 1. Tôi đã tham gia vào phần nào?

| Hoạt động | Tôi đã làm gì? | Kết quả / ảnh hưởng tới nhóm |
|---|---|---|
| Xác định bài toán | Cùng nhóm thu hẹp bài toán từ trợ lý Discord tổng quát xuống một lát cắt có thể kiểm chứng: deadline, link và cách nộp bài | Nhóm có một JTBD rõ, tránh xây chatbot trả lời mọi thứ nhưng không bảo đảm độ tin cậy |
| Evidence mining | Phân tích bộ Discord gồm 1.092 dòng, tách 779 tin người dùng và thống kê các nhóm pain như deadline, submission, điểm danh và XP | Tạo bằng chứng định lượng cho `docs/evidence.md` và giúp nhóm chọn đúng pain có cost-of-error cao |
| AI Spec | Viết và hiệu chỉnh các phần user/job, impact, scope, failure modes, success metrics và giới hạn của sản phẩm | `spec.md` mô tả rõ tiêu chuẩn đạt, non-goals và sự khác nhau giữa kết quả offline với kết quả live |
| Core pipeline | Thiết kế luồng phân tích intent/entity rồi chuyển kết quả qua policy xác định; không cho mô hình tự viết deadline hoặc tự phong nguồn chính thức | Giảm rủi ro hallucination và tạo ranh giới rõ giữa phần AI suy luận với phần code ra quyết định |
| Prompt và schema | Xây dựng đầu ra có cấu trúc cho message analyzer, giữ thứ tự/ID của batch và thêm tín hiệu confidence, personal-data, injection | Output của mô hình trở thành dữ liệu đầu vào có thể validate thay vì câu trả lời tự do khó kiểm soát |
| Evaluation | Xây golden set 48 ca gồm happy path, thiếu entity, conflict, no-source, personal data, injection và mixed intent | Nhóm đo được cả utility và safety; kết quả live 21/48 cũng được giữ lại để chỉ ra khoảng cách cần cải thiện |
| Phân tích giới hạn | Tách bộ dữ liệu thật thành candidate-only vì không có URL hoặc bộ Discord ID đủ để xác minh provenance | Ngăn hệ thống phát hành deadline “verified” từ dữ liệu ẩn danh và giữ `unverified_deadline_released = 0` |

**Dấu tay rõ nhất của tôi trong artifact cuối:**

```text
Dấu tay rõ nhất của tôi là mạch evidence → spec → pipeline → evaluation. Tôi góp phần biến yêu cầu “trợ lý Discord” thành một hệ thống chỉ dùng AI để phân loại/trích xuất, còn quyền xác nhận deadline được giữ trong policy xác định và source contract.
```

---

## 2. Bảng dùng AI

| Giai đoạn | Tôi dùng AI để làm gì? | AI hữu ích ở đâu? | AI sai / hời hợt ở đâu? | Tôi sửa gì bằng nhận định của mình? |
|---|---|---|---|---|
| Evidence mining | Hỗ trợ nhóm từ khóa và phân loại sơ bộ các pain trong dữ liệu Discord | Tăng tốc việc hình thành các nhóm deadline, submission, attendance và XP | Dễ xem tần suất từ khóa là bằng chứng đủ mạnh cho nhu cầu sản phẩm | Chỉ coi keyword scan là prevalence, kiểm tra lại mẫu theo `msg_id` và ghi rõ đây không phải độ chính xác classifier |
| Spec | Phản biện scope, failure modes và success metrics | Giúp phát hiện các trường hợp thiếu task, conflict, low confidence và no-source | Có xu hướng đề xuất chatbot/RAG rộng hơn lát cắt hackathon | Giữ MVP ở logistics có thể kiểm chứng và đưa daily digest, dữ liệu cá nhân ra khỏi scope |
| Core pipeline | Gợi ý schema đầu ra và các tình huống lỗi khi gọi provider | Hữu ích khi liệt kê lỗi timeout, 429, JSON sai và lệch ID/order | Có thể mặc định tin output đã qua schema là “đúng” | Xem output LLM vẫn là untrusted input; policy, provenance và renderer do code xác định |
| Evaluation | Gợi ý câu test đối nghịch và biến thể ngôn ngữ | Mở rộng golden set sang injection, mixed intent và conflict | Một số test ban đầu quá giống nhau hoặc kỳ vọng không khớp source mode | Rà lại expected outcome theo contract và giữ riêng kết quả offline/live |

> Với các quyết định về nguồn chính thức, metric và boundary, tôi không dùng output AI làm bằng chứng cuối; mọi kết luận đều phải đối chiếu với dữ liệu, code và kết quả chạy.

---

## 3. Reflection câu hỏi mở

**Reflection:**

```text
Khi bắt đầu, tôi nghĩ phần khó nhất sẽ là làm mô hình hiểu đúng câu hỏi logistics của học viên. Sau khi xem dữ liệu, tôi nhận ra rủi ro lớn hơn nằm ở việc một câu trả lời nghe hợp lý có thể bị hiểu nhầm là thông tin chính thức. Vì vậy tôi thay đổi cách tiếp cận từ “tăng độ thông minh của chatbot” sang “chứng minh được nguồn trước khi trả lời”. Evidence mining cũng dạy tôi rằng một con số tần suất chỉ cho biết chủ đề xuất hiện, chưa chứng minh bot đã phân loại đúng hoặc người dùng chắc chắn muốn sản phẩm này. Phần tôi đóng góp rõ nhất là nối evidence với spec, rồi biến các nguyên tắc trong spec thành schema, pipeline và phép đo cụ thể. Kết quả offline 48/48 ban đầu khiến tôi khá tự tin, nhưng kết quả live 21/48 cho thấy deterministic test không thể thay thế đánh giá model thật. Tôi thấy việc giữ lại kết quả xấu có giá trị hơn việc chỉ báo cáo một con số đẹp, vì nó chỉ thẳng vào vấn đề retrieval/source mode và sự khác biệt của classifier live. Tôi cũng học được rằng AI nên đảm nhiệm phần ngôn ngữ mơ hồ, còn quyết định có cost-of-error cao cần một boundary xác định và có thể kiểm thử. Nếu làm lại, tôi sẽ chốt sớm hơn ma trận test giữa offline, synthetic demo và live để golden set không bị hiểu sai theo từng môi trường. Tôi cũng sẽ dành thêm thời gian cho error analysis theo từng category thay vì chỉ nhìn pass rate tổng.
```

---

## 4. Tự kiểm cuối bài

- [x] Nêu rõ vai trò cá nhân và artifact có đóng góp trực tiếp
- [x] Có evidence định lượng từ bộ dữ liệu, không sao chép tin nhắn thô
- [x] Phân biệt rõ AI classification với deterministic decision
- [x] Nêu cả kết quả đạt và kết quả chưa đạt
- [x] Không xem synthetic fixture là thông tin khóa học thật
- [x] Có bài học, thay đổi nhận định và hướng cải thiện cụ thể

