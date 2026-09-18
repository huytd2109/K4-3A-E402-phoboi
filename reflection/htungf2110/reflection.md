# Individual Reflection — Trịnh Hoàng Tùng
## Thông tin cá nhân

- Họ và tên: Trịnh Hoàng Tùng
- Mã học viên: 2A202602937
- GitHub username: `htungf2110`
- Nhóm: Phoboi — lớp 3A, phòng E402, Track B1
- Vai trò: QA & Security Engineer
- Phần việc chính: Test suite, security module, golden set

---

## 1. Tôi đã tham gia vào phần nào?

| Hoạt động | Tôi đã làm gì? | Kết quả / ảnh hưởng tới nhóm |
|---|---|---|
| Threat modeling | Xác định các rủi ro chính: prompt injection, lộ PII/secret, nguồn giả, deadline không xác minh và model output sai schema | Nhóm chuyển safety từ một lời cam kết chung thành các invariant có thể kiểm thử |
| Security module | Xử lý giới hạn độ dài, loại mention, backstop cho yêu cầu dữ liệu cá nhân/injection và che PII/secret trong exception | Input và lỗi không được đi thẳng tới provider hoặc log mà chưa qua lớp bảo vệ |
| Deterministic boundary | Cùng nhóm khóa rule `LLM signal OR regex backstop`, trong đó personal-data luôn tối thiểu là `RESTRICT_PERSONAL` | Model không thể tự hạ mức bảo vệ; injection flag cũng không làm mất câu hỏi logistics hợp lệ trong cùng message |
| Test suite | Viết test cho model/schema, source, resolver, policy, Discord adapter, conversation, quota và fail-closed | Báo cáo validation cục bộ đạt 43 tests, không failure/error/skip |
| Golden set | Xây 48 ca P1 theo các category single-source, conflict, missing entity, no-source, personal, injection và mixed intent | Có chuẩn đo utility/safety trước khi demo và có cơ sở phân tích lỗi theo category |
| Hard-test stability | Chạy lặp nhóm test khó ba lần cho conflict, personal data, injection và mixed intent | Đạt 12/12 trong cả ba lượt, variance bằng 0 ở chế độ deterministic |
| Trung thực đánh giá | Giữ riêng báo cáo live 21/48 và offline 48/48; không dùng kết quả offline để tuyên bố model live đạt | Nhóm duy trì `unverified_deadline_released = 0` và trình bày đúng giới hạn của prototype |

**Dấu tay rõ nhất của tôi trong artifact cuối:**

```text
Dấu tay rõ nhất của tôi là bộ safety invariant được mã hóa thành security backstop, hard tests và golden set. Tôi tập trung kiểm tra rằng dù model sai, hệ thống vẫn không phát hành deadline chưa xác minh, không trả dữ liệu cá nhân và không nuốt lỗi provider.
```

---

## 2. Bảng dùng AI

| Giai đoạn | Tôi dùng AI để làm gì? | AI hữu ích ở đâu? | AI sai / hời hợt ở đâu? | Tôi sửa gì bằng nhận định của mình? |
|---|---|---|---|---|
| Threat modeling | Gợi ý attack surface và các biến thể prompt injection/PII | Mở rộng nhanh danh sách tình huống đối nghịch | Hay đề xuất block toàn bộ message khi thấy chuỗi injection | Giữ injection như một flag; phần logistics hợp lệ vẫn tiếp tục qua verified-or-handoff policy |
| Test design | Sinh biến thể câu hỏi và edge case cho từng outcome | Tăng độ đa dạng ngôn ngữ của golden set | Có test trùng ý, kỳ vọng mơ hồ hoặc phụ thuộc implementation hiện tại | Chuẩn hóa mỗi case theo contract và review thủ công expected outcome |
| Debug test | Hỗ trợ khoanh vùng mismatch giữa expected và actual | Rút ngắn thời gian tìm module liên quan | Đôi lúc đề xuất sửa test để khớp output thay vì sửa lỗi thật | Đối chiếu spec/source policy trước; chỉ đổi expectation khi contract thực sự thay đổi |
| Security review | Phản biện regex, exception sanitization và fail-closed paths | Hữu ích khi rà missing branch và dữ liệu nhạy cảm trong lỗi | Không chứng minh được regex bao phủ mọi cách diễn đạt | Dùng defense-in-depth: tín hiệu model OR regex, schema validation và deterministic minimum outcome |

> AI được dùng để mở rộng không gian test và hỗ trợ debug; quyết định pass/fail, invariant an toàn và expected outcome được xác nhận bằng spec cùng source policy.

---

## 3. Reflection câu hỏi mở

**Reflection:**

```text
Khi phụ trách QA và security, tôi học được rằng “bot không trả lời sai” khó đo hơn nhiều so với “bot có trả lời”. Một hệ thống có pass rate cao vẫn có thể không đạt nếu chỉ một lần phát hành deadline chưa xác minh hoặc để lộ dữ liệu cá nhân. Vì vậy tôi ưu tiên các safety counter bằng 0 trước khi tối ưu answer coverage. Tôi cũng thay đổi quan điểm về prompt injection: không phải cứ thấy một chuỗi đáng ngờ là từ chối toàn bộ message, vì người dùng có thể đang trích dẫn nó trong một câu hỏi hợp lệ. Rule OR giữa model signal và regex backstop giúp giữ mức bảo vệ tối thiểu, còn policy vẫn xử lý riêng intent logistics. Golden set 48 ca cho tôi thấy expected outcome phải bám vào contract, nếu không test rất dễ trở thành bản sao của implementation. Kết quả hard test 12/12 qua ba lượt chứng minh phần deterministic ổn định, nhưng không chứng minh Gemini live ổn định. Việc kết quả live chỉ đạt 21/48 là một cảnh báo quan trọng về khoảng cách giữa môi trường test và hành vi thật của model. Phần đóng góp rõ nhất của tôi là làm cho các giới hạn an toàn có thể tái hiện bằng test thay vì chỉ xuất hiện trong tài liệu. Nếu làm lại, tôi sẽ bổ sung sớm property-based test và fuzzing cho Unicode, mention, URL và các biến thể PII. Tôi cũng sẽ chuẩn bị quota cùng bộ live regression nhỏ từ đầu để phát hiện mismatch trước checkpoint đánh giá.
```

---

## 4. Tự kiểm cuối bài

- [x] Có vai trò cá nhân cụ thể trong QA và security
- [x] Nêu rõ invariant an toàn và cơ chế defense-in-depth
- [x] Có số liệu test tái hiện được
- [x] Không đánh đồng deterministic stability với model stability
- [x] Báo cáo trung thực cả kết quả live chưa đạt
- [x] Có bài học và đề xuất kiểm thử tiếp theo

