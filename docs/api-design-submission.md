# Thiết kế API — Bài nộp (Submission)

## Quy ước

- Submission hiện tham chiếu trực tiếp Problem, Student và testcase của Problem.
- Các màn hình Admin/Teacher hiện truy vấn Submission qua Problem → Lesson → Course; vì vậy Problem bank (`lesson_id = null`) không thuộc phạm vi các danh sách/chi tiết Submission này. Khi thêm bài bank vào Lesson, hệ thống tạo Problem bản sao với `problem_id` riêng; Submission cũ không được sao chép.
- Router này chỉ cung cấp chức năng quản lý bài nộp cho Admin/Teacher.
- Teacher chỉ xem và xử lý bài thuộc Course mình tạo; Admin xem toàn bộ.
- Sinh viên nộp bài qua `POST /courses/{course_id}/lessons/{lesson_id}/problems/{problem_id}/submissions` (xem api-design-problem.md); bài được chấm bất đồng bộ qua Judge0.

## GET /submissions/pending — Danh sách bài cần xử lý

**Query parameters**

| Field | Kiểu | Bắt buộc | Mặc định | Ghi chú |
|---|---|---|---|---|
| filter | string | không | `all` | `error` chỉ lọc compile_error; `late_appeal`, `similarity` chưa có dữ liệu riêng |
| search | string \| null | không | null | Tìm theo mã/tên Student, Course hoặc Problem |
| limit | int | không | 100 | Từ 1 đến 500 |

Danh sách gồm Submission status `pending`, `wrong_answer`, `compile_error`.

**Response 200 OK**: `PendingSubmissionListResponse` gồm `items`, `total`, `counts`. `counts` được tính sau khi giới hạn theo quyền và `search`, nhưng trước khi áp dụng `filter`; `all` là tổng bài cần xử lý khớp tìm kiếm, `error` là số `compile_error`. `late_appeal` và `similarity` hiện bằng 0 vì chưa có dữ liệu riêng.

**Response lỗi**: 403 người gọi không phải Admin/Teacher; 422 query sai kiểu hoặc limit ngoài giới hạn.

## GET /submissions/{submission_id} — Chi tiết bài nộp

**Response 200 OK**: `SubmissionDetailResponse`, gồm thông tin Student/Course/Lesson/Problem, code, language, status, compile_output, feedback, passed_count, tổng testcase, submitted_datetime và testcase. Function-call testcase trả input là mảng đối số và output JSON; stdin/stdout testcase trả cả input và output dạng chuỗi.

Mỗi phần tử `testcases` có thêm `status` và `time`: kết quả chấm **thật** của testcase đó (`accepted`, `wrong_answer`, `runtime_error`, `time_limit_exceeded`, `compile_error`, `internal_error`, `skipped`). `status = null` với bài nộp chấm trước khi hệ thống lưu kết quả từng test; khi đó giao diện chỉ hiện tổng `passed_count/total_testcases`, không suy ra đúng/sai từng test theo thứ tự.

Trường `testcase_results` (danh sách `{index, is_sample, status, time}`, theo thứ tự testcase, **không kèm dữ liệu test**) có cùng ý nghĩa và là trường dùng chung với API của sinh viên. Danh sách rỗng khi bài chưa có kết quả từng test hoặc testcase của đề đã đổi sau khi chấm.

`time` của test `time_limit_exceeded` là giới hạn wall time đã áp dụng (Judge0 chỉ trả thời gian CPU gần 0 khi dừng vì wall clock).

**Response lỗi**

| Status | Khi nào |
|---|---|
| 403 | Người gọi không phải Admin/Teacher |
| 404 | Submission không tồn tại hoặc nằm ngoài phạm vi Teacher |

## PATCH /submissions/{submission_id} — Cập nhật bài nộp

**Request body** (mọi field optional)

| Field | Kiểu | Ghi chú |
|---|---|---|
| feedback | string \| null | Tối đa 10.000 ký tự; chuỗi rỗng sau trim được lưu thành null |
| status | string \| null | Chỉ nhận `pending`, `accepted`, `wrong_answer`, `compile_error` |

**Response 200 OK**: `SubmissionDetailResponse` sau cập nhật.

**Response lỗi**

| Status | Khi nào |
|---|---|
| 403 | Người gọi không phải Admin/Teacher |
| 404 | Submission không tồn tại hoặc ngoài phạm vi Teacher |
| 422 | Status không thuộc các giá trị cho phép hoặc body sai định dạng |

## GET /submissions/mine/{submission_id} — Sinh viên xem kết quả bài nộp của mình

Chỉ chủ bài nộp (role Student). Bài của người khác trả 404 (không lộ sự tồn tại).

- `testcases`: **chỉ testcase mẫu** (`is_sample = true`), kèm `input`, `expected_output`, `status`, `time`.
- `testcase_results`: kết quả của **mọi** testcase (cả test ẩn) gồm `index`, `is_sample`, `status`, `time`. Không bao giờ chứa `input`/`expected_output` của test ẩn.

## POST /submissions/{submission_id}/regrade — Chấm lại bài lỗi hệ thống

Admin/Teacher (trong phạm vi lớp của mình). Chỉ nhận bài có `status = internal_error`; reset `passed_count`, `compile_output`, token Judge0 và `testcase_results`, rồi đưa vào hàng đợi chấm.

**Response 202 Accepted**: `{"submission_id": int, "status": "pending"}`. **409** nếu bài không ở trạng thái `internal_error`; **403** với Student.

## Chấm theo lô và dừng sớm

Backend gửi testcase lên Judge0 theo lô `GRADING_CHUNK_SIZE` (mặc định 10). Sau một lô có test `time_limit_exceeded`, các lô sau **không được gửi**; các test còn lại có `status = skipped` và tính là không đạt. Lô có `compile_error` cũng dừng (mọi test lỗi biên dịch như nhau, không biên dịch lại). Lý do: Judge0 chạy test gần như tuần tự, một bài lặp vô hạn trên 50 test có thể chiếm máy chấm khoảng 4 phút. Thời gian chờ mỗi lô = `max(GRADING_TIMEOUT_SECONDS, số test × wall time + GRADING_CHUNK_EXTRA_SECONDS)`.

## Chưa triển khai

Assignment grade/publish, phát hiện trùng lặp (`similarity`) và phúc khảo (`late_appeal`) chưa có dữ liệu riêng.
