# Individual Reflection — Trịnh Đức Huy
## Thông tin cá nhân

- Họ và tên: Trịnh Đức Huy
- Mã học viên: 2A202602865
- GitHub username: `huytd2109`
- Nhóm: Phoboi — lớp 3A, phòng E402, Track B1
- Vai trò: Lead Team & Backend Engineer
- Phần việc chính: Source repository, conflict resolver

---

## 1. Tôi đã tham gia vào phần nào?

| Hoạt động | Tôi đã làm gì? | Kết quả / ảnh hưởng tới nhóm |
|---|---|---|
| Điều phối nhóm | Chốt phân công, giữ repo chung, theo dõi các checkpoint và kết nối phần AI, backend, QA, UI, tài liệu | Các artifact được ghép thành một luồng demo thống nhất thay vì bốn phần rời rạc |
| Source repository | Xây contract cho nguồn gồm role, thời điểm, task/alias, cohort/class, deadline, URL, trạng thái và provenance | Hệ thống có tiêu chí máy kiểm tra được để phân biệt nguồn hợp lệ, candidate và fixture demo |
| Source mode | Tách `dataset`, `synthetic_demo` và môi trường test/demo/production | Dữ liệu giả lập không thể bị dùng nhầm trong production; UI và câu trả lời demo luôn có nhãn |
| Conflict resolver | Cài luật loại nguồn revoked/superseded, xử lý quan hệ `supersedes`, thiếu scope và deadline xung đột | Hệ thống không chọn bừa bản ghi mới nhất; conflict chưa giải quyết được chuyển sang `HANDOFF_CONFLICT` |
| Backend | Kết nối analyzer, policy, source store, API/CLI và Discord runtime | Tạo được đường chạy end-to-end từ câu hỏi đến answer, clarify, restrict hoặc handoff |
| Reliability | Bổ sung retry có giới hạn cho timeout/429/5xx, fail-closed cho lỗi auth/schema/config và cooldown chống handoff trùng | Backend không che giấu lỗi provider và không spam TA khi cùng một vấn đề lặp lại |
| Validation | Hỗ trợ thu thập feedback người dùng và đóng gói báo cáo chạy cục bộ | Nhóm có bằng chứng pytest/build/typecheck và phản hồi usability bên cạnh demo trực quan |

**Dấu tay rõ nhất của tôi trong artifact cuối:**

```text
Dấu tay rõ nhất của tôi là source repository và conflict resolver ở phía backend. Tôi chịu trách nhiệm bảo đảm một deadline chỉ được trả khi nguồn vượt qua contract, còn trường hợp thiếu scope, nguồn bị thu hồi hoặc xung đột đều đi theo nhánh an toàn.
```

---

## 2. Bảng dùng AI

| Giai đoạn | Tôi dùng AI để làm gì? | AI hữu ích ở đâu? | AI sai / hời hợt ở đâu? | Tôi sửa gì bằng nhận định của mình? |
|---|---|---|---|---|
| Thiết kế backend | Gợi ý cách chia module và liệt kê edge case của source/resolver | Giúp rà nhanh các nhánh revoked, superseded, missing scope và conflict | Thường đề xuất “chọn nguồn mới nhất” như một mặc định tiện lợi | Bỏ heuristic timestamp-only và yêu cầu quan hệ supersession hoặc handoff |
| Source contract | Phản biện các trường bắt buộc để dựng provenance | Hữu ích khi kiểm tra thiếu URL, Discord IDs, timezone và class scope | Có thể coi một chuỗi URL-looking là nguồn đã xác minh | Yêu cầu URL trực tiếp hoặc đủ guild/channel/message ID và validate bằng code |
| Error handling | Gợi ý các nhóm lỗi provider và chiến lược retry | Bao quát timeout, rate limit và server error | Dễ retry cả lỗi auth/config, làm chậm mà không thể tự hồi phục | Chỉ retry lỗi tạm thời; auth, permission, schema và config fail ngay |
| Điều phối | Hỗ trợ tóm tắt issue và checklist tích hợp giữa các phần | Giúp giảm thời gian tổng hợp khi deadline gần | Tóm tắt đôi khi bỏ mất giới hạn hoặc nhầm trạng thái “đã làm” | Đối chiếu với commit, test report và file thật trước khi chốt tiến độ |

> AI hỗ trợ rà soát và gợi ý; các luật trust, conflict, retry và quyết định release đều được chốt bằng source policy cùng kiểm thử của nhóm.

---

## 3. Reflection câu hỏi mở

**Reflection:**

```text
Vai trò lead khiến tôi phải nhìn sản phẩm như một chuỗi phụ thuộc thay vì chỉ hoàn thành module backend của mình. Tôi nhận ra source repository không đơn giản là nơi lưu deadline, mà là lớp quyết định thông tin nào có đủ quyền để đi tới người dùng. Ban đầu, cách chọn bản ghi mới nhất có vẻ hợp lý và dễ triển khai, nhưng nó không xử lý được trường hợp hai thông báo cùng hiệu lực hoặc một nguồn không thực sự thay thế nguồn kia. Sau khi nhóm challenge, tôi chuyển sang yêu cầu quan hệ supersedes rõ ràng và handoff khi conflict chưa giải quyết được. Quyết định đó làm bot trả lời ít hơn trong một số ca, nhưng đổi lại không tự đoán ở tình huống có cost-of-error cao. Tôi cũng học được rằng dẫn dắt nhóm trong hackathon không phải tự làm nhiều nhất, mà là giữ cho spec, code, test và demo cùng nói một sự thật. Khi kết quả live thấp hơn offline, việc quan trọng là không sửa lời kể để che khoảng trống mà phải phân biệt rõ từng chế độ chạy. Phần tôi đóng góp rõ nhất là biến các boundary về nguồn và xung đột thành luật backend có thể kiểm thử. Nếu làm lại, tôi sẽ thiết lập integration contract và owner cho từng interface ngay từ checkpoint đầu để giảm thời gian ghép module. Tôi cũng sẽ tổ chức một vòng dry-run end-to-end sớm hơn, gồm cả lỗi quota và Discord handoff, trước khi tập trung vào phần trình bày.
```

---

## 4. Tự kiểm cuối bài

- [x] Nêu rõ trách nhiệm lead và backend
- [x] Mô tả source contract và conflict resolver bằng tình huống cụ thể
- [x] Giải thích vì sao không chọn nguồn mới nhất một cách máy móc
- [x] Nêu cơ chế fail-closed, retry và handoff dedup
- [x] Phân biệt kết quả offline, live và synthetic demo
- [x] Có bài học, thay đổi quyết định và kế hoạch cải thiện

