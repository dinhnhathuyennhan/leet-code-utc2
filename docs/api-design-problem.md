# Thiết kế API — Quản lý bài tập (Problem)

> Tài liệu này đặc tả hướng đi thiết kế API cho module **Problem** (bài tập lập trình thuộc một bài học). Phase 2 của [roadmap.md](roadmap.md) sẽ implement các endpoint này. Cấu trúc response lỗi và quy ước chung lấy theo [api-design-course.md](api-design-course.md), [api-design-lesson.md](api-design-lesson.md) và [global-exception-handler.md](global-exception-handler.md).

## Quy ước chung

### Phân quyền truy cập (scope theo vai trò)

| Hành động | Admin | Teacher (chủ lớp) | Teacher (không chủ lớp) | Student (enrolled, trong thời gian mở) | Student (ngoài thời gian / chưa enroll) |
|---|---|---|---|---|---|
| `GET /lessons/{lesson_id}/problems` (list) | ✅ | ✅ (problem thuộc lớp mình tạo) | ✅ (problem thuộc lớp mình tạo) | ✅ chỉ thấy problem trong `[start_datetime, end_datetime]` | ❌ 403 |
| `GET /problems/{problem_id}` (chi tiết) | ✅ | ✅ (problem thuộc lớp mình tạo) | ✅ (problem thuộc lớp mình tạo) | ✅ nếu trong thời gian mở | ❌ 403 |
| `POST /lessons/{lesson_id}/problems` (tạo) | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 |
| `PATCH /problems/{problem_id}` (sửa) | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 |
| `DELETE /problems/{problem_id}` (xoá) | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 |

> **Quy ước "chủ lớp"** = `Course.created_by == current_user.user_id` (xem [api-design-course.md](api-design-course.md), [api-design-lesson.md](api-design-lesson.md)). Logic kiểm tra nằm trong `service`, không phải `require_role` ở router.

### Quy ước thời gian (`start_datetime`, `end_datetime` của Problem)

- Problem dùng kiểu `datetime` đầy đủ (khác với Lesson dùng `date`).
- Áp dụng quy ước thời gian đã chốt ở [api-design-course.md § Quy ước thời gian](api-design-course.md): **client gửi giờ Việt Nam, không kèm offset** (vd `"2026-10-15T08:00:00"`). Trước khi deadline chấm bài hoạt động (Phase 3), BE sẽ chuyển sang `timestamptz` (Phase 0 của roadmap) — khi đó tài liệu này sẽ được cập nhật.
- `start_datetime` phải **trước** `end_datetime` (`start_datetime < end_datetime`).
- `start_datetime`–`end_datetime` phải **nằm trong khoảng** `Lesson.start_date`–`Lesson.end_date` của lesson cha (mở rộng biên 1 ngày cho phép: `start_datetime` có thể bằng `Lesson.start_date` 00:00, `end_datetime` có thể bằng `Lesson.end_date` 23:59). Nếu nằm ngoài → 422 `PROBLEM_OUT_OF_LESSON_RANGE`.
- **Quy tắc "hiện với sinh viên"**: Problem chỉ hiện với Student khi thời điểm hiện tại (server) nằm trong `[start_datetime, end_datetime]`. Ngoài khoảng này → coi như "chưa mở" (trước `start_datetime`) hoặc "đã đóng" (sau `end_datetime`).

### Quy tắc giá trị cho `time_limit_seconds`, `constraints`, `level`, `hint`, `complexity`, `report`

