# Thiết kế API — Quản lý bài tập (Problem)

## Quy ước

- `lesson_id = null` biểu thị Problem nằm trong bank; Problem khác gắn trực tiếp vào Lesson.
- Problem trong bank là nguồn dùng chung, chưa thuộc Course nào. Khi thêm vào Lesson, hệ thống tạo một Problem mới cho Lesson; không đổi `lesson_id` của bản nguồn.
- Chưa có `created_by` cho Problem, Topic, archive hoặc Assignment snapshot.
- Problem gắn Lesson chỉ được quản lý bởi Admin hoặc Teacher chủ Course.
- **Ngân hàng bài chỉ Admin được ghi**: tạo (`POST /problems`), import (`POST /problems/import`, `/import/preview`), sửa (`PATCH /problems/{problem_id}`) và xoá (`DELETE /problems/{problem_id}`) bài bank đều yêu cầu Admin. Teacher chỉ xem/tìm bài bank (`GET /problems`, `GET /problems/{problem_id}`), sao chép bài vào Lesson (`POST /courses/{course_id}/lessons/{lesson_id}/problems`) hoặc tạo bài mới thẳng trong Lesson (`POST /courses/{course_id}/lessons/{lesson_id}/problems/new`).
- Datetime request phải kèm UTC offset; response dùng giờ Việt Nam với offset `+07:00`. `start_datetime` mở đề; `end_datetime` chỉ chặn Submit và không chặn xem đề.
- Với Problem đã gắn Lesson, lịch được suy ra từ `Lesson.start_date`/`end_date`; không chỉnh lịch riêng trên Problem. Khi ngày Lesson thay đổi, các Problem thuộc Lesson được đồng bộ về đầu ngày bắt đầu và cuối ngày kết thúc theo giờ Việt Nam.
- Mỗi Problem chỉ có một cách chấm, suy ra từ `function_name`: có tên thì chấm function-call (harness), `null` thì chấm stdin/stdout. `function_name` không đổi được sau khi tạo bài.
- Ngôn ngữ hỗ trợ: `python`, `javascript`, `c`, `cpp`, `java`. Go đã bị loại bỏ khỏi hệ thống.
- **Lưu ý khi soạn testcase** (rút ra từ review production `1.0.0-rc.1`):
  - Đầu vào là dict có **khoá dạng số** (vd `{"FIRST_NAME": ..., "1": 35}`): JavaScript luôn đưa khoá số lên đầu object, nên lời giải phụ thuộc thứ tự khoá cho kết quả khác Python (đã gặp ở HumanEval/95, test #36). Tránh testcase phụ thuộc thứ tự khoá, hoặc chỉ cho phép Python với đề đó.
  - Bộ testcase phải phân biệt được lời giải sai. Cảnh báo "N testcase có cùng expected_output" của `POST .../testcases/preview` là dấu hiệu bộ test yếu (HumanEval/163 có 37/50 test cùng kết quả `[]`, lời giải sai vẫn qua 20/50).

## POST /problems — Tạo Problem trong bank

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| title | string | có | 1–255 ký tự; trim; không được rỗng |
| report | string \| null | không | Mã bài tùy chọn; được lưu trong `problem.report` và trả về qua field `code` |
| function_name | string \| null | không | Có tên thì chấm function-call (harness); bỏ hoặc đặt `null` để chấm stdin/stdout. Không thể đổi sau khi tạo bài |
| description | string | có | Nội dung đề |
| constraints | string | có | Ràng buộc |
| level | string | có | Chỉ `easy`, `medium`, `hard` |
| time_limit_seconds | int | có | >= 1 |
| starter_codes | object | không | Code khởi tạo theo ngôn ngữ. Function-call: bắt buộc Python và JavaScript; C/C++ tùy chọn, chỉ nhận khi dựng được harness từ starter; không nhận Java. stdin/stdout: không bắt buộc, nhận cả 5 ngôn ngữ (gồm Java), có thể để trống |
| start_datetime | datetime | có | Phải có UTC offset; quyết định lúc mở đề |
| end_datetime | datetime | có | Phải có UTC offset; chỉ là hạn Submit; phải sau start |
| hint | string \| null | không | |
| complexity | string \| null | không | |
| testcases | array | có | Từ 10 đến 50 testcase tổng cộng, gồm ít nhất 3 mẫu (`is_sample=true`) và 5 hidden (`false`). Function-call: `input` là mảng đối số JSON, `expected_output` là giá trị JSON. stdin/stdout: cả hai là chuỗi |

Khi `function_name` có giá trị, runner gọi hàm/method cùng tên và so sánh kết quả JSON (số thực so sánh có dung sai, các kiểu còn lại so sánh chính xác; xem `api-design-testcase.md`). Function-call hỗ trợ Python và JavaScript (bắt buộc), C và C++ (tùy chọn); Java chỉ chạy ở stdin/stdout mode. Starter C/C++ dùng để suy ra chữ ký hàm: tham số tên `<tên mảng>Size` và con trỏ `returnSize` ở cuối được harness C tự xử lý và không tính là đối số JSON. Khi `function_name` bị bỏ hoặc là `null`, Judge0 nhận nguyên chuỗi testcase `input` làm stdin và kết quả stdout được so sánh sau khi trim khoảng trắng ở hai đầu.

`function_name` là metadata để runner biết điểm vào cần gọi; nó không mô tả kiểu tham số hay kiểu trả về. Thứ tự và cấu trúc tham số nằm trong mảng `input`, còn chữ ký đầy đủ thể hiện trong `starter_codes`. Tên phải là identifier ASCII hợp lệ.

### Lưu trữ trong database

- `problem.function_name`: tên method/function runner gọi; `null` chọn stdin/stdout mode. Cột nullable hỗ trợ cả dữ liệu cũ lẫn Problem mới. Giá trị không đổi sau khi tạo.
- `problem.starter_codes`: cột JSON ánh xạ ngôn ngữ sang template. Bài function-call chỉ lưu Python, JavaScript và C/C++ hợp lệ; template Java chỉ được dùng với stdin/stdout. Bài stdin/stdout có thể không có template nào.
- `problem.start_format_code`: cột Python legacy được giữ đồng bộ với `starter_codes.python` để các màn hình và client cũ tiếp tục hoạt động.
- `testcase.input` và `testcase.expected_output`: vẫn dùng cột text hiện có; testcase theo hợp đồng mới được JSON-serialize và đánh dấu bằng `input_type=json_args`, `expected_output_type=json`. Bản ghi stdin/stdout cũ giữ nguyên chuỗi và marker cũ.

**Response 201 Created**: `ProblemDetailResponse`; `lesson_id`, `course_id` trả null cho Problem mới; `code` phản ánh giá trị `report` nếu được gửi, nếu không sẽ null. `starter_codes` trả code theo ngôn ngữ; `starter_code` vẫn trả template Python để tương thích các màn hình cũ.

`ProblemDetailResponse` có thêm `supported_languages` (list ngôn ngữ chấm được) để client biết hiển thị lựa chọn nào:

- Bài stdin/stdout: đủ 5 ngôn ngữ (Python, JavaScript, C, C++, Java).
- Bài function-call: chỉ gồm ngôn ngữ nằm trong tập hỗ trợ harness và có starter hợp lệ. Ví dụ starter C++ không dựng được harness thì danh sách là `["python", "javascript"]` hoặc kèm `"c"`.

Run/Submit/Preview bằng ngôn ngữ ngoài `supported_languages` bị từ chối với `422 UNSUPPORTED_LANGUAGE`.

Admin preview nhận ngôn ngữ và code, chạy toàn bộ testcase đã lưu theo kiểu chấm
cố định của Problem (`function_name` có giá trị thì dùng function-call; `null`
thì dùng stdin/stdout). Preview không cho đổi kiểu chấm hoặc nhập cặp stdin/stdout
riêng cho một lần chạy.

## Quyền dùng AI review

- `POST /ai/review`: Admin, Teacher và Student đều được gọi để nhận review/gợi ý
  trên đoạn code tự do. Đây là review tham khảo, không thay đổi điểm hoặc
  Problem trong database.
- `POST /ai/review/{submission_id}`: chỉ Student được gọi cho bài nộp của chính
  mình sau khi đã đạt toàn bộ testcase.
- `POST /ai/problems/{problem_id}/review-preview`: Admin và Teacher được gọi sau
  khi đã chạy preview hợp lệ. Teacher chỉ được dùng với đề thư viện hoặc đề đã
  gắn trong Course do chính mình phụ trách.
- `GET /ai/test-connection`: chỉ Admin được gọi vì đây là thao tác kiểm tra cấu
  hình hệ thống, không cần hiển thị cho Teacher.

Trang chi tiết Problem bank của Teacher không cho sửa/xóa đề thư viện. Teacher
được xem nội dung, chạy toàn bộ testcase đã lưu và nhận AI review giống Admin;
với đề đã gắn lớp của mình, Teacher có thêm lối vào màn hình chỉnh sửa. Quyền
chỉnh sửa vẫn đi qua các endpoint Course/Lesson và bị từ chối nếu Course không
do Teacher đó phụ trách.

**Response lỗi**

| Status | Khi nào |
|---|---|
| 403 | Người gọi không phải Admin (Teacher cũng bị 403) |
| 422 | Field sai định dạng, level ngoài tập cho phép, hoặc lịch không hợp lệ |
| 422 | Bài function-call thiếu starter Python/JavaScript, có starter Java, hoặc starter C/C++ không dựng được harness |

## POST /courses/{course_id}/lessons/{lesson_id}/problems/new — Tạo Problem mới trong Lesson

Teacher (chủ Course) hoặc Admin tạo bài mới gắn thẳng vào Lesson, **không** tạo bản nào trong bank.

**Request body**: giống `POST /problems`. `start_datetime`/`end_datetime` vẫn phải hợp lệ nhưng bị bỏ qua: lịch bài lấy theo Lesson (00:00 ngày bắt đầu → 23:59:59 ngày kết thúc, giờ Việt Nam). `total_number_assignment` của Lesson được đếm lại.

**Response 201 Created**: `ProblemDetailResponse` với `lesson_id` là Lesson đích và `course_id` là Course.

**Response lỗi**: 403 không phải Admin/Teacher hoặc Teacher không phải chủ Course; 404 Course/Lesson không tồn tại hoặc Lesson không thuộc Course; 422 như `POST /problems`.

## POST /problems/import — Import nhiều Problem từ file JSON

Chỉ Admin gửi `multipart/form-data` với field `file`, file đuôi `.json`, tối đa 25 MB và 5.000 Problem mỗi lần. Nội dung chấp nhận một object Problem, một mảng Problem, hoặc object bọc `{ "problems": [...] }`. Mỗi Problem dùng cùng các field và validation như `POST /problems`. Có `function_name` thì testcase dùng mảng đối số/output JSON; bỏ hoặc đặt `function_name: null` thì testcase dùng chuỗi stdin/stdout. `report` tùy chọn được lưu trên Problem và trả qua field `code`; trường này không yêu cầu duy nhất.

Với bài function-call, starter C/C++ được validate trực tiếp bằng harness. Nếu không dựng được, preview báo lỗi ở field tương ứng và chặn import; hệ thống không tự xóa starter. Bài thiếu starter Python hoặc JavaScript cũng bị báo lỗi.

Trước khi ghi database, hệ thống parse và validate toàn bộ file, đồng thời so nội dung chuẩn hóa với các Problem nguồn trong bank và các Problem khác trong cùng file. Nội dung được chuẩn hóa theo Unicode, chữ hoa/thường và khoảng trắng trên tên, tên hàm, mô tả và ràng buộc. Problem trùng không được import. Có thể gọi `POST /problems/import/preview` trước để xem số bài/testcase và lỗi validation hoặc trùng nội dung. Sau đó toàn bộ Problem và testcase được tạo trong cùng một transaction; lỗi validation, trùng nội dung hoặc lỗi ghi dữ liệu sẽ không giữ lại bản ghi nào của file. Lỗi trả `422` kèm số thứ tự Problem và field đầu tiên bị lỗi.

### POST /problems/import/preview — Kiểm tra file trước khi import

Nhận cùng `multipart/form-data` như route import, nhưng không ghi database. Trả `valid`, tổng/đếm bài hợp lệ, tổng testcase (mẫu/hidden) và lỗi theo từng bài, bao gồm vị trí Problem bị lặp trong file hoặc trùng với bài nguồn đã có trong bank. Client chỉ nên bật bước xác nhận import khi `valid=true`.

**Response 201 Created**

```json
{
  "created_count": 1,
  "problems": [
    { "id": 42, "code": "TEAM-001", "title": "Sum Two Numbers", "total_number_testcase": 10 }
  ]
}
```

**Response lỗi**: `403` nếu không phải Admin (kể cả Teacher); `422` nếu phần mở rộng, kích thước, cấu trúc JSON, dữ liệu Problem không hợp lệ hoặc nội dung trùng trong file/Problem bank. Đây là kiểm tra ứng dụng; không có ràng buộc unique ở database trong giai đoạn này. Phần diễn đạt khác nhau nhưng cùng ý nghĩa vẫn cần người quản trị review.

## GET /problems — Tìm kiếm Problem

**Query parameters**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| q | string | không | Tìm không phân biệt hoa thường trong title hoặc mã bài (`report`, trả ra dưới tên `code`) |
| level | string | không | `easy`, `medium`, `hard` |
| grading_mode | string | không | `harness` để lọc bài function-call (`function_name` có giá trị); `stdin_stdout` để lọc bài stdin/stdout (`function_name = null`) |
| course_id | string | không | Giới hạn Problem thuộc Course |
| bank_only | bool | không | Mặc định `false`. `true` chỉ lấy bài trong bank (`lesson_id = null`) |
| has_testcases | bool | không | Mặc định `false`. `true` chỉ lấy bài có ít nhất một testcase (bài gắn được vào Lesson) |
| page | int | không | Mặc định 1, >= 1 |
| page_size | int | không | Mặc định 20, từ 1 đến 100 |

Teacher thấy tất cả Problem trong bank và Problem thuộc Course mình tạo; Admin thấy tất cả Problem. Khi không truyền `course_id`, danh sách của Teacher gồm cả bank và các bài thuộc Course của mình. Nếu truyền `course_id`, kết quả chỉ gồm Problem đã gắn vào Lesson của Course đó, không gồm bài bank vì bài bank chưa thuộc Course. `course_id` là bộ lọc, không phải field của Problem list item. Response gồm `items`, `total`, `page`, `page_size`; item có id, `code` (giá trị `report`, null nếu chưa đặt), title, level, `lesson_id` (null với bài bank), tổng testcase và `grading_mode` (`harness` khi có `function_name`, ngược lại `stdin_stdout`).

Các bộ lọc được áp dụng ở DB trước khi phân trang nên `total` luôn khớp với danh sách đã lọc. Màn tạo/sửa buổi học dùng `bank_only=true&has_testcases=true` cho nhóm "Ngân hàng bài" và `course_id=<course>` cho nhóm "Bài trong lớp học này", tải thêm trang kế tiếp khi cuộn tới cuối danh sách.

**Response lỗi**: 403 không phải Admin/Teacher; 422 query sai kiểu/giới hạn, level hoặc `grading_mode` không hợp lệ.

## GET /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id} — Chi tiết Problem

**Response 200 OK**: `ProblemDetailResponse` (gồm `supported_languages`).

Student chỉ xem Problem từ `start_datetime` trở đi và chỉ nhận testcase mẫu. Sau `end_datetime`, Student vẫn xem được đề. Admin/Teacher có quyền Course nhận toàn bộ testcase.

**Response lỗi**: 403 không có quyền xem Course; 404 Problem không tồn tại/không thuộc Lesson hoặc chưa mở với Student.

## PATCH /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id} — Cập nhật Problem

**Request body** (mọi field optional):

| Field | Kiểu | Ghi chú |
|---|---|---|
| title | string \| null | 1–255 ký tự; null bỏ qua |
| function_name | string \| null | Không thể đổi sau khi tạo bài: gửi giá trị khác `function_name` hiện tại (kể cả `null`) trả 409; gửi lại đúng giá trị hiện tại được chấp nhận |
| description, constraints | string \| null | null bỏ qua |
| level | string \| null | `easy`, `medium`, `hard`; null bỏ qua |
| hint, complexity, report | string \| null | Có thể xóa bằng null; `report` được trả dưới tên `code` |
| time_limit_seconds | int \| null | Nếu gửi phải >= 1 |
| start_datetime, end_datetime | datetime \| null | Với Problem thuộc Lesson, các giá trị này không được áp dụng; lịch lấy theo Lesson |
| starter_codes | object \| null | Ngôn ngữ hợp lệ: Python, C, C++, Java, JavaScript. Bài function-call: bắt buộc Python và JavaScript, C/C++ tùy chọn và phải dựng được harness, không nhận Java. Bài stdin/stdout: không bắt buộc, nhận cả 5 |
| testcases | array \| null | Nếu gửi, phải có 10–50 testcase theo grading mode, ít nhất 3 mẫu và 5 hidden; thay toàn bộ danh sách; null bỏ qua |

Muốn đổi cách chấm (function-call ⇄ stdin/stdout) phải tạo Problem mới, vì `function_name` không đổi được. Các field lịch trên endpoint này được bỏ qua; muốn đổi thời gian mở/đóng bài phải cập nhật ngày của Lesson. Khi Problem đã có Submission, thay đổi testcase, starter code hoặc `time_limit_seconds` bị chặn với 409 để giữ nguyên hợp đồng chấm lịch sử.

**Response 200 OK**: `ProblemDetailResponse`.

**Response lỗi**: 403 không có quyền; 404 Problem không thuộc Lesson; 409 đổi `function_name`, hoặc đã có Submission khi thay testcase/metadata ảnh hưởng đến chấm; 422 field không hợp lệ, starter code không đạt yêu cầu của cách chấm, hoặc testcase dưới/trên giới hạn.

## DELETE /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id} — Xóa Problem

**Response**: `204 No Content`.

Xóa Problem và testcase của bản gắn Lesson; không xóa Problem nguồn trong bank. Bị chặn với 409 nếu đã có Submission. Lỗi khác: 403 không có quyền; 404 Problem không thuộc Lesson.

## Chưa triển khai

Không có archive, import workbook hoặc Topic. `report` là mã bài tùy chọn, không có ràng buộc unique; API trả field này với tên `code`. Phát hiện trùng khi import dựa trên tên/mô tả/tên hàm/ràng buộc đã chuẩn hóa, không thể nhận ra mọi trường hợp diễn đạt khác nhau nhưng cùng ý nghĩa. Function-call runner hỗ trợ Python và JavaScript (bắt buộc), C và C++ (tùy chọn); stdin/stdout runner hỗ trợ cả năm ngôn ngữ, gồm Java.
