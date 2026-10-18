# Thiết kế API — Quản lý Testcase

## Quy ước

- Testcase thuộc trực tiếp Problem; chưa có AssignmentTestcase snapshot.
- Khi tạo Problem bank qua `POST /problems`, testcase ban đầu được gửi trong body và gắn với Problem có `lesson_id = null`.
- Base path: `/courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases` (ký hiệu `BASE`).
- Các thao tác ghi yêu cầu Admin hoặc Teacher chủ Course.
- Không cho thay testcase khi Problem đã có Submission.
- Testcase mới dùng `input` là mảng đối số JSON theo thứ tự tham số function; `expected_output` là giá trị JSON.
- Testcase được lưu và trả về dưới dạng JSON đã parse. Bản ghi cũ có `input_type=stdin`/`expected_output_type=stdout` vẫn được trả ở dạng chuỗi.

## GET /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases — Danh sách testcase

**Query**: `is_sample` (boolean, không bắt buộc).

Người dùng có quyền xem Course được gọi. Student luôn chỉ nhận testcase `is_sample=true`, bất kể filter gửi lên.

**Response 200 OK**

| Field | Kiểu | Ghi chú |
|---|---|---|
| testcases | array | Mỗi phần tử có id, input, expected_output, is_sample, input_type, expected_output_type |
| total_sample | int | Tổng testcase mẫu của Problem |
| total_hidden | int | Tổng testcase ẩn; hiện có trả cả cho Student |

**Response lỗi**: 403 không có quyền xem Course; 404 Problem không tồn tại/không thuộc Lesson hoặc chưa mở với Student.

## POST /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases — Thêm testcase

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| input | JSON array | có | Đối số truyền vào function theo đúng thứ tự; ví dụ `[[2, 7, 11, 15], 9]` |
| expected_output | JSON value | có | Giá trị function cần trả về; ví dụ `[0, 1]` |
| is_sample | boolean | không | Mặc định false |

**Response 200 OK**: `ProblemDetailResponse` sau khi thêm.

**Response lỗi**: 403 không có quyền; 404 Problem không hợp lệ; 409 Problem đã có Submission; 422 body sai định dạng.

## PATCH /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases/{testcase_id} — Cập nhật testcase

**Request body**: `input`, `expected_output`, `is_sample` optional; field không gửi được bỏ qua. `input` phải là JSON array; `expected_output` phải là giá trị JSON (gồm cả `null`).

**Response 200 OK**: `ProblemDetailResponse`.

**Response lỗi**: 403 không có quyền; 404 testcase không tồn tại/không thuộc Problem; 409 Problem đã có Submission; 422 body sai định dạng.

## DELETE /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases/{testcase_id} — Xóa testcase

**Response**: `204 No Content`.

**Response lỗi**: 403 không có quyền; 404 testcase không thuộc Problem; 409 Problem đã có Submission hoặc testcase cần xóa là testcase cuối cùng.

## PATCH /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases/batch — Đổi trạng thái mẫu hàng loạt

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| testcase_ids | int[] | có | Không được rỗng; mọi ID phải thuộc Problem |
| is_sample | boolean | có | Trạng thái mới |

**Response 200 OK**: `ProblemDetailResponse`.

**Response lỗi**: 403 không có quyền; 404 một hoặc nhiều testcase không thuộc Problem; 409 Problem đã có Submission; 422 danh sách rỗng/sai định dạng.

## POST /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases/preview — Kiểm tra payload

**Request body**: `{ "testcases": [...] }`; danh sách không được rỗng.

Không ghi database. Mỗi phần tử phải là object có `input` là JSON array và `expected_output` là giá trị JSON; `is_sample` nếu gửi phải là boolean.

**Response 200 OK**: `valid`, `count`, `sample_count`, `hidden_count`, `errors` (index 1-based và message), `warnings`.

**Response lỗi**: 403 không phải Admin/Teacher; 422 payload rỗng/sai cấu trúc cấp ngoài.

## GET /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases/download — Tải testcase

**Query**: `format` là `json` (mặc định) hoặc `zip`.

Admin/Teacher chủ Course tải toàn bộ testcase, gồm input/output testcase ẩn. ZIP chứa một file JSON.

**Response 200 OK**: file JSON hoặc ZIP, `Content-Disposition` đặt tên `testcases_{problem_id}.{format}`.

**Response lỗi**: 403 không có quyền; 404 Problem không hợp lệ; 422 format ngoài `json`, `zip`.

## POST /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/testcases/upload — Thay toàn bộ testcase từ file

File upload JSON hoặc ZIP chứa JSON; tối đa 5 MB, phần ZIP giải nén tối đa 20 MB. Testcase mới cần `input` là JSON array và `expected_output` là giá trị JSON; `is_sample` nếu có phải là boolean. File export của testcase legacy stdin/stdout có thể upload lại và giữ nguyên marker/chuỗi legacy. Payload rỗng hoặc sai định dạng bị từ chối. Thay đổi bị chặn khi Problem đã có Submission.

**Response 200 OK**: `ProblemDetailResponse`.

**Response lỗi**: 403 không có quyền; 404 Problem không hợp lệ; 409 đã có Submission; 422 file/payload sai hoặc vượt giới hạn.

Các route theo `BASE` chỉ quản lý testcase của Problem đã gắn Lesson. Problem bank không có route riêng để đọc hoặc sửa testcase sau khi tạo; khi bank Problem được thêm vào Lesson, các testcase của nó được sao chép cùng Problem và sau đó có thể quản lý trên bản Lesson qua `BASE`.