| Field | Ràng buộc | Ghi chú |
|---|---|---|
| `time_limit_seconds` | int, 1 ≤ x ≤ 15 (**đề xuất**, chốt khi implement) | dựa trên số liệu đo trong [judge0-setup.md](judge0-setup.md): TLE ~1s cho C++ vòng lặp vô hạn. Đặt max 15s để chừa margin cho ngôn ngữ chậm (Java, Python). Roadmap chưa chốt con số này — Phase 2 sẽ chốt dựa trên số liệu thực đo thêm. |
| `start_format_code` | string, tối đa 50.000 ký tự | code mẫu ban đầu cho sinh viên (template). Có thể rỗng `""` |
| `description` | string markdown, tối đa 20.000 ký tự | nội dung đề bài, hiển thị qua markdown editor ở FE (xem [roadmap.md § Phase 2 FE](roadmap.md)) |
| `constraints` | string markdown, tối đa 5.000 ký tự | ràng buộc đề bài, FE hiển thị riêng khối |
| `level` | enum string: `"easy"` \| `"medium"` \| `"hard"` | dùng để lọc/sắp xếp ở Phase 4. Mặc định `"medium"` khi không truyền |
| `hint` | string markdown \| null, tối đa 5.000 ký tự | tuỳ chọn. Nếu có → hiển thị cho student; nếu null → ẩn nút "Xem gợi ý" |
| `complexity` | string \| null, tối đa 200 ký tự | độ phức tạp kỳ vọng (vd: `"O(n log n)"`). Tuỳ chọn |
| `report` | string markdown \| null, tối đa 5.000 ký tự | báo cáo sau khi chấm (Phase 3 — Submission). **Phase 2 endpoint này bỏ qua field này**, Phase 3 mới sử dụng |
| `total_number_testcase` | int | luôn = 0 lúc tạo, **chỉ service cập nhật** khi thêm/xoá Testcase (xem [api-design-testcase.md](api-design-testcase.md)) |

### Quy tắc xoá có cascade

- `DELETE /problems/{problem_id}` xoá problem và **toàn bộ Testcase + Submission con** (cascade qua FK). Mặc định chặn khi còn Testcase con, có flag `?force=true` để cascade (xem § DELETE).
- **Không cho phép restore** sau khi xoá.

### Cột đếm & cập nhật

| Cột | Cập nhật khi | Ghi chú |
|---|---|---|
| `Problem.total_number_testcase` | Tạo/xoá Testcase con | Tăng khi thêm Testcase, giảm khi xoá. Cập nhật trong `testcase_service` (xem [api-design-testcase.md](api-design-testcase.md)) |
| `Lesson.total_number_assignment` | Tạo/xoá Problem con | Tăng khi thêm Problem, giảm khi xoá. Cập nhật trong `problem_service` |
| `Problem.report` | Sau khi chấm bài (Phase 3) | Phase 3 sẽ chốt cơ chế (Submission service viết, Problem service chỉ đọc). API Problem ở Phase 2 **không nhận** field `report` từ client |

### Quy tắc response

- Response **luôn dùng `response_model`** đã khai báo.
- Các field lạ trong request body `POST`/`PATCH` sẽ bị Pydantic bỏ qua.
- Khi Student xem problem, response **không bao gồm** testcase ẩn (`is_sample = false`) — xem [api-design-testcase.md § Quy tắc ẩn testcase](api-design-testcase.md).

### Xử lý lỗi

- Mọi exception nghiệp vụ kế thừa `AppError` (xem [global-exception-handler.md](global-exception-handler.md)). Router không viết `try/except`.
- Lỗi dùng chung (xem [api-design-lesson.md](api-design-lesson.md)):
  - `LessonNotFoundError` (404 `LESSON_NOT_FOUND`)
  - `CourseNotFoundError` (404 `COURSE_NOT_FOUND`)
  - `ForbiddenError` (403 `FORBIDDEN`, message cụ thể theo ngữ cảnh)
- Lỗi riêng của domain `problem` (đặt trong `backend/app/services/problem_service.py`):
  - `ProblemNotFoundError` (404 `PROBLEM_NOT_FOUND`, message `"Không tìm thấy bài tập"`)
  - `ProblemNotOpenError` (403 `PROBLEM_NOT_OPEN`, message `"Bài tập hiện chưa mở hoặc đã đóng"`) — dùng cho Student truy cập ngoài khoảng `[start_datetime, end_datetime]`
  - `ProblemOutOfLessonRangeError` (422 `PROBLEM_OUT_OF_LESSON_RANGE`, message `"Thời gian bài tập phải nằm trong khoảng của bài học"`)
  - `ProblemInvalidTimeLimitError` (422 `INVALID_TIME_LIMIT`, message `"time_limit_seconds phải nằm trong khoảng 1-15"`)
  - `ProblemInvalidLevelError` (422 `INVALID_LEVEL`, message `"level phải là easy, medium hoặc hard"`)
  - `ProblemNotEmptyError` (409 `PROBLEM_NOT_EMPTY`, message `"Không thể xoá bài tập đang có testcase. Hãy xoá hết testcase trước"`) — dùng cho `DELETE` không `force`

