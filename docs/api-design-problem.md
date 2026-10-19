# Thiết kế API — Quản lý bài tập (Problem)

## Quy ước

- `lesson_id = null` biểu thị Problem nằm trong bank; Problem khác gắn trực tiếp vào Lesson.
- Problem trong bank là nguồn dùng chung, chưa thuộc Course nào. Khi thêm vào Lesson, hệ thống tạo một Problem mới cho Lesson; không đổi `lesson_id` của bản nguồn.
- Chưa có `created_by` cho Problem, Topic, archive hoặc Assignment snapshot.
- Problem gắn Lesson chỉ được quản lý bởi Admin hoặc Teacher chủ Course.
- Datetime request phải kèm UTC offset; response dùng giờ Việt Nam với offset `+07:00`. `start_datetime` mở đề; `end_datetime` chỉ chặn Submit và không chặn xem đề.

## POST /problems — Tạo Problem trong bank

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| title | string | có | 1–255 ký tự; trim; không được rỗng |
| function_name | string | có | Tên hàm hợp lệ dùng để gọi lời giải, ví dụ `twoSum` |
| description | string | có | Nội dung đề |
| constraints | string | có | Ràng buộc |
| level | string | có | Chỉ `easy`, `medium`, `hard` |
| time_limit_seconds | int | có | >= 1 |
| starter_codes | object | có | Phải có code không rỗng cho `python`, `c`, `cpp`, `java`; Python là ngôn ngữ chấm ban đầu |
| start_datetime | datetime | có | Phải có UTC offset; quyết định lúc mở đề |
| end_datetime | datetime | có | Phải có UTC offset; chỉ là hạn Submit; phải sau start |
| hint | string \| null | không | |
| complexity | string \| null | không | |
| testcases | array | có | Ít nhất 1 testcase; `input` là mảng đối số JSON theo thứ tự tham số, `expected_output` là giá trị JSON; `is_sample` mặc định `false` |

Với Python, hợp đồng runner là gọi method có tên `function_name` trên `Solution`, truyền các phần tử của `input` theo thứ tự và so sánh giá trị trả về với `expected_output` (ví dụ `Solution().twoSum(*input)`). Ví dụ testcase: `input: [[2, 7, 11, 15], 9]`, `expected_output: [0, 1]`. Các template C/C++/Java cũng có function cùng tên; giai đoạn đầu chỉ Python được chấm.

`function_name` là metadata để runner biết điểm vào cần gọi; nó không mô tả kiểu tham số hay kiểu trả về. Thứ tự và cấu trúc tham số nằm trong mảng `input`, còn chữ ký đầy đủ thể hiện trong `starter_codes`. Tên phải là identifier ASCII dùng được trong Python, C/C++ và Java.

### Lưu trữ trong database

- `problem.function_name`: tên method/function runner gọi. Cột nullable để giữ nguyên Problem cũ theo stdin/stdout; API tạo Problem mới bắt buộc có tên này. Không thể tự suy ra tên hàm của dữ liệu cũ một cách an toàn.
- Problem cũ có `function_name = null` hoặc testcase stdin/stdout không tương thích với runner function-call. Trước khi bật chấm cho các bản ghi này, cần chuyển đổi có chủ đích hoặc từ chối chấm; không tự suy luận chữ ký hàm.
- `problem.starter_codes`: cột JSON ánh xạ ngôn ngữ sang template. Migration khởi tạo bản ghi cũ bằng `{"python": start_format_code}`; các template C/C++/Java chỉ bắt buộc khi tạo Problem mới.
- `problem.start_format_code`: cột Python legacy được giữ đồng bộ với `starter_codes.python` để các màn hình và client cũ tiếp tục hoạt động.
- `testcase.input` và `testcase.expected_output`: vẫn dùng cột text hiện có; testcase theo hợp đồng mới được JSON-serialize và đánh dấu bằng `input_type=json_args`, `expected_output_type=json`. Bản ghi stdin/stdout cũ giữ nguyên chuỗi và marker cũ.

**Response 201 Created**: `ProblemDetailResponse`; `lesson_id`, `course_id`, `code` trả null. `starter_codes` trả code theo ngôn ngữ; `starter_code` vẫn trả template Python để tương thích các màn hình cũ.

**Response lỗi**

