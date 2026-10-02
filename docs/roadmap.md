# Roadmap dự án "Chấm Code" (29/09/2026 → sẵn sàng demo 04/12, buffer tới giữa 12)

## Bối cảnh

Đây là kế hoạch chung của cả nhóm (5 người, chia 2 nhóm BE/FE) cho giai đoạn từ nay tới buổi demo. Phần nền **Auth + Quản lý tài khoản + Course** đã xong. Phần chấm code dùng **Judge0 self-host**, đã dựng và chạy thử thành công (xem [judge0-setup.md](judge0-setup.md)).

**Mục tiêu tiến độ:** hoàn thiện sản phẩm trước **04/12**, chừa phần **buffer từ 05/12** tới hạn demo (giữa tháng 12).

### Tình trạng hiện tại (tính trên nhánh `develop`, ngày 29/09)

**Backend: đã có**

- Auth: `POST /auth/login`, `/auth/change-password`, `/auth/logout`, `/auth/refresh-access-token` (`backend/app/routers/auth.py`)
- Tài khoản: `POST /teachers`, `/students`, `/students/import` (Excel), `/users/{id}/reset-password`
- Course: POST/GET list/GET detail/PATCH, enrollments POST/GET/DELETE (`backend/app/routers/course.py`)
- Global Exception Handler, CI (ruff + pytest + eslint + build), docker-compose (Postgres + migrate + pgAdmin)

**Backend: chưa có (mới có model trong `backend/models.py`)**

- `Class` (lớp hành chính): chưa có endpoint nào
- `Lesson`, `Problem`, `Testcase`, `Submission`: **lõi của sản phẩm chấm code, chưa có dòng logic nào**
- Admin xem danh sách tài khoản: chưa có
- Test: chưa có `test_auth_service.py` (login/refresh/logout/change-password chưa có test)

**Frontend**

- Trên `develop` mới có `/login` và `/change-password`. `getHomePath` (`frontend/src/lib/auth/redirect.ts`) redirect về `/admin-dashboard`, `/teacher-dashboard`, `/student-dashboard`, nhưng **3 trang này chưa tồn tại**, nên đăng nhập xong sẽ bị 404
- Có code trùng lặp: 2 HTTP client (`lib/axios.ts` và `lib/api/client.ts`), 2 token store (`lib/token-store.ts` và `lib/auth/token-store.ts`)

**Hạ tầng**

- ✅ Judge0 CE 1.13.1 đã chạy trên một máy chung của nhóm, chấm đúng cả 5 loại kết quả, chia sẻ cho thành viên qua Tailscale có token xác thực

**Git / quy trình**

- `feature/get-course` và `feature/login-ui` chưa merge vào `develop`. `login-ui` còn lẫn file rác (`frontend/tsc-errors.txt`, `frontend/tsc.txt`)
- `main` đang chậm hơn `develop` 73 commit

**Nợ kỹ thuật đã biết**: ngày của course đang là giờ VN naive, **phải chốt timezone trước khi làm deadline cho Lesson/Problem**.

> **Nhận định:** FE đang đi sau BE khá xa (BE có ~15 endpoint, FE mới gọi được auth), còn BE thì chưa đụng tới phần lõi (bài tập và chấm code). Hướng đi: **(1) cho FE theo kịp phần đã có**, song song với **(2) BE mở module Lesson/Problem**, rồi dồn lực vào **(3) Submission**.

---

## Cách rút ngắn tiến độ

1. **BE và FE chạy lệch pha, không chờ nhau.** BE luôn đi trước FE khoảng 7 ngày. Khi BE xong một phase thì chuyển ngay sang phase sau, còn FE làm phase đó dựa trên API contract đã có.
2. **Người lo hạ tầng chuyển sang hỗ trợ FE**, vì phần việc rủi ro nhất là Judge0 đã xong. FE thành 3 người, mỗi người phụ trách giao diện của 1 vai trò (Admin / Teacher / Student).
3. **Việc đơn giản được giao thời gian ngắn** (xem cột "Ước lượng"). Các API CRUD làm theo mẫu có sẵn trong `course_service.py`, và xuất Excel dùng lại thư viện đang dùng cho import.

