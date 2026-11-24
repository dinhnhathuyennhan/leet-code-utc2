# Lỗi tồn đọng — Chấm Code v1.0.0-rc.1

Kết quả review production (https://utc2-chamcode.duckdns.org) ngày 18–19/11/2026 trên cả 3 role Admin / Teacher / Student, kèm kiểm thử chuyên sâu máy chấm Judge0 (564 đề, 6 ngôn ngữ). Danh sách sắp xếp theo mức độ nghiêm trọng, cột **Trạng thái** cập nhật theo code.

**Chú thích trạng thái**

| Ký hiệu | Ý nghĩa |
|---|---|
| ✅ develop | Đã sửa trên `develop` (PR #59, #61) |
| ✅ nhánh này | Đã sửa trên `bugfix/rc1-review-issues` |
| 🟡 một phần | Phần code đã xong; phần còn lại là việc hạ tầng/dữ liệu, ghi ở cột "Còn lại" |
| ↩️ đính chính | Không phải lỗi; giải thích ở cột "Còn lại" |
| ⏳ chưa sửa | Chưa xử lý trong nhánh này |

Mọi bản sửa đều **chưa có trên production**: cần phát hành `1.0.0-rc.2` rồi kiểm tra lại.

---

## 🔴 Mức cao

| # | Lỗi | Trạng thái | Bản sửa / Còn lại |
|---|---|---|---|
| 1 | API chi tiết bài nộp của sinh viên trả cả input/đáp án của test ẩn | ✅ develop | `student_service.py` chỉ trả test mẫu. Kết quả test ẩn giờ nằm trong `testcase_results` (không kèm dữ liệu) |
| 2 | Trạng thái Đúng/Sai từng test là giả (`index < passed_count`) | ✅ nhánh này | Cột mới `submission.testcase_results` (migration `f7a8b9c0d1e2`). API trả `status` thật cho từng test và trường `testcase_results`; trang Student/Teacher/Admin hiển thị theo dữ liệu thật. Bài nộp cũ chỉ hiện tổng `passed/total` |
| 3 | Judge0 chấm tuần tự: một bài lặp vô hạn trên 50 test chiếm máy chấm ~4 phút | 🟡 một phần | **Đã sửa:** chấm theo lô 10 test, dừng sau lô có test quá thời gian (test còn lại `skipped`) hoặc lỗi biên dịch; timeout tính theo số test. **Còn lại:** tăng `COUNT` worker và vCPU của EC2 Judge0 (docs/judge0-setup.md) |

## 🟠 Mức trung bình

| # | Lỗi | Trạng thái | Bản sửa / Còn lại |
|---|---|---|---|
| 4 | Nút kiểm tra Judge0 ở trang Cấu hình luôn báo HTTP 400 | ✅ develop | `judge0/client.py` gửi bài lấy token rồi hỏi lại kết quả |
| 5 | AI review luôn báo lỗi (local và production) | ⏳ chưa sửa | Không phải lỗi code: chưa có máy chủ Ollama (`qwen2.5-coder:7b`) ở local, và production chưa nối Ollama qua Tailscale (`OLLAMA_BASE_URL`). Nhóm sẽ cấu hình riêng sau PR này |
| 6 | Harness JS đổi thứ tự khoá số của object (HumanEval/95, test #36) | 🟡 một phần | Đây là hành vi của ngôn ngữ JavaScript. Đã ghi hướng dẫn soạn testcase trong docs/api-design-problem.md. **Còn lại:** giáo viên sửa hoặc bỏ testcase đó |
| 7 | Phiên bản ngôn ngữ cũ: Node 12, Python 3.8, C++ không có C++20 | 🟡 một phần | Đã ghi bảng phiên bản và cách nâng cấp trong docs/judge0-setup.md. **Còn lại:** nâng image Judge0 trên server |
| 8 | Cột MSSV hiển thị UUID | ✅ develop | Dùng `student_code` |
| 9 | Không xoá được bài tập, buổi học, lớp học phần | ✅ nhánh này | **Đã thêm** `DELETE /courses/{id}` và nút "Xoá lớp" (Admin/Teacher chủ lớp; chặn khi đã có bài nộp). **↩️ Đính chính:** nút "Xóa bài" vẫn hoạt động; lúc review nó dùng `window.confirm`, và hộp thoại này bị trình duyệt tự động đóng. Nút xoá buổi học có sẵn ở thẻ buổi học chưa mở, và backend chặn xoá buổi học đã có bài tập |
| 10 | Swagger/OpenAPI công khai | ✅ nhánh này | Biến `API_DOCS_ENABLED`; `false` trên production |
| 11 | Thiếu header bảo mật HTTP | ✅ nhánh này | `deploy/Caddyfile`: HSTS, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, bỏ `Server`. CSP chưa bật (Next.js cần nonce) |

## 🟡 Mức thấp

| # | Lỗi | Trạng thái | Bản sửa / Còn lại |
|---|---|---|---|
| 12 | Route chấm lại khai báo lệch | ✅ develop | `POST /submissions/{id}/regrade`, có nút "Chấm lại" khi bài bị `internal_error` |
| 13 | C++/Java chấm chậm (biên dịch lại cho mỗi test) | 🟡 một phần | Lỗi biên dịch giờ dừng sau lô đầu, không biên dịch lại 50 lần. **Còn lại:** harness chạy nhiều test trong một lần biên dịch (thay đổi kiến trúc chấm) |
| 14 | Đề STDIO khai báo Go nhưng không có code khởi tạo | ✅ nhánh này | **Loại bỏ hoàn toàn Go:** `SUPPORTED_LANGUAGES` chỉ gồm 5 ngôn ngữ; khoá lạ trong `JUDGE_LANGUAGES` bị bỏ qua kèm cảnh báo; xoá `go` khỏi `.env.example` và `deploy/.env.prod.example` |
| 15 | stderr lộ tên hàm nội bộ của harness (`_cham_main`) | ✅ nhánh này | Traceback Python chỉ giữ dòng thuộc code sinh viên. Thiếu hàm thì báo "Không tìm thấy hàm '...' trong bài làm." (Python và JS) |
| 16 | Tạo lớp hành chính trùng mã không hiện thông báo | ↩️ đính chính | Code đã hiện lỗi 409 bằng toast (`getErrorMessage`). Lúc review, toast biến mất trước khi được kiểm tra |
| 17 | Bấm EN ở trang Admin vẫn tiếng Việt | ✅ nhánh này | Admin/Teacher chưa có i18n (0/45 component). Nút VI/EN giờ chỉ hiện ở khu vực Student |
| 18 | Bộ test HumanEval/163 yếu | 🟡 một phần | Đã ghi hướng dẫn trong docs/api-design-problem.md. **Còn lại:** rà và bổ sung testcase cho đề |
| 19 | TLE hiển thị thời gian `0.001s` | ✅ nhánh này | Test quá thời gian hiển thị giới hạn wall time đã áp dụng |
| 20 | Đổi ngôn ngữ trong editor vẫn giữ code cũ | ✅ develop | Nạp code khởi tạo của ngôn ngữ mới, có cảnh báo |
| 21 | Văn bản nội bộ lọt ra giao diện | ✅ nhánh này | Thay 2 câu ở trang soạn buổi học |
| 22 | Output `[]` hiển thị rỗng; mức độ "easy" chưa dịch | ✅ nhánh này | Hiển thị JSON của giá trị; nhãn Dễ/Trung bình/Khó qua i18n |
| 23 | Header lộ công nghệ (`Server: uvicorn`, `X-Powered-By`) | ✅ nhánh này | `poweredByHeader: false`, `uvicorn --no-server-header`, Caddy bỏ `Server` |
| 24 | Đăng xuất gọi `POST /auth/logout` 2 lần | ✅ nhánh này | Gộp các lần gọi trùng khi đang đăng xuất |

---

## Việc còn lại ngoài code (cho người phụ trách hạ tầng)

1. Trên `/opt/chamcode/.env` của production: thêm `API_DOCS_ENABLED=false`, `GRADING_CHUNK_SIZE=10`; xoá `go` khỏi `JUDGE_LANGUAGES` (docs/deploy-ec2-cd.md mục 9.3).
2. Judge0: đặt `COUNT` worker theo số vCPU, cân nhắc nâng EC2 Judge0 và image ngôn ngữ (docs/judge0-setup.md).
3. AI review: dựng Ollama và nối với backend production qua Tailscale, đặt `OLLAMA_BASE_URL` (docs/deploy-ec2-cd.md).
4. Sau deploy `rc.2`: chạy `caddy validate`, kiểm tra header bằng `curl -sI`, và chạy lại kiểm thử chấm bài.

## Dữ liệu test còn lại trên production

Lớp `TESTRC1` (buổi học 1, bản sao đề #454) và bài nộp #1–#3 của SV 6451071082. Lớp này đã có bài nộp nên API xoá lớp mới vẫn chặn; cần xoá trong DB (đã có backup).
