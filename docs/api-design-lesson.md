# Thiết kế API — Quản lý bài học (Lesson)

> Tài liệu này đặc tả đầy đủ API cho module **Lesson** (bài học trong một lớp học), phục vụ cả **Phase 2 (CRUD Lesson)** lẫn **Phase 3 (Submission & chấm bài)** của [roadmap.md](roadmap.md). Cấu trúc response lỗi và quy ước chung lấy theo [api-design-course.md](api-design-course.md), [api-design-problem.md](api-design-problem.md), [api-design-testcase.md](api-design-testcase.md) và [global-exception-handler.md](global-exception-handler.md).

## Quy ước chung

### Phân quyền truy cập (scope theo vai trò)

| Hành động | Admin | Teacher (chủ lớp) | Teacher (không chủ lớp) | Student (enrolled) | Student (chưa enroll) |
|---|---|---|---|---|---|
| `GET /courses/{course_id}/lessons` (list) | ✅ thấy tất cả | ✅ thấy tất cả lesson trong course | ❌ 403 (không thấy lesson lớp người khác tạo) | ✅ thấy lesson (chỉ trong khoảng `start_date`–`end_date` của lesson) | ❌ 403 |
| `GET /lessons/{lesson_id}` (chi tiết) | ✅ | ✅ (lesson thuộc lớp mình tạo) | ❌ 403 | ✅ (nếu đang trong khoảng thời gian mở) | ❌ 403 |
| `POST /courses/{course_id}/lessons` (tạo) | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 |
| `PATCH /lessons/{lesson_id}` (sửa) | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 |
| `DELETE /lessons/{lesson_id}` (xoá) | ✅ | ✅ | ❌ 403 | ❌ 403 | ❌ 403 |
| `GET /lessons/{lesson_id}/progress` *(Phase 4)* | ✅ | ✅ (lesson thuộc lớp mình tạo) | ❌ 403 | ✅ (chỉ progress của chính mình) | ❌ 403 |

> **Quy ước "chủ lớp"** = `Course.created_by == current_user.user_id` (xem [api-design-course.md](api-design-course.md)). Logic kiểm tra nằm trong `service`, không phải `require_role` ở router.
> **Lưu ý "Teacher (không chủ lớp)"**: cùng role Teacher nhưng **luôn bị 403** khi truy cập lesson thuộc course do Teacher khác tạo — kể cả GET list. Pattern giống [api-design-course.md](api-design-course.md) và [api-design-problem.md](api-design-problem.md).

### Quy ước thời gian (`start_date`, `end_date` của Lesson)

- Lesson dùng kiểu `date` (ngày, không có giờ) — khác với `Course.start_date`/`end_date` (datetime) và `Problem.start_datetime`/`end_datetime` (datetime đầy đủ).
- Áp dụng quy ước thời gian đã chốt ở [api-design-course.md § Quy ước thời gian](api-design-course.md): **client gửi giờ Việt Nam, không kèm offset** (vd `"2026-10-15"`). Trước khi deadline của Problem/Submission hoạt động, BE sẽ chuyển sang `timestamptz` (Phase 0 của [roadmap.md](roadmap.md) — chưa hoàn thành).
- `start_date` phải **trước hoặc bằng** `end_date` (`start_date <= end_date`). Nếu vi phạm → 422 `INVALID_FORMAT`.
- `start_date` phải **nằm trong hoặc bằng** `Course.start_date.date()` của course cha.
- `end_date` phải **nằm trong hoặc bằng** `Course.end_date.date()` của course cha.
- Nếu `start_date` hoặc `end_date` nằm ngoài khoảng của Course → 422 `LESSON_OUT_OF_COURSE_RANGE`.

### Quy ước xoá có cascade

- `DELETE /lessons/{lesson_id}` xoá lesson và **toàn bộ Problem + Testcase + Submission liên quan** (cascade qua FK). Mặc định chặn khi còn Problem con (409 `LESSON_NOT_EMPTY`), có flag `?force=true` để cascade (xem § `DELETE /lessons/{lesson_id}`).
- **Không cho phép restore** sau khi xoá (theo pattern của các module khác trong repo).
- Khi xoá cascade `force=true`: cần xử lý thêm **Submission** (xoá record `Submission` + file output nếu có) — xem [api-design-problem.md § DELETE](api-design-problem.md) và [api-design-testcase.md § Cascade](api-design-testcase.md).