## Lịch tổng quan

Số ngày tính theo lịch, gồm cả hai đầu mốc. Ví dụ 05/10 → 07/10 là 3 ngày.

| Phase                          | BE ×2                            | FE ×2 + 1 hỗ trợ        |
| ------------------------------ | -------------------------------- | ----------------------- |
| 0. Dọn nền                     | 29/09 → 02/10 (4 ngày), cả nhóm  | cùng BE                 |
| 1. FE theo kịp + Class/Account | 05/10 → 07/10 (3 ngày)           | 05/10 → 14/10 (10 ngày) |
| 2. Lesson / Problem / Testcase | 08/10 → 20/10 (13 ngày)          | 15/10 → 27/10 (13 ngày) |
| 3. Submission + chấm bài       | 21/10 → 03/11 (14 ngày)          | 28/10 → 10/11 (14 ngày) |
| 4. Theo dõi và thống kê        | 04/11 → 17/11 (14 ngày)          | 11/11 → 20/11 (10 ngày) |
| 5. Hoàn thiện và demo          | 23/11 → 04/12 (12 ngày), cả nhóm | cùng BE                 |
| Buffer                         | 05/12 → hạn demo                 | cùng BE                 |

Sau khi BE xong một phase và trước khi FE bắt đầu phase tiếp theo, BE dùng khoảng thời gian đó để viết docs cho phase kế tiếp, rồi sửa bug do FE báo lên.

---

## Nguyên tắc làm việc cho mọi phase

1. **Docs trước, code sau:** mỗi module mới bắt đầu bằng `docs/use-cases-<module>.md` và `docs/api-design-<module>.md` (giống auth/course). Docs phải xong **trước khi FE bắt đầu** phase đó, để FE mock theo API contract.
2. Mỗi PR nhỏ, tách từ `develop`, tuân thủ các quy tắc (AppError, whitelist role, scope dữ liệu, test đủ nhánh). PR nên được review trong vòng 1 ngày để không chặn người khác.
3. **Cuối mỗi phase:** merge `develop` vào `main` và demo nội bộ 15 phút.
4. Phân vai: **BE ×2, FE ×2, 1 người hạ tầng + QA** (từ Phase 1 chuyển sang hỗ trợ FE, và vẫn giữ Judge0 chạy ổn định).

---

## Phase 0: Dọn nền (29/09 → 02/10, 4 ngày)

| Việc                                                                                                                       | Ai      | Ước lượng |
| -------------------------------------------------------------------------------------------------------------------------- | ------- | --------- |
| Review rồi merge `feature/get-course`                                                                                      | BE      | 0.5 ngày  |
| Xoá `tsc-errors.txt`/`tsc.txt` và merge `feature/login-ui`                                                                 | FE      | 0.5 ngày  |
| Gộp HTTP client (giữ 1 trong `lib/axios.ts` / `lib/api/client.ts`) và token store (giữ 1)                                  | FE      | 1 ngày    |
| Viết `backend/tests/test_auth_service.py` (login sai/đúng, refresh hết hạn/bị revoke, token_version, logout)               | BE      | 1–2 ngày  |
| Sửa Excel import thiếu `class_id`                                                                                          | BE      | 0.5 ngày  |
| **Chốt quy ước timezone** (khuyến nghị: lưu UTC `timestamptz`, FE hiển thị giờ VN) và cập nhật `docs/api-design-course.md` | BE      | 1 ngày    |
| ~~Dựng Judge0~~ ✅ đã xong, xem [judge0-setup.md](judge0-setup.md)                                                         | Hạ tầng | —         |
| Các thành viên cần dùng Judge0 kết nối qua Tailscale (Phần B của hướng dẫn)                                                | Hạ tầng | 0.5 ngày  |
| Merge `develop` vào `main`                                                                                                 | Lead    | 0.5 ngày  |

