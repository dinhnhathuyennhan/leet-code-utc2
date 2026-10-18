# Thiết kế API — Quản lý buổi học (Lesson)

## Quy ước

- Lesson chứa trực tiếp Problem qua `Problem.lesson_id`; chưa có LessonAssignment hoặc snapshot.
- Problem bank (`lesson_id = null`) chưa thuộc Course/Lesson và không xuất hiện trong dữ liệu Lesson/Course cho tới khi được sao chép vào Lesson.
- Admin có thể quản lý mọi Course; Teacher chỉ quản lý Course mình tạo.
- Student xem Lesson khi có quyền xem Course; dữ liệu testcase ẩn và thống kê được lọc khỏi response.

## POST /courses/{course_id}/lessons — Tạo buổi học

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| lesson_name | string | có | 1–255 ký tự; trim khoảng trắng; không được rỗng |
| start_date | date | có | phải trước hoặc bằng `end_date` |
| end_date | date | có | phải sau hoặc bằng `start_date` |
| problem_ids | int[] | không | mặc định `[]`; Problem bank hoặc Problem từ Lesson khác được sao chép thành bản riêng cho Lesson đích, kèm testcase |

`lesson_number` do server gán tiếp theo thứ tự hiện tại.

**Response 201 Created**: `CourseResponse`.

**Response lỗi**

| Status | Khi nào |
|---|---|
| 403 | Không có quyền tạo/sửa Lesson trong Course |
| 404 | Course hoặc Problem được chỉ định không tồn tại |
| 422 | Body sai định dạng, tên rỗng hoặc ngày không hợp lệ |

## GET /courses/{course_id}/lessons/{lesson_id} — Chi tiết buổi học

**Response 200 OK**: `LessonDetailResponse`, gồm thông tin Lesson, thống kê và exercises. Mỗi exercise trả `function_name`, testcase JSON (`input` là mảng đối số, `expected_output` là giá trị), `starter_codes` theo các khóa `python`, `c`, `cpp`, `java`; trường `starter_code` tiếp tục giữ template Python để tương thích.

**Quy tắc theo vai trò**

- Admin/Teacher có quyền xem Course nhận tất cả Problem/testcase và trường thống kê.
- Student chỉ nhận Problem đã tới `start_datetime`, testcase mẫu; các trường `submitted_students`, `total_students`, `stats`, `alert` và `submitted_count` được trả về là `null`.
- Thống kê dành cho Admin/Teacher chỉ tính các Student hiện đang enroll trong Course; bài nộp của Student đã bị gỡ enrollment không được tính.

**Response lỗi**

| Status | Khi nào |
|---|---|
| 403 | Không có quyền xem Course |
| 404 | Course hoặc Lesson không tồn tại/không thuộc Course |

## PATCH /courses/{course_id}/lessons/{lesson_id} — Cập nhật buổi học

**Request body** (mọi field optional)

| Field | Kiểu | Ghi chú |
|---|---|---|
| lesson_name | string \| null | 1–255 ký tự; null bị bỏ qua |
| start_date | date \| null | null bị bỏ qua |
| end_date | date \| null | null bị bỏ qua |
| problem_ids | int[] \| null | Chỉ thêm bài; không thay thế danh sách. Problem bank hoặc từ Lesson khác được sao chép cùng testcase; nguồn không đổi |

**Response 200 OK**: `CourseResponse`.

**Response lỗi**: 403 không có quyền; 404 Course/Lesson/Problem không tồn tại; 422 dữ liệu hoặc khoảng ngày không hợp lệ.

## POST /courses/{course_id}/lessons/{lesson_id}/problems — Gắn Problem vào buổi

**Request body**: `{ "problem_ids": [1, 2] }`; danh sách không được rỗng.

Problem bank được dùng chung và không bị chuyển khỏi bank. Khi thêm Problem bank, hệ thống tạo bản sao với `problem_id` mới, `lesson_id` là Lesson đích, sao chép testcase và giữ `report`; `start_datetime`/`end_datetime` của bản sao được đặt theo ngày bắt đầu/kết thúc của Lesson đích. Problem thuộc Lesson khác cũng được sao chép; Teacher chỉ được sao chép nếu sở hữu Course nguồn, Admin được sao chép mọi Problem. Submission không được sao chép. Problem đã nằm trong chính Lesson đích được giữ nguyên.

**Response 200 OK**: `CourseResponse`.

**Response lỗi**: 403 không có quyền; 404 Problem không tồn tại; 422 danh sách rỗng/sai định dạng.

## PATCH /courses/{course_id}/lessons/reorder — Sắp xếp buổi học

**Request body**: `{ "order": [<lesson_id>, ...] }`.

Danh sách phải chứa tất cả Lesson thuộc Course đúng một lần. Server gán `lesson_number` bắt đầu từ 1 theo thứ tự gửi.

**Response 200 OK**: `CourseResponse`.

**Response lỗi**: 403 không có quyền; 422 danh sách ID thiếu, thừa hoặc trùng.

## POST /courses/{course_id}/lessons/{lesson_id}/duplicate — Nhân bản buổi học

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| new_start_date | date | có | phải trước hoặc bằng `new_end_date` |
| new_end_date | date | có | phải sau hoặc bằng `new_start_date` |
| target_course_id | string \| null | không | mặc định Course nguồn; tối đa 50 ký tự |

Lesson mới giữ tên nguồn, được gán số thứ tự cuối danh sách; Problem/testcase được sao chép.

**Response 201 Created**: `CourseResponse` của Course đích.

**Response lỗi**: 403 không có quyền xem Course nguồn/quản lý Course đích; 404 Course/Lesson không tồn tại; 422 ngày không hợp lệ.

## DELETE /courses/{course_id}/lessons/{lesson_id} — Xóa buổi học

**Request body**: không có. **Response**: `204 No Content`.

Không thể xóa Lesson còn Problem (409). Ngoài ra trả 403 nếu không có quyền, 404 nếu Lesson không tồn tại.