---

## POST /lessons/{lesson_id}/problems — Tạo bài tập

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| title | string | có | tối đa 255 ký tự, tự trim 2 đầu |
| description | string | có | markdown, tối đa 20.000 ký tự. Có thể rỗng `""` |
| time_limit_seconds | int | có | 1 ≤ x ≤ 15 (đề xuất, chốt khi implement) |
| start_format_code | string | có | tối đa 50.000 ký tự. Có thể rỗng `""` |
| constraints | string | có | tối đa 5.000 ký tự. Có thể rỗng `""` |
| level | string | không | enum `"easy"` \| `"medium"` \| `"hard"`. Mặc định `"medium"` |
| hint | string \| null | không | tối đa 5.000 ký tự. Mặc định `null` |
| complexity | string \| null | không | tối đa 200 ký tự. Mặc định `null` |
| start_datetime | datetime | có | xem [Quy ước thời gian](#quy-ước-thời-gian-start_datetime-end_datetime-của-problem) |
| end_datetime | datetime | có | phải > `start_datetime`, nằm trong khoảng của lesson |

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| problem_id | int | |
| lesson_id | int | |
| title | string | |
| description | string | |
| time_limit_seconds | int | |
| start_format_code | string | |
| constraints | string | |
| level | string | |
| hint | string \| null | |
| complexity | string \| null | |
| start_datetime | datetime | |
| end_datetime | datetime | |
| total_number_testcase | int | luôn = 0 lúc tạo |
| report | string \| null | luôn = null ở Phase 2 |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Thiếu field, field bắt buộc = `null`, sai kiểu dữ liệu, vượt quá độ dài tối đa, hoặc `title` / `description` / `start_format_code` / `constraints` là chuỗi rỗng `""` (chỉ `title` là bắt buộc không rỗng) | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 422 | `title` chỉ chứa khoảng trắng, vd `"   "` | `{"error_code": "EMPTY_FIELD", "message": "title không được để trống"}` |
| 422 | `time_limit_seconds` ngoài khoảng 1-15 | `{"error_code": "INVALID_TIME_LIMIT", "message": "time_limit_seconds phải nằm trong khoảng 1-15"}` |
| 422 | `level` không thuộc enum | `{"error_code": "INVALID_LEVEL", "message": "level phải là easy, medium hoặc hard"}` |
| 422 | `start_datetime >= end_datetime` | `{"error_code": "INVALID_FORMAT", "message": "start_datetime phải trước end_datetime"}` |
| 422 | `start_datetime`–`end_datetime` nằm ngoài khoảng của lesson | `{"error_code": "PROBLEM_OUT_OF_LESSON_RANGE", "message": "Thời gian bài tập phải nằm trong khoảng của bài học"}` |
| 404 | `lesson_id` không tồn tại | `{"error_code": "LESSON_NOT_FOUND", "message": "Không tìm thấy bài học"}` |
| 403 | Người gọi không phải Admin, hoặc là Teacher nhưng không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thêm bài tập vào bài học này"}` |

**Quy tắc nghiệp vụ**

- `total_number_testcase` luôn khởi tạo = 0, không nhận từ client.
- `report` luôn = null lúc tạo, không nhận từ client.
- `title` được tự động trim khoảng trắng hai đầu trước khi lưu.
- Sau khi tạo thành công, **tăng `Lesson.total_number_assignment` lên 1** (cùng transaction với insert Problem — nếu lỗi giữa chừng thì rollback toàn bộ, không tăng nửa vời).
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

---

## GET /lessons/{lesson_id}/problems — Danh sách bài tập trong bài học

**Query parameters**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| include_inactive | bool | không | mặc định `false`. Khi `false`: Student chỉ thấy problem có `start_datetime <= now <= end_datetime`. Khi `true`: thấy tất cả. Admin/Teacher luôn thấy tất cả bất kể flag |
| level | string | không | lọc theo level (`"easy"` \| `"medium"` \| `"hard"`). Bỏ trống = tất cả |

**Response 200 OK**: mảng object giống response của `POST /lessons/{lesson_id}/problems`, sắp xếp theo `start_datetime` tăng dần. Không có problem nào → `[]`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `lesson_id` không tồn tại | `{"error_code": "LESSON_NOT_FOUND", "message": "Không tìm thấy bài học"}` |
| 403 | Student chưa enroll vào course chứa lesson, hoặc lesson đã đóng cửa và `include_inactive=false` | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem bài học này"}` |
| 403 | Teacher không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem bài học này"}` |
| 403 | Role không thuộc Admin/Teacher/Student | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 422 | `level` không thuộc enum | `{"error_code": "INVALID_LEVEL", "message": "level phải là easy, medium hoặc hard"}` |

**Quy tắc nghiệp vụ**

- Kết quả tự động scope theo vai trò người gọi (xem bảng § Phân quyền):
  - **Admin**: thấy tất cả problem trong lesson.
  - **Teacher chủ lớp**: thấy tất cả problem.
  - **Teacher không phải chủ lớp**: 403.
  - **Student đã enroll**: thấy problem trong khoảng thời gian mở (mặc định). Có thể bật `include_inactive=true` để xem tất cả.
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi truy cập theo vai trò.

---

## GET /problems/{problem_id} — Chi tiết bài tập

**Response 200 OK**: object giống response của `POST /lessons/{lesson_id}/problems`. Ngoài ra (nếu triển khai ở Phase 2 — khuyến nghị **bổ sung luôn** để FE render trang làm bài):

| Field | Kiểu | Ghi chú |
|---|---|---|
| sample_testcases | array of object | chỉ các Testcase có `is_sample = true`. Mỗi phần tử: `testcase_id`, `input`, `expected_output`, `input_type`, `expected_output_type`. **Không bao giờ trả testcase ẩn** (`is_sample = false`) cho bất kỳ role nào qua endpoint này — xem [api-design-testcase.md](api-design-testcase.md) |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `problem_id` không tồn tại | `{"error_code": "PROBLEM_NOT_FOUND", "message": "Không tìm thấy bài tập"}` |
| 403 | Student chưa enroll vào course chứa problem, hoặc ngoài khoảng `[start_datetime, end_datetime]` | `{"error_code": "PROBLEM_NOT_OPEN", "message": "Bài tập hiện chưa mở hoặc đã đóng"}` |
| 403 | Teacher không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem bài tập này"}` |
| 403 | Role không thuộc Admin/Teacher/Student | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Áp dụng cùng quy tắc scope và "hiện với sinh viên" như `GET /lessons/{lesson_id}/problems`.
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi truy cập theo vai trò.

---

## PATCH /problems/{problem_id} — Cập nhật bài tập

**Request body** (tất cả optional, chỉ cập nhật field được truyền)

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| title | string | không | tối đa 255 ký tự, tự trim 2 đầu |
| description | string | không | tối đa 20.000 ký tự |
| time_limit_seconds | int | không | 1 ≤ x ≤ 15 (đề xuất, chốt khi implement) |
| start_format_code | string | không | tối đa 50.000 ký tự |
| constraints | string | không | tối đa 5.000 ký tự |
| level | string | không | enum `"easy"` \| `"medium"` \| `"hard"` |
| hint | string \| null | không | tối đa 5.000 ký tự. Gửi `null` = xoá hint hiện có; gửi `""` → 422 `EMPTY_FIELD` |
| complexity | string \| null | không | tối đa 200 ký tự. Gửi `null` = xoá |
| start_datetime | datetime | không | nếu đổi, phải < `end_datetime` hiện tại hoặc mới |
| end_datetime | datetime | không | nếu đổi, phải > `start_datetime` hiện tại hoặc mới, và nằm trong khoảng của lesson |

Field không gửi → giữ nguyên. Field gửi = `null` → **xoá** (chỉ áp dụng cho `hint`, `complexity`; các field khác nếu gửi `null` sẽ bị bỏ qua, **không xoá**). Body rỗng `{}` hoặc toàn `null` → không cập nhật gì, trả 200 với dữ liệu hiện tại.

**Response 200 OK**: object giống response của `POST /lessons/{lesson_id}/problems`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `problem_id` không tồn tại | `{"error_code": "PROBLEM_NOT_FOUND", "message": "Không tìm thấy bài tập"}` |
| 403 | Người gọi không phải Admin, hoặc là Teacher nhưng không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền chỉnh sửa bài tập này"}` |
| 422 | Sai kiểu dữ liệu, vượt quá độ dài tối đa | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 422 | `title` được truyền nhưng rỗng hoặc chỉ chứa khoảng trắng | `{"error_code": "EMPTY_FIELD", "message": "title không được để trống"}` |
| 422 | `time_limit_seconds` ngoài khoảng 1-15 | `{"error_code": "INVALID_TIME_LIMIT", "message": "..."}` |
| 422 | `level` không thuộc enum | `{"error_code": "INVALID_LEVEL", "message": "..."}` |
| 422 | `hint` được truyền nhưng rỗng `""` | `{"error_code": "EMPTY_FIELD", "message": "hint không được để trống (gửi null để xoá)"}` |
| 422 | `start_datetime >= end_datetime` (so với giá trị hiện tại nếu chỉ gửi 1 trong 2) | `{"error_code": "INVALID_FORMAT", "message": "start_datetime phải trước end_datetime"}` |
| 422 | `end_datetime` mới nằm ngoài khoảng của lesson | `{"error_code": "PROBLEM_OUT_OF_LESSON_RANGE", "message": "..."}` |

**Quy tắc nghiệp vụ**

- Không cho sửa `problem_id`, `lesson_id`, `total_number_testcase`, `report` qua endpoint này (field lạ bị bỏ qua).
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

---

## DELETE /problems/{problem_id} — Xoá bài tập

**Query parameters**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| force | bool | không | mặc định `false`. Khi `false`: nếu còn Testcase con → 409 `PROBLEM_NOT_EMPTY`. Khi `true`: cascade xoá toàn bộ Testcase + Submission con (xem § Quy tắc xoá có cascade) |

**Response**: `204 No Content`

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `problem_id` không tồn tại | `{"error_code": "PROBLEM_NOT_FOUND", "message": "Không tìm thấy bài tập"}` |
| 403 | Người gọi không phải Admin, hoặc là Teacher nhưng không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xoá bài tập này"}` |
| 409 | `force=false` và problem còn Testcase con | `{"error_code": "PROBLEM_NOT_EMPTY", "message": "Không thể xoá bài tập đang có testcase. Hãy xoá hết testcase trước"}` |

**Quy tắc nghiệp vụ**

- Khi xoá thành công, **giảm `Lesson.total_number_assignment` đi 1** (cùng transaction với xoá Problem).
- Khi xoá cascade (`force=true`): xoá Problem → cascade xoá Testcase → cascade xoá Submission. Mọi thao tác phải nằm trong **một transaction**; nếu lỗi giữa chừng thì rollback toàn bộ.
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

---

## Mở rộng trong tương lai (Phase 4 trở đi, **không implement ở Phase 2/3**)

- `GET /problems/{id}/leaderboard` — bảng xếp hạng SV theo số testcase pass / thời gian nộp (Phase 4).
- `PATCH /problems/{id}/report` — service nội bộ cập nhật sau khi chấm (do Submission service gọi, **không public**).
- `GET /problems/{id}/submissions?student_id=...` — lọc lịch sử nộp theo SV cụ thể (dành cho GV xem, Phase 4). Phase 3 SV chỉ xem của chính mình.
- `GET /problems/{id}/statistics` — số SV đã AC, trung bình passed_count, v.v. (Phase 4).

---

## Phase 3 — Submission & chấm bài

Phase 3 thêm 2 endpoint public cho Student (Run/Submit) và 1 endpoint xem lịch sử. Judge0 được bọc trong `app/services/judge_client.py`, **luôn dùng `base64_encoded=true`** (xem [judge0-setup.md](judge0-setup.md) § Lưu ý bảo mật). `language_id` mapping (Python 71, C++ 54, Java 62, C 50) nằm trong `judge_client.py`, **không để lộ ra API**.

### Ngôn ngữ hỗ trợ (chốt theo Judge0 CE 1.13.1, xem [judge0-setup.md § Bước 5](judge0-setup.md))

| Tên hiển thị (API) | `language_id` Judge0 | Ghi chú |
|---|---|---|
| `python` | 71 | Python 3.8.1 |
| `cpp` | 54 | C++ (GCC 9.2.0) |
| `c` | 50 | C (GCC 9.2.0) |
| `java` | 62 | Java (OpenJDK 13) |

Client chỉ cần gửi `language: "python" | "cpp" | "c" | "java"` (enum string). Service tự map sang `language_id` Judge0. **Cập nhật mapping** khi Judge0 được nâng cấp — chốt trong `judge_client.py`, không để lộ.

### Giới hạn thời gian / bộ nhớ (lấy từ số liệu đo trong [judge0-setup.md § Bước 6](judge0-setup.md))

| Field | Giá trị | Ghi chú |
|---|---|---|
| `time_limit_seconds` | **1 ≤ x ≤ 15** (đề xuất, chốt khi implement Phase 2) | Map sang `cpu_time_limit` của Judge0 (đơn vị giây). C++/C/Python 1-10s là đủ; Java cần tới 15s |
| `memory_limit_kb` | **128000 KB (~128 MB)** mặc định cho C/C++/Python, **256000 KB (~256 MB)** cho Java (đề xuất, chốt khi implement Phase 2) | Map sang `memory_limit` của Judge0 (đơn vị KB). Java tốn RAM hơn hẳn do JVM (đo thực tế ~50 MB cho bài AC đơn giản, nhưng cần margin cho test lớn) |

> **Hiện tại (Phase 2)**: Problem chỉ lưu `time_limit_seconds` (model `Problem` hiện không có `memory_limit_kb`). **Cần thêm cột `memory_limit_kb` trong migration Alembic trước Phase 3**, mặc định 128000 (C/C++/Python) hoặc 256000 (Java) tuỳ `language` — tốt nhất để client truyền lên (validate theo language). Chi tiết chốt khi viết `judge_client.py`.

### POST /problems/{problem_id}/run — Chạy thử (không lưu)

Dùng khi SV bấm nút "Run" để test code trên **sample testcase** (`is_sample = true`), **không tạo Submission**, **không ảnh hưởng** `total_number_student_finished`.

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| language | string | có | enum: `"python"` \| `"cpp"` \| `"c"` \| `"java"` |
| source_code | string | có | code nguồn, tối đa **50.000** ký tự (UTF-8, server tự base64-encode khi gọi Judge0) |
| stdin_override | string \| null | không | nếu có → dùng làm stdin cho **tất cả** sample testcase (thay vì stdin của từng testcase). Tối đa 10.000 ký tự. Hữu ích khi SV muốn chạy với input khác testcase mẫu |

**Response 200 OK** — trả kết quả từng sample testcase, **đồng bộ** (đợi Judge0 xong)

| Field | Kiểu | Ghi chú |
|---|---|---|
| results | array of object | mỗi phần tử: `testcase_id`, `status` (`accepted` / `wrong_answer` / `time_limit_exceeded` / `runtime_error` / `compile_error` / `internal_error`), `stdout`, `stderr`, `time` (giây), `memory` (KB), `compile_output` (nếu có) |
| passed_count | int | tổng sample testcase pass |
| total_count | int | tổng sample testcase đã chạy |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Thiếu field, `source_code` rỗng/vượt quá 50.000 ký tự, `stdin_override` vượt quá 10.000 ký tự, `language` không thuộc enum | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 404 | `problem_id` không tồn tại | `{"error_code": "PROBLEM_NOT_FOUND", "message": "Không tìm thấy bài tập"}` |
| 403 | Student chưa enroll, hoặc ngoài khoảng `[start_datetime, end_datetime]`, hoặc Problem còn chưa có sample testcase nào (`is_sample = true`) | `{"error_code": "PROBLEM_NOT_OPEN" \| "FORBIDDEN" \| "NO_SAMPLE_TESTCASE", "message": "..."}` |
| 429 | SV gọi `/run` quá nhiều lần trong thời gian ngắn (vd > 10 lần/phút) — rate limit, **chốt khi implement** | `{"error_code": "RATE_LIMITED", "message": "Bạn gọi quá nhiều. Vui lòng chờ ít giây rồi thử lại"}` |
| 502 | Judge0 không khả dụng / timeout (> 15s) | `{"error_code": "JUDGE_UNAVAILABLE", "message": "Hệ thống chấm bài đang bận, vui lòng thử lại sau"}` |

**Quy tắc nghiệp vụ**

- Chỉ chạy với sample testcase (`is_sample = true`). **Không bao giờ** gửi testcase ẩn cho Judge0 từ endpoint này (xem [api-design-testcase.md § Quy tắc ẩn testcase](api-design-testcase.md)).
- **Không tạo Submission**, không ghi DB. Endpoint là read-only đối với DB.
- Service bọc Judge0 (`judge_client.run(...)`): build request với `base64_encoded=true`, gọi `/submissions/batch?wait=true`, map status id (1-14) sang enum string của API.
- **Yêu cầu quyền**: Student đã enroll và đang trong khoảng `[start_datetime, end_datetime]`. Admin/Teacher cũng có thể gọi để test (xem bảng § Phân quyền).

### POST /problems/{problem_id}/submissions — Nộp bài (lưu Submission)

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| language | string | có | enum: `"python"` \| `"cpp"` \| `"c"` \| `"java"` |
| source_code | string | có | tối đa 50.000 ký tự |

**Response 202 Accepted** — chấm **bất đồng bộ**, FE poll `GET /submissions/{id}` để lấy kết quả

| Field | Kiểu | Ghi chú |
|---|---|---|
| submission_id | int | |
| problem_id | int | |
| student_id | string | |
| language | string | |
| status | string | luôn = `"pending"` ngay khi tạo |
| submitted_datetime | datetime | |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Thiếu field, `source_code` rỗng/vượt quá 50.000 ký tự, `language` không thuộc enum | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 404 | `problem_id` không tồn tại | `{"error_code": "PROBLEM_NOT_FOUND", "message": "Không tìm thấy bài tập"}` |
| 403 | Student chưa enroll, hoặc ngoài khoảng `[start_datetime, end_datetime]`, hoặc Problem chưa có testcase nào | `{"error_code": "PROBLEM_NOT_OPEN" \| "FORBIDDEN" \| "NO_TESTCASE", "message": "..."}` |
| 429 | SV nộp quá nhiều lần trong thời gian ngắn (vd > 5 lần/phút) — rate limit, **chốt khi implement** | `{"error_code": "RATE_LIMITED", "message": "Bạn nộp bài quá nhiều. Vui lòng chờ ít giây rồi thử lại"}` |
| 502 | Judge0 không khả dụng khi service tạo Submission record (khác với lúc chấm) | `{"error_code": "JUDGE_UNAVAILABLE", "message": "..."}` |

**Quy tắc nghiệp vụ**

- Service tạo record `Submission` với `status = "pending"` rồi trả 202 ngay. **Chấm bất đồng bộ** bằng `BackgroundTasks` (FastAPI) hoặc task queue (chốt khi implement).
- Background task: gọi `judge_client.run_all(...)` chạy **toàn bộ testcase** (cả ẩn), poll kết quả, cập nhật `Submission.status`, `passed_count`, `compile_output`, `feedback`, `submitted_code` (giữ nguyên)...
- Mapping status Judge0 → enum API:
  | Judge0 `status.id` | Enum API |
  |---|---|
  | 1, 2 | `pending` (chưa xong) |
  | 3 | `accepted` |
  | 4 | `wrong_answer` |
  | 5 | `time_limit_exceeded` |
  | 6 | `compile_error` |
  | 7-12 | `runtime_error` |
  | 13 | `internal_error` (lỗi Judge0, không phải lỗi SV) |
  | 14 | `exec_format_error` |
- Sau khi chấm xong, **luôn cập nhật `Problem.report`** (field JSON hoặc markdown tóm tắt — chốt khi implement). Bước này gọi internal `PATCH /problems/{id}/report` (không public).
- Nếu Submission `status = accepted` là lần đầu của SV đó trên problem → tăng `Lesson.total_number_student_finished` lên 1 (cùng transaction với cập nhật Submission).
- **Yêu cầu quyền**: Student đã enroll và đang trong khoảng `[start_datetime, end_datetime]`.

### GET /submissions/{submission_id} — FE poll kết quả

**Response 200 OK**

| Field | Kiểu | Ghi chú |
|---|---|---|
| submission_id | int | |
| problem_id | int | |
| student_id | string | |
| language | string | |
| source_code | string | code SV đã nộp (giữ nguyên) |
| status | string | `pending` / `accepted` / `wrong_answer` / `time_limit_exceeded` / `compile_error` / `runtime_error` / `internal_error` / `exec_format_error` |
| compile_output | string \| null | output trình biên dịch (nếu có) |
| feedback | string \| null | feedback tổng quát (vd: `"3/5 testcase passed"`) |
| passed_count | int | |
| total_count | int | tổng testcase của problem (cả ẩn) — chỉ trả khi đã chấm xong |
| submitted_datetime | datetime | |
| results | array of object | chi tiết từng testcase (chỉ trả khi đã chấm xong). Mỗi phần tử: `testcase_id`, `status`, `time`, `memory`, `is_sample`. **Không trả `input` / `expected_output`** — xem [api-design-testcase.md § Quy tắc ẩn testcase](api-design-testcase.md) |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `submission_id` không tồn tại | `{"error_code": "SUBMISSION_NOT_FOUND", "message": "Không tìm thấy bài nộp"}` |
| 403 | Student cố xem submission của người khác, hoặc Teacher không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem bài nộp này"}` |

### GET /problems/{problem_id}/submissions — Lịch sử nộp bài

**Query parameters**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| limit | int | không | mặc định `20`, tối đa `100` |
| offset | int | không | mặc định `0` |

**Response 200 OK** — mảng các object giống response của `GET /submissions/{submission_id}` (không bao gồm `results` để response nhỏ, FE click vào mới gọi detail)

| Field | Kiểu | Ghi chú |
|---|---|---|
| (mảng object) | | mỗi phần tử: `submission_id`, `language`, `status`, `passed_count`, `total_count`, `submitted_datetime` |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `problem_id` không tồn tại | `{"error_code": "PROBLEM_NOT_FOUND", "message": "Không tìm thấy bài tập"}` |
| 403 | Student chưa enroll / ngoài khoảng `[start_datetime, end_datetime]`, Teacher không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "..."}` |
| 422 | `limit` > 100 hoặc < 1 | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |

**Quy tắc nghiệp vụ**

- **Student**: chỉ trả submission của chính mình (`student_id == current_user.user_id`).
- **Teacher chủ lớp / Admin**: trả tất cả submission của mọi SV trong problem.
- Sắp xếp theo `submitted_datetime` **giảm dần** (mới nhất trước).
- **Yêu cầu quyền**: Student đã enroll, hoặc Teacher chủ lớp, hoặc Admin.

### Exception mới (Phase 3, cần thêm vào `submission_service.py`)

- `SubmissionNotFoundError` (404 `SUBMISSION_NOT_FOUND`, message `"Không tìm thấy bài nộp"`)
- `JudgeUnavailableError` (502 `JUDGE_UNAVAILABLE`, message `"Hệ thống chấm bài đang bận, vui lòng thử lại sau"`) — Judge0 timeout / không kết nối được
- `NoSampleTestcaseError` (422 `NO_SAMPLE_TESTCASE`, message `"Bài tập chưa có testcase mẫu để chạy thử"`) — dùng cho `/run` khi problem chưa có `is_sample = true`
- `NoTestcaseError` (422 `NO_TESTCASE`, message `"Bài tập chưa có testcase để nộp"`) — dùng cho `/submissions` khi problem chưa có testcase nào
- `RateLimitedError` (429 `RATE_LIMITED`, message `"Bạn gọi quá nhiều. Vui lòng chờ ít giây rồi thử lại"`) — rate limit

> Tất cả exception trên hiện **CHƯA CÓ** trong `backend/app/core/exceptions.py`. Cần thêm vào `submission_service.py` theo pattern ở `auth_service.py` (xem [global-exception-handler.md § Bước 2](global-exception-handler.md)).