**Xong phase khi:** develop sạch, CI xanh.

---

## Phase 1: FE theo kịp + Class/Account

**BE: 05/10 → 07/10 (3 ngày)**

| Việc                                                                                          | Ước lượng |
| --------------------------------------------------------------------------------------------- | --------- |
| `GET /users` (Admin, có lọc theo role/class, phân trang, scope theo vai trò), `GET /users/me` | 1–2 ngày  |
| CRUD `Class` (Admin), dùng cho import Excel và lọc sinh viên                                  | 1 ngày    |
| Sau đó chuyển sang viết docs cho Lesson/Problem/Testcase (Phase 2)                            | —         |

**FE: 05/10 → 14/10 (10 ngày, 3 người làm song song)**

- Chung (làm trước, 1–2 ngày): layout dashboard theo role + route guard (dựa trên `auth-context.tsx`, `redirect.ts`)
- **Người 1, Admin:** danh sách tài khoản, tạo GV/SV, import Excel (hiển thị kết quả từng dòng), reset mật khẩu (hiện mật khẩu tạm 1 lần)
- **Người 2, Teacher:** danh sách/chi tiết/tạo/sửa course, quản lý sinh viên trong lớp
- **Người 3, Student:** danh sách course mình đang học (phần này nhẹ, xong sớm thì hỗ trợ 2 người còn lại)

**Xong phase khi:** demo được toàn bộ luồng Admin → GV tạo lớp → thêm SV → SV đăng nhập thấy lớp, hoàn toàn trên UI.

---

## Phase 2: Lesson / Problem / Testcase

**BE: 08/10 → 20/10 (13 ngày, gồm cả viết docs)**

Router/service/schema/test mới, theo pattern `course_service.py`:

| Việc                                                                  | Ước lượng |
| --------------------------------------------------------------------- | --------- |
| Docs use-case + API design cho 3 module                               | 2 ngày    |
| `GET/POST/PATCH/DELETE /courses/{id}/lessons`                         | 2 ngày    |
| `GET/POST/PATCH/DELETE /lessons/{id}/problems`                        | 2–3 ngày  |
| `GET/POST/PATCH/DELETE /problems/{id}/testcases` (+ upload hàng loạt) | 2–3 ngày  |

Quy tắc cần có trong docs và test:

- Chỉ GV tạo course mới được sửa nội dung; SV phải đang enroll mới xem được
- **SV chỉ thấy testcase `is_sample = true`**; testcase ẩn không bao giờ lộ qua API của SV
- Problem chỉ hiện với SV trong khoảng `start_datetime`–`end_datetime` (dùng timezone đã chốt ở Phase 0)
- Các cột đếm (`total_number_assignment`, `total_number_testcase`...): cập nhật trong service, hoặc bỏ và tính bằng query, chốt khi viết docs
- Chọn giá trị mặc định cho giới hạn thời gian/bộ nhớ dựa trên số liệu đo trong [judge0-setup.md](judge0-setup.md) (Java cần nhiều RAM hơn hẳn)
- Migration Alembic kèm theo nếu schema thay đổi

**FE: 15/10 → 27/10 (13 ngày)**

- GV: trang soạn Lesson/Problem (editor markdown cho description), quản lý testcase
- SV: trang danh sách lesson → problem → xem đề + sample testcase

**Xong phase khi:** GV soạn được một bài hoàn chỉnh có testcase, SV xem được đề.

---

## Phase 3: Submission + chấm bài, lõi sản phẩm

Judge0 đã chạy sẵn, nên phase này chỉ còn phần tích hợp.

**BE: 21/10 → 03/11 (14 ngày)**

