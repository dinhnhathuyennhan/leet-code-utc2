# Thiết kế API — Quản lý lớp học (Course)

## Phân quyền tổng quát

- **Admin không vận hành lớp học.** Admin chỉ **xem** lớp học phần do giảng viên quản lý: danh sách và chi tiết lớp, buổi học, bài tập và testcase trong buổi, danh sách sinh viên, bảng điểm (kể cả xuất Excel). Admin không tạo/sửa lớp, không can thiệp buổi học, bài tập trong buổi, testcase, ghi danh và bài nộp; gọi các API ghi đó nhận **403**.
- Các thao tác ghi trên do **Teacher chủ lớp** (`course.created_by`) thực hiện.
- Admin vẫn được **xoá lớp**, kể cả xoá cưỡng bức (`force=true`), xem mục DELETE bên dưới.

## Quy ước thời gian

Áp dụng cho các field `datetime` của Course, Problem và Submission.

- Client gửi datetime bắt buộc có UTC offset (vd: `"2026-09-07T00:00:00+07:00"`). Backend chấp nhận offset tường minh và trả thời gian theo `Asia/Ho_Chi_Minh` với offset `+07:00`.
- Database lưu các thời điểm dưới dạng `timestamptz` theo UTC. Khi đọc, backend chuyển sang giờ Việt Nam có timezone.
- Field kiểu `date` của Lesson (`start_date`, `end_date`) là ngày lịch, không có giờ hay offset. Course dùng `datetime`. Lesson mở lúc 00:00 giờ Việt Nam ngày `start_date`, hết hạn lúc 23:59:59.999999 ngày `end_date`; `opens_at` và `deadline` trả giờ Việt Nam kèm `+07:00`.
- Với Problem, `start_datetime` quyết định lúc mở đề; `end_datetime` chỉ chặn Submit, không chặn xem đề.
- Phía FE hiển thị theo `Asia/Ho_Chi_Minh` để không phụ thuộc múi giờ trình duyệt.

## Quan hệ với Problem bank

Problem bank có `lesson_id = null` nên chưa thuộc Course; bản nguồn không xuất hiện trong `sessions[].problems` hoặc dữ liệu điểm của Course. Khi thêm bài bank vào Lesson, hệ thống tạo Problem bản sao gắn với Lesson đích; Course response và thống kê dùng bản sao đó.

