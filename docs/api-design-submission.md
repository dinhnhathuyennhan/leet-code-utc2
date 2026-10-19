# Thiết kế API — Bài nộp (Submission)

## Quy ước

- Submission hiện tham chiếu trực tiếp Problem, Student và testcase của Problem.
- Các màn hình Admin/Teacher hiện truy vấn Submission qua Problem → Lesson → Course; vì vậy Problem bank (`lesson_id = null`) không thuộc phạm vi các danh sách/chi tiết Submission này. Khi thêm bài bank vào Lesson, hệ thống tạo Problem bản sao với `problem_id` riêng; Submission cũ không được sao chép.
- Router này chỉ cung cấp chức năng quản lý bài nộp cho Admin/Teacher.
- Teacher chỉ xem và xử lý bài thuộc Course mình tạo; Admin xem toàn bộ.
- Chưa có API Student tạo Submission/Run, Judge0 async hoặc Assignment snapshot.

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

**Response 200 OK**: `SubmissionDetailResponse`, gồm thông tin Student/Course/Lesson/Problem, code, language, status, compile_output, feedback, passed_count, tổng testcase, submitted_datetime và testcase. `input` là mảng đối số JSON, `expected_output` là giá trị JSON; testcase legacy stdin/stdout giữ dạng chuỗi.

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

## Chưa triển khai

Không có endpoint tạo Submission trong router hiện tại. Các API Run code, Student submission history, deadline validation, Assignment grade/publish chưa được triển khai.
