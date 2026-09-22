# Thiết kế API — Quản lý lớp học (Course)

## POST /courses — Tạo lớp học

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| course_id | string | có | mã lớp học, duy nhất |
| course_name | string | có | |
| term | string | có | học kỳ |
| start_date | datetime | có | phải trước `end_date` |
| end_date | datetime | có | |
| avt_link | string | không | |

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
| 422 | Thiếu field / `start_date` không trước `end_date` (use-case bước 5a) | (chi tiết lỗi field) |
| 400 | `course_id` đã tồn tại (use-case bước 6a) | `{"detail": "Mã lớp học đã tồn tại"}` |

**Quy tắc nghiệp vụ**

- `created_by` luôn set = `user_id` của người đang đăng nhập, không nhận từ client.
- `total_number_student` luôn khởi tạo = 0, không nhận từ client.
- **Yêu cầu quyền**: Admin hoặc Teacher (`require_role(Role.ADMIN, Role.TEACHER)`).

## GET /courses — Danh sách lớp học

**Response 200 OK**: mảng object giống response của `POST /courses`.

**Quy tắc nghiệp vụ**

- Kết quả tự động scope theo vai trò người gọi: Admin thấy toàn bộ lớp học; Teacher chỉ thấy lớp có `created_by = user_id` của chính mình; Student chỉ thấy lớp mình có `Enrollment`.
- **Yêu cầu quyền**: Bearer token hợp lệ (bất kỳ role nào).

## GET /courses/{course_id} — Chi tiết lớp học

**Response 200 OK**: object giống response của `POST /courses`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `course_id` không tồn tại | `{"detail": "Không tìm thấy lớp học"}` |
| 403 | Teacher không phải chủ lớp, hoặc Student chưa được thêm vào lớp (use-case "Xem danh sách sinh viên" bước 2a/2b) | `{"detail": "Bạn không có quyền xem lớp học này"}` |

**Quy tắc nghiệp vụ**

- Cùng quy tắc scope như `GET /courses`, áp dụng cho 1 lớp cụ thể.
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi truy cập theo vai trò.

## PATCH /courses/{course_id} — Cập nhật lớp học

**Request body** (tất cả optional, chỉ cập nhật field được truyền)

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| course_name | string | không | |
| term | string | không | |
| start_date | datetime | không | |
| end_date | datetime | không | |
| avt_link | string | không | |

**Response 200 OK**: object giống response của `POST /courses`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `course_id` không tồn tại | `{"detail": "Không tìm thấy lớp học"}` |
| 403 | Teacher không phải chủ lớp | `{"detail": "Bạn không có quyền thực hiện hành động này"}` |
| 422 | Sai định dạng field | (chi tiết lỗi field) |

**Quy tắc nghiệp vụ**

- Không cho sửa `course_id`, `created_by`, `total_number_student` qua endpoint này.
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp (`created_by == current_user.user_id`).

## POST /courses/{course_id}/enrollments — Thêm sinh viên vào lớp

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| student_id | string | có | `user_id` của Sinh viên |

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| enrollment_id | int | |
| course_id | string | |
| student_id | string | |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `course_id` không tồn tại, hoặc `student_id` không tồn tại/không phải Sinh viên (use-case bước 4a) | `{"detail": "Không tìm thấy sinh viên"}` |
| 403 | Teacher không phải chủ lớp (use-case bước 3a) | `{"detail": "Bạn không có quyền thêm sinh viên vào lớp này"}` |
| 409 | Sinh viên đã có trong lớp học (use-case bước 5a) | `{"detail": "Sinh viên đã có trong lớp học"}` |

**Quy tắc nghiệp vụ**

- Sau khi thêm thành công, `total_number_student` của lớp học tăng lên 1.
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

## GET /courses/{course_id}/enrollments — Danh sách sinh viên trong lớp

**Response 200 OK**

| Field | Kiểu | Ghi chú |
|---|---|---|
| (mảng object) | | mỗi phần tử: `enrollment_id`, `student_id`, `full_name`, `email` |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `course_id` không tồn tại | `{"detail": "Không tìm thấy lớp học"}` |
| 403 | Teacher không phải chủ lớp, hoặc Student không thuộc lớp này (use-case bước 2a/2b) | `{"detail": "Bạn không có quyền xem lớp học này"}` |

**Quy tắc nghiệp vụ**

- Admin và Teacher chủ lớp thấy toàn bộ danh sách; Student chỉ gọi được cho chính lớp mình đã được thêm vào.
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi truy cập theo vai trò.

## DELETE /courses/{course_id}/enrollments/{student_id} — Xoá sinh viên khỏi lớp

**Request body**: không có

**Response**: `204 No Content`

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `course_id` không tồn tại, hoặc `student_id` không có `Enrollment` trong lớp này (use-case bước 5a) | `{"detail": "Sinh viên không thuộc lớp học này"}` |
| 403 | Teacher không phải chủ lớp (use-case bước 4a) | `{"detail": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Sau khi xoá thành công, `total_number_student` của lớp học giảm đi 1.
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.