### Cột đếm

| Cột | Cập nhật khi | Ghi chú |
|---|---|---|
| `Lesson.total_number_assignment` | Tạo/xoá Problem con | Tăng khi thêm Problem, giảm khi xoá. Cập nhật **trong service** (không dùng trigger DB) để giữ logic ở một nơi |
| `Lesson.total_number_student_finished` | Sau khi Submission của 1 SV đạt Accepted (Phase 3) | Tăng khi có Submission `status = accepted` mới từ 1 SV. Logic chốt ở Phase 3 (Submission service). **Phase 2 chưa cập nhật cột này** |
| `Course.total_number_student` | Không liên quan | Lesson không đụng đến cột này |

### Quy tắc slug & response

- `lesson_number` là số nguyên dương, **duy nhất trong phạm vi 1 course** (2 lesson cùng course không được trùng số). Không cần duy nhất global.
- **Quan trọng**: model `Lesson` hiện tại (`backend/app/models/entities.py`) **không có unique constraint** trên `(course_id, lesson_number)`. Khi implement service phải check trùng lặp trước khi insert (`SELECT ... WHERE course_id = ? AND lesson_number = ?`); nếu tìm thấy → raise `LessonNumberConflictError`. Có thể cân nhắc thêm unique constraint vào migration Alembic sau khi Phase 2 ổn định (rủi ro: migration fail nếu DB đã có data trùng).
- Response **luôn dùng `response_model`** đã khai báo, không trả field thừa từ model.
- Các field lạ trong request body `POST`/`PATCH` sẽ bị Pydantic bỏ qua theo cấu hình `model_config` (giống `course_service.py`).
- `created_by` (FK user) chưa có trong model `Lesson` hiện tại (`backend/app/models/entities.py` — chỉ có `lesson_id, lesson_number, lesson_name, course_id, total_number_assignment, total_number_student_finished, start_date, end_date`). **Cần thêm cột `created_by` trong migration Alembic trước khi implement**, set = `current_user.user_id` khi tạo. Phase 3 có thể tận dụng cột này để thống kê "GV nào soạn bài nhiều nhất". Nếu cố tình không thêm → docs này sẽ được cập nhật để bỏ field khỏi response.

### Xử lý lỗi

- Mọi exception nghiệp vụ kế thừa `AppError` (xem [global-exception-handler.md](global-exception-handler.md)). Router không viết `try/except`.
- Lỗi dùng chung (đặt trong `core/exceptions.py`):
  - `NotFoundError` (404 `NOT_FOUND`, message cụ thể theo ngữ cảnh) — dùng chung cho mọi resource, **route/service sẽ map** sang message cụ thể (`"Không tìm thấy lớp học"` / `"Không tìm thấy bài học"` / ...).
  - `ConflictError` (409 `CONFLICT`, message cụ thể).
  - `ForbiddenError` (403 `FORBIDDEN`, message cụ thể theo ngữ cảnh — `"Bạn không có quyền thêm bài học vào lớp này"` / `"Bạn không có quyền xem bài học này"` / ...).
  - `EmptyFieldError` (422 `EMPTY_FIELD`).
  - `InvalidFormatError` (422 `INVALID_FORMAT`).
- Lỗi riêng của domain `lesson` (đặt trong `backend/app/modules/lessons/service.py`):
  - `LessonNotFoundError` (404 `LESSON_NOT_FOUND`, message `"Không tìm thấy bài học"`)
  - `LessonNumberConflictError` (409 `LESSON_NUMBER_CONFLICT`, message `"Số thứ tự bài học đã tồn tại trong lớp này"`)
  - `LessonOutOfCourseRangeError` (422 `LESSON_OUT_OF_COURSE_RANGE`, message `"Ngày bài học phải nằm trong khoảng thời gian của lớp"`)
  - `LessonNotEmptyError` (409 `LESSON_NOT_EMPTY`, message `"Không thể xoá bài học đang có bài tập. Hãy xoá hết bài tập trước"`) — **mặc định chặn xoá khi còn Problem**, có flag `?force=true` để cascade (xem § `DELETE /lessons/{lesson_id}`)