## POST /courses — Tạo lớp học

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| course_id | string | có | mã lớp học, duy nhất, tối đa 50 ký tự |
| course_name | string | có | tối đa 255 ký tự |
| term | string | có | học kỳ, tối đa 255 ký tự |
| start_date | datetime | có | phải trước `end_date`, xem [Quy ước thời gian](#quy-ước-thời-gian) |
| end_date | datetime | có | |
| avt_link | string | không | tối đa 2048 ký tự |

`course_id`, `course_name`, `term` được tự động trim khoảng trắng hai đầu trước khi lưu (`avt_link` giữ nguyên).

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| course_id | string | |
| course_name | string | |
| term | string | |
| start_date | datetime | |
| end_date | datetime | |
| avt_link | string \| null | |
| created_by | string | `user_id` của người tạo |
| total_number_student | int | luôn = 0 lúc tạo |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Thiếu field, field bắt buộc = `null`, sai kiểu dữ liệu, vượt quá độ dài tối đa, hoặc `course_id` / `course_name` / `term` là chuỗi rỗng `""` (use-case bước 5a) | `{"error_code": "VALIDATION_ERROR", "message": "..."}` (message của pydantic, tiếng Anh) |
| 422 | `course_id` / `course_name` / `term` chỉ chứa khoảng trắng, vd `"   "` (use-case bước 5a) | `{"error_code": "EMPTY_FIELD", "message": "<field> không được để trống"}` |
| 422 | `start_date` không trước `end_date` (use-case bước 5a) | `{"error_code": "INVALID_FORMAT", "message": "start_date phải trước end_date"}` |
| 403 | Người gọi không phải Teacher (Admin chỉ xem lớp học phần) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 409 | `course_id` đã tồn tại (use-case bước 6a) | `{"error_code": "CONFLICT", "message": "Mã lớp học đã tồn tại"}` |

**Quy tắc nghiệp vụ**

- `created_by` luôn set = `user_id` của người đang đăng nhập, không nhận từ client.
- `total_number_student` luôn khởi tạo = 0, không nhận từ client. Ở các response chi tiết/danh sách lớp học (có buổi học), giá trị này là số dòng `enrollment` thật của lớp tại thời điểm gọi, không đọc cột cache.
- **Yêu cầu quyền**: chỉ Teacher (`require_role(Role.TEACHER)`). Admin chỉ xem lớp học phần, không tạo lớp (403).

## GET /courses — Danh sách lớp học

**Response 200 OK**: mảng object giống response của `POST /courses`, sắp xếp theo `course_id`. Không có lớp nào → `[]`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 403 | Role của người gọi không thuộc Admin/Teacher/Student | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Kết quả tự động scope theo vai trò người gọi: Admin thấy toàn bộ lớp học; Teacher chỉ thấy lớp có `created_by = user_id` của chính mình; Student chỉ thấy lớp mình có `Enrollment`.
- **Yêu cầu quyền**: Bearer token hợp lệ (bất kỳ role nào).

## GET /courses/{course_id} — Chi tiết lớp học

**Response 200 OK**: object giống response của `POST /courses`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `course_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học"}` |
| 403 | Teacher không phải chủ lớp, Student chưa được thêm vào lớp (use-case "Xem danh sách sinh viên" bước 2a/2b), hoặc role không thuộc Admin/Teacher/Student | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem lớp học này"}` |

**Quy tắc nghiệp vụ**

- Cùng quy tắc scope như `GET /courses`, áp dụng cho 1 lớp cụ thể.
- `sessions[].participant_count`: số sinh viên **đang ghi danh** trong lớp đã nộp ít nhất một bài của buổi học đó. Bài nộp của sinh viên đã bị xoá khỏi lớp không được đếm. Sinh viên gọi thì nhận `null`.
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi truy cập theo vai trò.

## PATCH /courses/{course_id} — Cập nhật lớp học

**Request body** (tất cả optional, chỉ cập nhật field được truyền)

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| course_name | string | không | tối đa 255 ký tự |
| term | string | không | tối đa 255 ký tự |
| start_date | datetime | không | xem [Quy ước thời gian](#quy-ước-thời-gian) |
| end_date | datetime | không | |
| avt_link | string | không | tối đa 2048 ký tự. Không gỡ được ảnh: gửi `null` sẽ bị bỏ qua |

Field gửi lên với giá trị `null` sẽ bị **bỏ qua** (giữ nguyên giá trị cũ), không phải xoá giá trị.

**Response 200 OK**: object giống response của `POST /courses`. Body rỗng `{}` hoặc toàn `null` → không cập nhật gì, trả 200 với dữ liệu hiện tại.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `course_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học"}` |
| 403 | Người gọi không phải Teacher (kể cả Admin), hoặc Teacher không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 422 | Sai kiểu dữ liệu, vượt quá độ dài tối đa | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 422 | `course_name` / `term` được truyền nhưng rỗng hoặc chỉ chứa khoảng trắng | `{"error_code": "EMPTY_FIELD", "message": "<field> không được để trống"}` |
| 422 | `start_date` không trước `end_date` (nếu chỉ gửi một trong hai, so với giá trị đang lưu trong DB) | `{"error_code": "INVALID_FORMAT", "message": "start_date phải trước end_date"}` |

**Quy tắc nghiệp vụ**

- Không cho sửa `course_id`, `created_by`, `total_number_student` qua endpoint này (field lạ trong body bị bỏ qua).
- **Yêu cầu quyền**: chỉ Teacher chủ lớp (`require_role(Role.TEACHER)` + `created_by == current_user.user_id`). Admin chỉ xem, không sửa lớp (403).

## DELETE /courses/{course_id} — Xoá lớp học

**Quyền**: Admin (mọi lớp) hoặc Teacher là chủ lớp (`created_by`). Riêng `force=true` chỉ Admin. Đây là thao tác ghi duy nhất trên lớp học phần mà Admin còn giữ.

Xoá lớp cùng toàn bộ buổi học, bài tập (bản sao trong lớp), testcase của các bài đó và danh sách ghi danh. Đề nguồn trong ngân hàng (`lesson_id = null`) và tài khoản Sinh viên không bị ảnh hưởng.

**Query parameter**

| Tham số | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| force | bool | không | mặc định `false`. `true`: xoá vĩnh viễn cả bài nộp của Sinh viên trong lớp. Chỉ Admin được dùng |

Ví dụ: `DELETE /courses/JAVA01?force=true`

**Request body**: không có

**Response 204 No Content**

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | `force` không phải giá trị boolean, vd `force=maybe` | `{"error_code": "VALIDATION_ERROR", "message": "..."}` (message của pydantic, tiếng Anh) |
| 403 | Người gọi không phải Admin/Teacher | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 403 | `force=true` nhưng người gọi là Teacher, kể cả chủ lớp. Kiểm tra trước mọi truy vấn, nên trả 403 cả khi lớp không tồn tại | `{"error_code": "FORBIDDEN", "message": "Chỉ Admin mới được xoá lớp học đã có bài nộp"}` |
| 404 | `course_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học"}` |
| 403 | Teacher không phải chủ lớp (use-case "Xoá lớp học" bước 4b) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xoá lớp học này"}` |
| 409 | Không dùng `force` mà lớp đã có bài nộp của Sinh viên (bước 5a, 5b) | `{"error_code": "COURSE_HAS_SUBMISSIONS", "message": "Không thể xoá lớp học đã có bài nộp của sinh viên (2 bài nộp)"}` |
| 409 | Có bài nộp mới chen vào ngay lúc đang xoá (E2) | `{"error_code": "COURSE_HAS_SUBMISSIONS", "message": "Lớp học vừa có bài nộp mới của sinh viên, vui lòng thử lại"}` |

**Quy tắc nghiệp vụ**

- Mặc định **không xoá lớp đã có bài nộp**, để giữ lịch sử chấm của Sinh viên. Message 409 ghi số bài nộp để FE hỏi Admin có muốn xoá cưỡng bức không.
- `force=true` (chỉ Admin): xoá vĩnh viễn mọi bài nộp của các bài tập trong lớp, rồi xoá lớp như trên. Không thể khôi phục. Lớp chưa có bài nộp thì `force=true` xoá như bình thường.
- Toàn bộ thao tác xoá nằm trong một transaction. Nếu có bài nộp mới được ghi vào sau bước kiểm tra, khoá ngoại chặn việc xoá, hệ thống rollback (lớp giữ nguyên) và trả 409 như bảng trên để thử lại.
- Xoá cưỡng bức được ghi log ứng dụng (mức INFO): `user_id` của Admin, `course_id` và số bài nộp đã xoá.
- Bài nộp đang được chấm mà bị xoá: worker chấm bài dừng chấm và bỏ kết quả, không thử lại.
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp (`require_role(Role.ADMIN, Role.TEACHER)` + kiểm tra `created_by`); `force=true` chỉ Admin.

## POST /courses/{course_id}/enrollments — Thêm sinh viên vào lớp

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| student_id | string | một trong hai | `user_id` (UUID) của Sinh viên. Để tương thích FE hiện tại, giá trị không phải UUID được tra như MSSV |
| student_code | string | một trong hai | MSSV, đúng 10 chữ số (nhận cả số JSON) |

Truyền **đúng một** trong `student_id` / `student_code`. Chuỗi rỗng hoặc toàn khoảng trắng được coi như không truyền.

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| enrollment_id | int | |
| course_id | string | |
| student_id | string | UUID của Sinh viên |
| student_code | string \| null | MSSV |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Không truyền `student_id` lẫn `student_code` | `{"error_code": "EMPTY_FIELD", "message": "Cần nhập student_id (UUID) hoặc student_code (MSSV)"}` |
| 422 | Truyền cả `student_id` và `student_code` | `{"error_code": "INVALID_FORMAT", "message": "Chỉ được truyền một trong hai: ..."}` |
| 422 | `student_code` không đúng 10 chữ số ASCII | `{"error_code": "INVALID_FORMAT", "message": "Mã sinh viên phải gồm đúng 10 chữ số"}` (hoặc "...chỉ được gồm chữ số (0-9)") |
| 404 | `course_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học"}` |
| 404 | `student_id` / `student_code` không khớp Sinh viên nào, hoặc thuộc tài khoản không phải Sinh viên (use-case bước 4a) | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy sinh viên"}` |
| 403 | Người gọi không phải Teacher (Admin chỉ xem lớp học phần) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 403 | Teacher không phải chủ lớp (use-case bước 3a) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thêm sinh viên vào lớp này"}` |
| 409 | Sinh viên đã có trong lớp học (use-case bước 5a), kể cả khi 2 request thêm cùng một Sinh viên chạy cùng lúc (E2) | `{"error_code": "CONFLICT", "message": "Sinh viên đã có trong lớp học"}` |

**Quy tắc nghiệp vụ**

- Sau khi thêm thành công, `total_number_student` được đếm lại từ bảng `enrollment` (không cộng dồn), nên giá trị cũ bị lệch cũng tự đúng lại.
- DB có ràng buộc unique `uq_enrollment_course_student` trên (`course_id`, `student_id`). Nếu 2 request cùng qua bước kiểm tra trùng, request đến sau bị ràng buộc chặn, rollback (sĩ số không tăng) và nhận 409 như trên, không phải 500.
- **Yêu cầu quyền**: chỉ Teacher chủ lớp (`require_role(Role.TEACHER)`). Admin chỉ xem danh sách sinh viên, không ghi danh (403).

## POST /courses/{course_id}/enrollments/class — Thêm cả lớp hành chính vào lớp học

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| class_id | string | có | mã lớp hành chính, vd `CQ.67.CNTT`, 1-50 ký tự (xem [api-design-class.md](api-design-class.md)) |

Ví dụ:

```json
{ "class_id": "CQ.67.CNTT" }
```

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| course_id | string | |
| class_id | string | |
| added_count | int | số Sinh viên vừa được thêm |
| skipped_count | int | số Sinh viên của lớp hành chính đã có trong lớp học từ trước, bị bỏ qua |
| added_student_ids | string[] | `user_id` (UUID) của các Sinh viên vừa được thêm |

```json
{
  "course_id": "JAVA01",
  "class_id": "CQ.67.CNTT",
  "added_count": 95,
  "skipped_count": 2,
  "added_student_ids": ["3f6c1e2a-...", "..."]
}
```

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Thiếu `class_id`, rỗng `""` hoặc dài quá 50 ký tự | `{"error_code": "VALIDATION_ERROR", "message": "..."}` (message của pydantic, tiếng Anh) |
| 403 | Người gọi không phải Teacher (Admin chỉ xem lớp học phần) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 404 | `course_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học"}` |
| 403 | Teacher không phải chủ lớp (use-case "Thêm lớp hành chính vào lớp học" bước 4a) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thêm sinh viên vào lớp này"}` |
| 404 | `class_id` không tồn tại (bước 5a) | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp hành chính"}` |
| 409 | Có Sinh viên của lớp hành chính vừa được request khác thêm vào lớp học cùng lúc (E3) | `{"error_code": "CONFLICT", "message": "Danh sách lớp học vừa được thay đổi đồng thời, vui lòng thử lại"}` |

**Quy tắc nghiệp vụ**

- Chỉ lấy tài khoản có `class_id` bằng lớp hành chính và `role_id = 3` (Sinh viên). Sinh viên đã có trong lớp học được bỏ qua, không báo lỗi.
- Cả lô được lưu trong **một transaction**: `total_number_student` được đếm lại từ bảng `enrollment`. Nếu ràng buộc unique (`course_id`, `student_id`) chặn một dòng bất kỳ (request đồng thời), **cả lô bị huỷ**, không Sinh viên nào được thêm, sĩ số không lệch; gọi lại thì những Sinh viên đã có sẽ được tính vào `skipped_count`.
- Lớp hành chính không có Sinh viên nào: trả 201 với `added_count = 0`.
- **Yêu cầu quyền**: chỉ Teacher chủ lớp (`require_role(Role.TEACHER)`). Admin chỉ xem danh sách sinh viên, không ghi danh (403).

## GET /courses/{course_id}/enrollments — Danh sách sinh viên trong lớp

**Response 200 OK**

| Field | Kiểu | Ghi chú |
|---|---|---|
| (mảng object) | | mỗi phần tử: `enrollment_id`, `student_id` (UUID), `student_code` (MSSV, có thể null), `full_name`, `email`, `class_id`, `is_active` |
| class_id | string \| null | lớp hành chính của Sinh viên. Chỉ trả cho Admin/Teacher; Student gọi thì luôn `null` |
| is_active | bool \| null | `false` nếu tài khoản Sinh viên đang bị khoá. Chỉ trả cho Admin/Teacher; Student gọi thì luôn `null` |

Ví dụ một phần tử (Admin/Teacher gọi):

```json
{
  "enrollment_id": 12,
  "student_id": "3f6c1e2a-...",
  "student_code": "6751071001",
  "full_name": "Nguyễn Văn A",
  "email": "6751071001@st.utc2.edu.vn",
  "class_id": "CQ.67.CNTT",
  "is_active": true
}
```

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `course_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học"}` |
| 403 | Teacher không phải chủ lớp, hoặc Student không thuộc lớp này (use-case bước 2a/2b) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem lớp học này"}` |

**Quy tắc nghiệp vụ**

- Admin và Teacher chủ lớp thấy toàn bộ danh sách; Student chỉ gọi được cho chính lớp mình đã được thêm vào.
- `class_id` và `is_active` chỉ trả khi người gọi là Admin hoặc Teacher (whitelist theo `role_id`); Student nhận `null` để không lộ lớp hành chính và trạng thái khoá của bạn cùng lớp.
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi truy cập theo vai trò.

## DELETE /courses/{course_id}/enrollments/{student_id} — Xoá sinh viên khỏi lớp

**Request body**: không có

**Response**: `204 No Content`

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `course_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp học"}` |
| 404 | `student_id` không có `Enrollment` trong lớp này (use-case bước 5a) | `{"error_code": "NOT_FOUND", "message": "Sinh viên không thuộc lớp học này"}` |
| 403 | Người gọi không phải Teacher (Admin chỉ xem lớp học phần) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 403 | Teacher không phải chủ lớp (use-case bước 4a) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Sau khi xoá thành công, `total_number_student` được đếm lại từ bảng `enrollment`.
- **Yêu cầu quyền**: chỉ Teacher chủ lớp (`require_role(Role.TEACHER)`). Admin chỉ xem danh sách sinh viên, không ghi danh (403).

## GET /students/{student_id}/dashboard — Tổng quan học tập của sinh viên

**Response 200 OK**

| Field | Kiểu | Ghi chú |
|---|---|---|
| total_classes | int | Số lớp sinh viên đang ghi danh (trong phạm vi người gọi được xem) |
| completed_problems | int | Số bài đã có ít nhất một bài nộp `accepted` (mỗi bài đếm 1 lần) |
| total_problems | int | Tổng số bài tập của các lớp trên |
| average_score | float \| null | Điểm trung bình **thang 10**, làm tròn 2 chữ số. `null` khi chưa có bài nào có điểm |
| due_this_week | int | Số bài đang mở, hạn nộp trong 7 ngày tới (tính cả hôm nay) mà sinh viên chưa nộp đạt |
| courses | array | Danh sách lớp, mỗi phần tử cùng shape với `GET /courses/{course_id}` |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `student_id` không phải UUID (mọi vai trò); hoặc Admin/Sinh viên xem `student_id` không tồn tại hay không phải Sinh viên | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy sinh viên"}` |
| 403 | Sinh viên xem của người khác, hoặc Giáo viên xem `student_id` không học lớp nào do mình tạo (kể cả `student_id` không tồn tại: Giáo viên nhận 403, không phải 404) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem thông tin sinh viên này"}` |
| 403 | Role của người gọi không thuộc Admin/Teacher/Student | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Phạm vi lớp: Admin và chính sinh viên thấy mọi lớp sinh viên đang ghi danh. Giáo viên chỉ thấy các lớp do mình tạo, mọi chỉ số (kể cả `average_score`) cũng chỉ tính trên các lớp đó.
- `average_score`: mỗi bài lấy **một** bài nộp theo đúng cách bảng điểm lớp chọn: ưu tiên bài có điểm chấm tay (`manual_score`), nếu không thì bài có `passed_count` cao nhất (điểm = `passed_count / total_number_testcase × 10`, làm tròn 1 chữ số). Sau đó lấy trung bình trên các bài có điểm. Bài chưa nộp không tính vào mẫu số.
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi theo vai trò như trên.

## GET /courses/{course_id}/grades/export — Xuất bảng điểm Excel

**Response 200 OK**: file `.xlsx` với `Content-Type` là
`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` và tên file
`bang-diem-{course_id}.xlsx`.

Sheet `Bảng điểm` gồm MSSV, họ tên, lớp, điểm từng bài, tổng từng buổi và điểm
tổng. Số liệu được tính cùng quy tắc với bảng điểm trên UI: điểm tay được ưu
tiên, bài chưa nộp hiển thị 0 khi tính tổng; các tổng được làm tròn 1 chữ số.
MSSV được xuất dạng text để giữ số 0 ở đầu. Các chuỗi bắt đầu bằng `=`, `+`,
`-`, hoặc `@` được escape trước khi ghi vào workbook để tránh Excel formula
injection.

**Yêu cầu quyền**: Admin (xem mọi lớp) hoặc Teacher là chủ lớp. Endpoint chỉ đọc dữ liệu và
không tạo hoặc thay đổi bảng/cột database.