| Việc                                                                                                                                                                                                                                            | Ước lượng |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| `app/services/judge_client.py`: bọc API Judge0 (httpx), map ngôn ngữ (Python 71, C++ 54, Java 62, C 50), chuẩn hoá status. **Luôn dùng `base64_encoded=true`** (xem judge0-setup.md). Thêm `JUDGE0_URL`, `JUDGE0_AUTH_TOKEN` vào `.env.example` | 2–3 ngày  |
| `POST /problems/{id}/run`: chạy trên sample testcase, **không lưu**, dùng khi SV bấm "Run"                                                                                                                                                      | 1–2 ngày  |
| `POST /problems/{id}/submissions`: chạy toàn bộ testcase, lưu `Submission` (status `pending` rồi cập nhật kết quả); chấm bất đồng bộ bằng Judge0 batch + `BackgroundTasks`                                                                      | 3–4 ngày  |
| `GET /submissions/{id}` (FE poll), `GET /problems/{id}/submissions` (lịch sử của SV)                                                                                                                                                            | 1 ngày    |

- Quy tắc: chỉ SV đã enroll, chỉ trong thời hạn, giới hạn kích thước code/tần suất nộp; lỗi Judge0 trả về qua `AppError` (vd `JudgeUnavailableError`)
- Test: mock `judge_client`, không gọi Judge0 thật trong CI

**FE: 28/10 → 10/11 (14 ngày)**

- Trang làm bài: code editor (Monaco), chọn ngôn ngữ, nút Run/Submit, panel kết quả từng testcase, lịch sử nộp

**Xong phase khi:** SV nộp bài, nhận verdict đúng cho cả 5 loại kết quả.

---

## Phase 4: Theo dõi và thống kê

**BE: 04/11 → 17/11 (14 ngày) · FE: 11/11 → 20/11 (10 ngày)**

| Việc                                                                                              | Ước lượng                 |
| ------------------------------------------------------------------------------------------------- | ------------------------- |
| GV: xem submission theo bài/theo SV, xem code SV nộp                                              | 2 ngày (BE) + 2 ngày (FE) |
| Tiến độ theo lesson (`total_number_student_finished`), SV: trạng thái từng bài (chưa làm / đã AC) | 2 ngày (BE) + 2 ngày (FE) |
| **Xuất bảng điểm Excel** (dùng lại thư viện của phần import)                                      | 1–2 ngày (BE)             |
| Dashboard tổng quan cho từng role                                                                 | 2 ngày (BE) + 3 ngày (FE) |

---

## Phase 5: Hoàn thiện và demo (23/11 → 04/12, 12 ngày)

- E2E test các luồng chính (Playwright), rà soát bảo mật toàn bộ phần phân quyền
- Seed data demo (course, lesson, problem, testcase thật)
- Đóng gói docker-compose cho full stack (backend + frontend + DB), kèm hướng dẫn trỏ tới Judge0
- Hoàn thiện docs và báo cáo đồ án, merge `main`

**Buffer (05/12 → hạn demo):** dành cho việc trễ, sửa bug phát sinh, tập demo.

**Cắt scope nếu trễ:** bỏ xuất Excel, bỏ dashboard thống kê và chỉ giữ Phase 0–3 cùng danh sách submission cơ bản.

---

## Việc cần làm ngay (29/09 → 02/10)

1. Review và merge `feature/get-course`
2. Dọn file rác, merge `feature/login-ui`
3. Chốt timezone, viết `test_auth_service.py`
4. Họp 30 phút: phân người cho từng phase theo bảng trên, **chốt ai là Người 1/2/3 bên FE**

## Cách kiểm tra

- Mỗi phase có tiêu chí "Xong phase khi" ở trên, kiểm bằng demo trên UI
- CI (`.github/workflows/ci.yaml`) phải xanh: `ruff check .`, `pytest`, `npm run lint`, `npm run build`
- Phase 3 kiểm thêm bằng tay với Judge0 dùng chung của nhóm