| Status | Khi nào |
|---|---|
| 403 | Người gọi không phải Admin/Teacher |
| 422 | Field sai định dạng, level ngoài tập cho phép, hoặc lịch không hợp lệ |

## GET /problems — Tìm kiếm Problem

**Query parameters**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| q | string | không | Tìm trong title |
| level | string | không | `easy`, `medium`, `hard` |
| course_id | string | không | Giới hạn Problem thuộc Course |
| page | int | không | Mặc định 1, >= 1 |
| page_size | int | không | Mặc định 20, từ 1 đến 100 |

Teacher thấy tất cả Problem trong bank và Problem thuộc Course mình tạo; Admin thấy tất cả Problem. Khi không truyền `course_id`, danh sách của Teacher gồm cả bank và các bài thuộc Course của mình. Nếu truyền `course_id`, kết quả chỉ gồm Problem đã gắn vào Lesson của Course đó, không gồm bài bank vì bài bank chưa thuộc Course. `course_id` là bộ lọc, không phải field của Problem list item. Response gồm `items`, `total`, `page`, `page_size`; item có id, code (`report`), title, level, `lesson_id` (null với bài bank) và tổng testcase.

**Response lỗi**: 403 không phải Admin/Teacher; 422 query sai kiểu/giới hạn hoặc level không hợp lệ.

## GET /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id} — Chi tiết Problem

**Response 200 OK**: `ProblemDetailResponse`.

Student chỉ xem Problem từ `start_datetime` trở đi và chỉ nhận testcase mẫu. Sau `end_datetime`, Student vẫn xem được đề. Admin/Teacher có quyền Course nhận toàn bộ testcase.

**Response lỗi**: 403 không có quyền xem Course; 404 Problem không tồn tại/không thuộc Lesson hoặc chưa mở với Student.

## PATCH /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id} — Cập nhật Problem

**Request body** (mọi field optional):

| Field | Kiểu | Ghi chú |
|---|---|---|
| title | string \| null | 1–255 ký tự; null bỏ qua |
| function_name | string \| null | Tên hàm mới; khi đổi phải gửi lại toàn bộ `starter_codes` |
| description, constraints | string \| null | null bỏ qua |
| level | string \| null | `easy`, `medium`, `hard`; null bỏ qua |
| hint, complexity, report | string \| null | Có thể xóa bằng null |
| time_limit_seconds | int \| null | Nếu gửi phải >= 1 |
| start_datetime, end_datetime | datetime \| null | Nếu đổi một field, cặp thời gian mới phải hợp lệ |
| starter_codes | object \| null | Nếu gửi phải có code không rỗng cho `python`, `c`, `cpp`, `java`; null bỏ qua |
| testcases | array \| null | Nếu gửi, phải có ít nhất 1 testcase JSON và thay toàn bộ danh sách; null bỏ qua |

Nếu thay đổi lịch: datetime phải có UTC offset và `start_datetime < end_datetime`. Không áp giới hạn tương lai hoặc khoảng cách tối đa. Khi Problem đã có Submission, thay đổi testcase, `function_name`, starter code hoặc `time_limit_seconds` bị chặn với 409 để giữ nguyên hợp đồng chấm lịch sử. Không thể xóa testcase cuối cùng.

**Response 200 OK**: `ProblemDetailResponse`.

**Response lỗi**: 403 không có quyền; 404 Problem không thuộc Lesson; 409 đã có Submission khi thay testcase hoặc metadata ảnh hưởng đến chấm; 422 field/lịch không hợp lệ.

## DELETE /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id} — Xóa Problem

**Response**: `204 No Content`.

Xóa Problem và testcase của bản gắn Lesson; không xóa Problem nguồn trong bank. Bị chặn với 409 nếu đã có Submission. Lỗi khác: 403 không có quyền; 404 Problem không thuộc Lesson.

## Chưa triển khai

Không có route đọc chi tiết, sửa hoặc xóa riêng Problem bank. Testcase ban đầu được gửi cùng `POST /problems`; các route sửa/quản lý testcase hiện chỉ hỗ trợ Problem đã gắn vào Lesson. Chưa có archive, import workbook, Topic hoặc mã bài unique. `report` là code tùy chọn hiện có, không có ràng buộc unique. Starter code được lưu cho Python, C, C++ và Java; ban đầu chỉ Python được chấm. API và dữ liệu đã có function name cùng testcase JSON; runner Python gọi method/harness là phần tiếp theo.