> **Ghi chú quan trọng**: `LessonNotFoundError`, `LessonNumberConflictError`, `LessonOutOfCourseRangeError`, `LessonNotEmptyError` hiện **CHƯA CÓ** trong `backend/app/core/exceptions.py` (file này mới chỉ có các exception dùng chung cho Auth/Course). Cần thêm vào `lesson_service.py` khi implement Phase 2, theo pattern đã có ở `auth_service.py` (xem [global-exception-handler.md § Bước 2](global-exception-handler.md)).

---

## POST /courses/{course_id}/lessons — Tạo bài học

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| lesson_number | int | có | số nguyên dương, duy nhất trong course |
| lesson_name | string | có | tối đa 255 ký tự, tự trim 2 đầu trước khi lưu |
| start_date | date | có | xem [Quy ước thời gian](#quy-ước-thời-gian-start_date-end_date-của-lesson) |
| end_date | date | có | phải ≥ `start_date` và nằm trong khoảng của course |

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| lesson_id | int | |
| lesson_number | int | |
| lesson_name | string | |
| course_id | string | |
| total_number_assignment | int | luôn = 0 lúc tạo |
| total_number_student_finished | int | luôn = 0 lúc tạo |
| start_date | date | |
| end_date | date | |
| created_by | string | `user_id` của người tạo |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Thiếu field, field bắt buộc = `null`, sai kiểu dữ liệu, vượt quá độ dài tối đa, hoặc `lesson_name` là chuỗi rỗng `""` | `{"error_code": "VALIDATION_ERROR", "message": "..."}` (message của pydantic) |
| 422 | `lesson_name` chỉ chứa khoảng trắng, vd `"   "` | `{"error_code": "EMPTY_FIELD", "message": "lesson_name không được để trống"}` |
| 422 | `start_date > end_date` | `{"error_code": "INVALID_FORMAT", "message": "start_date phải trước hoặc bằng end_date"}` |
| 422 | `start_date` < `Course.start_date.date()` hoặc `end_date` > `Course.end_date.date()` | `{"error_code": "LESSON_OUT_OF_COURSE_RANGE", "message": "Ngày bài học phải nằm trong khoảng thời gian của lớp"}` |
| 404 | `course_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học"}` |
| 403 | Người gọi không phải Admin, hoặc là Teacher nhưng không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thêm bài học vào lớp này"}` |
| 409 | `lesson_number` đã tồn tại trong course này | `{"error_code": "LESSON_NUMBER_CONFLICT", "message": "Số thứ tự bài học đã tồn tại trong lớp này"}` |

**Quy tắc nghiệp vụ**

- `total_number_assignment` và `total_number_student_finished` luôn khởi tạo = 0, không nhận từ client.
- `created_by` luôn set = `user_id` của người đang đăng nhập (cần bổ sung cột này trong migration — xem § Quy tắc slug & response).
- `lesson_name` được tự động trim khoảng trắng hai đầu trước khi lưu (giống `course_id`, `course_name`, `term` ở Course).
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

---

## GET /courses/{course_id}/lessons — Danh sách bài học trong lớp

**Query parameters**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| include_inactive | bool | không | mặc định `false`. Khi `false`: Student chỉ thấy lesson có `start_date <= today <= end_date`. Khi `true`: thấy tất cả lesson. Admin/Teacher luôn thấy tất cả bất kể flag |

**Response 200 OK**: mảng object giống response của `POST /courses/{course_id}/lessons`, sắp xếp theo `lesson_number` tăng dần. Không có lesson nào → `[]`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `course_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học"}` |
| 403 | Student chưa enroll vào course này | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem lớp học này"}` |
| 403 | Teacher cố xem lesson của lớp không phải do mình tạo | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem lớp học này"}` |
| 403 | Role của người gọi không thuộc Admin/Teacher/Student | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Kết quả tự động scope theo vai trò người gọi:
  - **Admin**: thấy tất cả lesson trong course.
  - **Teacher chủ lớp**: thấy tất cả lesson trong course do mình tạo.
  - **Teacher không phải chủ lớp**: 403 (xem bảng § Phân quyền).
  - **Student đã enroll**: thấy lesson trong khoảng thời gian mở (mặc định). Có thể bật `include_inactive=true` để xem tất cả (vd xem lesson đã đóng cửa trong quá khứ).
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi truy cập theo vai trò (xem § Phân quyền).

---

## GET /lessons/{lesson_id} — Chi tiết bài học

**Response 200 OK**: object giống response của `POST /courses/{course_id}/lessons`. Ngoài ra (Phase 2 nên bổ sung luôn để FE render sẵn):

| Field | Kiểu | Ghi chú |
|---|---|---|
| problems | array of object | danh sách Problem thuộc lesson, sắp theo `problem_id` tăng dần. Có thể trả `[]` ở Phase 2 và bổ sung ở Phase 3 |

**Query parameters** (tùy chọn, hỗ trợ giống `GET /courses/{course_id}/lessons`):

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| include_inactive | bool | không | mặc định `false`. Student không thể xem lesson đã đóng cửa khi flag = `false` |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `lesson_id` không tồn tại | `{"error_code": "LESSON_NOT_FOUND", "message": "Không tìm thấy bài học"}` |
| 403 | Student chưa enroll vào course chứa lesson này, hoặc lesson đã đóng cửa và `include_inactive=false` | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem bài học này"}` |
| 403 | Teacher cố truy cập lesson thuộc lớp không phải do mình tạo | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem bài học này"}` |
| 403 | Role của người gọi không thuộc Admin/Teacher/Student | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Áp dụng cùng quy tắc scope như `GET /courses/{course_id}/lessons`, cho 1 lesson cụ thể.
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi truy cập theo vai trò.

---

## PATCH /lessons/{lesson_id} — Cập nhật bài học

**Request body** (tất cả optional, chỉ cập nhật field được truyền)

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| lesson_number | int | không | nếu đổi, phải không trùng với lesson khác trong cùng course |
| lesson_name | string | không | tối đa 255 ký tự, tự trim 2 đầu |
| start_date | date | không | nếu đổi, phải ≤ `end_date` hiện tại hoặc mới (nếu cũng đổi `end_date`), và nằm trong khoảng của course |
| end_date | date | không | nếu đổi, phải ≥ `start_date` hiện tại hoặc mới, và nằm trong khoảng của course |

Field gửi lên với giá trị `null` sẽ bị **bỏ qua** (giữ nguyên giá trị cũ), không phải xoá giá trị. Body rỗng `{}` hoặc toàn `null` → không cập nhật gì, trả 200 với dữ liệu hiện tại.

**Response 200 OK**: object giống response của `POST /courses/{course_id}/lessons`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `lesson_id` không tồn tại | `{"error_code": "LESSON_NOT_FOUND", "message": "Không tìm thấy bài học"}` |
| 403 | Người gọi không phải Admin, hoặc là Teacher nhưng không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền chỉnh sửa bài học này"}` |
| 422 | Sai kiểu dữ liệu, vượt quá độ dài tối đa | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 422 | `lesson_name` được truyền nhưng rỗng hoặc chỉ chứa khoảng trắng | `{"error_code": "EMPTY_FIELD", "message": "lesson_name không được để trống"}` |
| 422 | `start_date > end_date` (so với giá trị hiện tại trong DB nếu chỉ gửi 1 trong 2) | `{"error_code": "INVALID_FORMAT", "message": "start_date phải trước hoặc bằng end_date"}` |
| 422 | `start_date` hoặc `end_date` mới nằm ngoài khoảng của course | `{"error_code": "LESSON_OUT_OF_COURSE_RANGE", "message": "Ngày bài học phải nằm trong khoảng thời gian của lớp"}` |
| 409 | `lesson_number` mới đã tồn tại trong course | `{"error_code": "LESSON_NUMBER_CONFLICT", "message": "Số thứ tự bài học đã tồn tại trong lớp này"}` |

**Quy tắc nghiệp vụ**

- Không cho sửa `lesson_id`, `course_id`, `total_number_assignment`, `total_number_student_finished`, `created_by` qua endpoint này (field lạ trong body bị bỏ qua).
- Nếu đổi `lesson_number`, validate không trùng trong cùng `course_id` (không phải global).
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

---

## DELETE /lessons/{lesson_id} — Xoá bài học

**Query parameters**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| force | bool | không | mặc định `false`. Khi `false`: nếu còn Problem con → 409 `LESSON_NOT_EMPTY`. Khi `true`: cascade xoá toàn bộ Problem + Testcase + Submission con (xem § Quy ước xoá có cascade) |

**Response**: `204 No Content`

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `lesson_id` không tồn tại | `{"error_code": "LESSON_NOT_FOUND", "message": "Không tìm thấy bài học"}` |
| 403 | Người gọi không phải Admin, hoặc là Teacher nhưng không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xoá bài học này"}` |
| 409 | `force=false` và lesson còn Problem con | `{"error_code": "LESSON_NOT_EMPTY", "message": "Không thể xoá bài học đang có bài tập. Hãy xoá hết bài tập trước"}` |

**Quy tắc nghiệp vụ**

- Khi xoá thành công (kể cả cascade), `Course.total_number_student` **không đổi** (Lesson không liên quan đến enrollment).
- Khi xoá cascade (`force=true`): xoá toàn bộ `Problem` con → cascade xoá toàn bộ `Testcase` con → cascade xoá toàn bộ `Submission` con. Mọi thao tác phải nằm trong **một transaction** (dùng `session.begin()` hoặc tương đương); nếu lỗi giữa chừng thì rollback toàn bộ, không xoá dở.
- **Phase 3 bổ sung**: nếu cascade Submission, cần cân nhắc giữ lại record Submission ở trạng thái "deleted" (không xoá cứng) để phục vụ thống kê Phase 4. Chốt khi implement Phase 3.
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

---

## Mở rộng trong tương lai (Phase 4 trở đi, **không implement ở Phase 2/3**)

- `GET /lessons/{lesson_id}/progress` — trả `total_number_student_finished` đã tính sẵn và danh sách SV đã hoàn thành (Phase 4 — theo dõi tiến độ). Có thể trả thêm `submission_count` (số lượt nộp) để FE hiển thị "bài này SV đã nộp X lần".
- `GET /courses/{course_id}/lessons?include_inactive=true` — đã chốt từ Phase 2.
- Bulk import lesson bằng Excel — chưa chốt, có thể bỏ scope nếu trễ (xem [roadmap.md § Cắt scope](roadmap.md)).
- `GET /lessons/{lesson_id}/submissions` — lịch sử nộp bài **của GV xem** (tất cả SV trong lớp) — Phase 4. Phase 3 chỉ có endpoint `GET /problems/{problem_id}/submissions` (xem [api-design-problem.md](api-design-problem.md)).

---

## Liên quan tới Phase 3 (Submission & chấm bài)

Lesson **không có endpoint Phase 3 mới** (Phase 3 chỉ thêm endpoint ở Problem & Submission). Tuy nhiên, Lesson bị ảnh hưởng gián tiếp:

- **Cột `total_number_student_finished`**: được tăng bởi Submission service khi có Submission mới `status = accepted` từ 1 SV. Xem chi tiết ở [api-design-problem.md § Cột đếm](api-design-problem.md).
- **Cascade xoá**: nếu `DELETE /lessons/{id}?force=true` chạy trong khi có Submission đang xử lý (status `pending`) → service phải đợi/cancel submission đó trước khi xoá (chốt khi implement Phase 3).
- **FE dùng** `GET /lessons/{id}` để lấy danh sách Problem kèm lesson — FE sẽ dựa vào đó gọi tiếp `POST /problems/{problem_id}/run` hoặc `POST /problems/{problem_id}/submissions`.
- `GET /lessons/{lesson_id}/submissions` — lịch sử nộp bài **của GV xem** (tất cả SV trong lớp) — Phase 4. Phase 3 chỉ có endpoint `GET /problems/{problem_id}/submissions` (xem [api-design-problem.md](api-design-problem.md)).
