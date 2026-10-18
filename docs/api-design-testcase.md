# Thiết kế API — Quản lý testcase (Testcase)

> Tài liệu này đặc tả hướng đi thiết kế API cho module **Testcase** (bộ test đầu vào/đầu ra của một bài tập). Phase 2 của [roadmap.md](roadmap.md) sẽ implement các endpoint này. Cấu trúc response lỗi và quy ước chung lấy theo [api-design-course.md](api-design-course.md), [api-design-problem.md](api-design-problem.md) và [global-exception-handler.md](global-exception-handler.md).

## Quy ước chung

### Phân quyền truy cập (scope theo vai trò)

| Hành động | Admin | Teacher (chủ lớp) | Teacher (không chủ lớp) | Student |
|---|---|---|---|---|
| `GET /problems/{problem_id}/testcases` (list) | ✅ thấy tất cả (cả ẩn) | ✅ thấy tất cả (cả ẩn) | ✅ thấy tất cả (cả ẩn) | ✅ **chỉ thấy `is_sample = true`** |
| `GET /testcases/{testcase_id}` (chi tiết) | ✅ | ✅ (testcase thuộc lớp mình tạo) | ✅ (testcase thuộc lớp mình tạo) | ✅ nếu `is_sample = true`. ❌ 404 nếu `is_sample = false` (ẩn) |
| `POST /problems/{problem_id}/testcases` (tạo) | ✅ | ✅ | ❌ 403 | ❌ 403 |
| `POST /problems/{problem_id}/testcases/bulk` (tạo hàng loạt) | ✅ | ✅ | ❌ 403 | ❌ 403 |
| `PATCH /testcases/{testcase_id}` (sửa) | ✅ | ✅ | ❌ 403 | ❌ 403 |
| `DELETE /testcases/{testcase_id}` (xoá) | ✅ | ✅ | ❌ 403 | ❌ 403 |

> **Quy ước "chủ lớp"** = `Course.created_by == current_user.user_id` (xem [api-design-course.md](api-design-course.md), [api-design-lesson.md](api-design-lesson.md), [api-design-problem.md](api-design-problem.md)). Logic kiểm tra nằm trong `service`, không phải `require_role` ở router.

### Quy tắc ẩn testcase (bảo mật — yêu cầu cứng từ [roadmap.md § Phase 2](roadmap.md))

> **Student chỉ thấy testcase `is_sample = true`; testcase ẩn không bao giờ lộ qua API của Student.**

- Khi Student gọi `GET /problems/{problem_id}/testcases`: chỉ trả về testcase có `is_sample = true`. Service **không query** testcase ẩn (tránh lộ qua log hoặc timing attack).
- Khi Student gọi `GET /testcases/{testcase_id}` mà `is_sample = false`: trả **404 `TESTCASE_NOT_FOUND`** (giả vờ không tồn tại), **không trả 403** (để không phân biệt được testcase ẩn với testcase thật sự không tồn tại).
- Khi Student gọi `GET /problems/{problem_id}` (xem [api-design-problem.md](api-design-problem.md)): chỉ nhúng `sample_testcases` (đã lọc `is_sample = true`).
- Endpoint `POST /problems/{problem_id}/submissions` (Phase 3) chạy **toàn bộ testcase** (cả ẩn) — đây là chỗ duy nhất trong flow của Student mà testcase ẩn được "sử dụng", nhưng **input/expected_output không bao giờ trả về response** của endpoint đó, chỉ trả kết quả pass/fail.

### Quy tắc giá trị cho `input`, `expected_output`, `input_type`, `expected_output_type`

| Field | Ràng buộc | Ghi chú |
|---|---|---|
| `input` | string, tối đa 10.000 ký tự | dữ liệu đầu vào chương trình (stdin). Có thể rỗng `""` (bài không đọc input) |
| `expected_output` | string, tối đa 10.000 ký tự | kết quả mong đợi trên stdout. Có thể rỗng `""` |
| `input_type` | enum string: `"text"` \| `"number"` \| `"json"` (**cột mới**, model `Testcase` hiện tại trong `backend/app/models/entities.py` chỉ có `input, expected_output, is_sample` — cần thêm trong migration Alembic) | mô tả kiểu dữ liệu của `input` để FE render đúng widget. Mặc định `"text"` |
| `expected_output_type` | enum string: `"text"` \| `"number"` \| `"json"` (**cột mới**) | mô tả kiểu dữ liệu của `expected_output`. Mặc định `"text"` |
| `is_sample` | bool | mặc định `false` khi tạo (testcase ẩn). Teacher đánh dấu `true` cho testcase muốn public cho Student |

**Lưu ý về base64 và ký tự đặc biệt**: vì input/output có thể chứa ký tự bất kỳ (binary, NULL, control char, UTF-8 đặc biệt), client **nên gửi base64** cho cả `input` và `expected_output` để tránh lỗi encoding. Tuy nhiên:
- **Phase 2 đơn giản hoá**: API nhận string thuần (UTF-8). Nếu input/output chứa ký tự không in được, FE phải escape (vd dùng JSON string).
- **Phase 3 (Submission)**: bắt buộc base64 theo [judge0-setup.md § Lưu ý bảo mật](judge0-setup.md) vì Judge0 yêu cầu `base64_encoded=true`. Lúc đó mới cần thêm field phụ hoặc query param `?encoding=base64` cho Testcase API. Tài liệu này sẽ cập nhật khi Phase 3 bắt đầu.

### Quy tắc xoá

- `DELETE /testcases/{testcase_id}` xoá testcase đơn lẻ. Khi xoá thành công, **giảm `Problem.total_number_testcase` đi 1** (cùng transaction).
- **Không cho phép restore** sau khi xoá.
- Không có cascade (Testcase là lá trong cây phụ thuộc).

### Quy tắc tạo hàng loạt (bulk)

- Endpoint `POST /problems/{problem_id}/testcases/bulk` cho phép tạo nhiều testcase trong 1 request. Mục đích: GV soạn bài nhanh khi import từ bộ test có sẵn (vd copy-paste từ file `.txt`/Excel).
- Xử lý "best-effort" giống `POST /students/import` (xem [api-design-auth.md](api-design-auth.md)): testcase hợp lệ vẫn tạo, testcase lỗi bị bỏ qua và liệt kê trong `errors` — không trả lỗi HTTP cho toàn bộ request chỉ vì có testcase lỗi. **Kể cả khi `created` rỗng toàn bộ, vẫn trả 201 kèm `errors` đầy đủ**.
- Tất cả testcase tạo hợp lệ phải nằm trong **một transaction**; nếu lỗi giữa chừng (vd mất kết nối DB) thì rollback toàn bộ, không tạo dở.

### Cột đếm & cập nhật

| Cột | Cập nhật khi | Ghi chú |
|---|---|---|
| `Problem.total_number_testcase` | Tạo/xoá Testcase con | Tăng khi thêm Testcase, giảm khi xoá. Cập nhật trong `testcase_service` (cùng transaction với insert/delete) |

### Quy tắc response

- Response **luôn dùng `response_model`** đã khai báo. Đối với Student: service **lọc `is_sample = true` ở tầng query** (không phải tầng serialize), tránh lộ qua log/exception message.
- Các field lạ trong request body bị Pydantic bỏ qua.
- **Không bao giờ trả `expected_output` của testcase ẩn** cho Student qua bất kỳ endpoint nào — kể cả khi Student đoán được `testcase_id` của testcase ẩn và gọi trực tiếp `GET /testcases/{testcase_id}` (sẽ trả 404 như § Quy tắc ẩn testcase).

### Xử lý lỗi

- Mọi exception nghiệp vụ kế thừa `AppError` (xem [global-exception-handler.md](global-exception-handler.md)). Router không viết `try/except`.
- Lỗi dùng chung (xem [api-design-lesson.md](api-design-lesson.md), [api-design-problem.md](api-design-problem.md)):
  - `ProblemNotFoundError` (404 `PROBLEM_NOT_FOUND`)
  - `ForbiddenError` (403 `FORBIDDEN`, message cụ thể theo ngữ cảnh)
- Lỗi riêng của domain `testcase` (đặt trong `backend/app/modules/problems/testcase_service.py`):
  - `TestcaseNotFoundError` (404 `TESTCASE_NOT_FOUND`, message `"Không tìm thấy testcase"`) — cũng dùng cho Student cố truy cập testcase ẩn (giả vờ không tồn tại)
  - `TestcaseInvalidTypeError` (422 `INVALID_TESTCASE_TYPE`, message `"input_type và expected_output_type phải là text, number hoặc json"`)
  - `TestcaseBulkEmptyError` (400 `EMPTY_TESTCASE_BULK`, message `"Danh sách testcase không được rỗng"`) — khi `POST /testcases/bulk` body có `testcases = []`
  - `TestcaseBulkTooLargeError` (400 `TESTCASE_BULK_TOO_LARGE`, message `"Vượt quá số testcase cho phép trong 1 request"`) — giới hạn 200 testcase/request
  - `TestcaseInvalidFieldError` (422 `INVALID_TESTCASE_FIELD`, message cụ thể: `"input vượt quá 10000 ký tự"` / `"expected_output vượt quá 10000 ký tự"` / ...)

---

## POST /problems/{problem_id}/testcases — Tạo testcase

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| input | string | có | tối đa 10.000 ký tự. Có thể rỗng `""` |
| expected_output | string | có | tối đa 10.000 ký tự. Có thể rỗng `""` |
| input_type | string | không | enum `"text"` \| `"number"` \| `"json"`. Mặc định `"text"` |
| expected_output_type | string | không | enum. Mặc định `"text"` |
| is_sample | bool | không | mặc định `false` |

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| testcase_id | int | |
| problem_id | int | |
| input | string | |
| expected_output | string | |
| input_type | string | |
| expected_output_type | string | |
| is_sample | bool | |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Thiếu field, field bắt buộc = `null`, sai kiểu dữ liệu | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 422 | `input_type` hoặc `expected_output_type` không thuộc enum | `{"error_code": "INVALID_TESTCASE_TYPE", "message": "input_type và expected_output_type phải là text, number hoặc json"}` |
| 422 | `input` vượt quá 10.000 ký tự | `{"error_code": "INVALID_TESTCASE_FIELD", "message": "input vượt quá 10000 ký tự"}` |
| 422 | `expected_output` vượt quá 10.000 ký tự | `{"error_code": "INVALID_TESTCASE_FIELD", "message": "expected_output vượt quá 10000 ký tự"}` |
| 404 | `problem_id` không tồn tại | `{"error_code": "PROBLEM_NOT_FOUND", "message": "Không tìm thấy bài tập"}` |
| 403 | Người gọi không phải Admin, hoặc là Teacher nhưng không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thêm testcase vào bài tập này"}` |

**Quy tắc nghiệp vụ**

- Sau khi tạo thành công, **tăng `Problem.total_number_testcase` lên 1** (cùng transaction với insert Testcase).
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

---

## POST /problems/{problem_id}/testcases/bulk — Tạo hàng loạt

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| testcases | array of object | có | mỗi phần tử có shape giống body của `POST /problems/{problem_id}/testcases`. Tối đa 200 phần tử (**tham khảo**, chốt khi implement). Mảng rỗng → 400 |

**Response 201 Created** — tổng hợp kết quả xử lý từng testcase (best-effort)

| Field | Kiểu | Ghi chú |
|---|---|---|
| created | array of object | mỗi phần tử: `testcase_id`, `input`, `expected_output`, `input_type`, `expected_output_type`, `is_sample` |
| errors | array of object | mỗi phần tử: `index` (vị trí trong mảng `testcases`, 0-based), `field` (field bị lỗi, vd `"input"` / `"expected_output_type"`), `reason` (lý do lỗi, vd `"vượt quá 10000 ký tự"`) |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 400 | `testcases = []` hoặc không có key `testcases` | `{"error_code": "EMPTY_TESTCASE_BULK", "message": "Danh sách testcase không được rỗng"}` |
| 400 | `len(testcases) > 200` (con số 200 là tham khảo, chốt khi implement) | `{"error_code": "TESTCASE_BULK_TOO_LARGE", "message": "Vượt quá số testcase cho phép trong 1 request"}` |
| 404 | `problem_id` không tồn tại | `{"error_code": "PROBLEM_NOT_FOUND", "message": "Không tìm thấy bài tập"}` |
| 403 | Người gọi không phải Admin, hoặc là Teacher nhưng không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thêm testcase vào bài tập này"}` |

**Quy tắc nghiệp vụ**

- Xử lý "best-effort" giống `POST /students/import` (xem [api-design-auth.md](api-design-auth.md)): testcase hợp lệ tạo thành công, testcase lỗi bị bỏ qua và liệt kê trong `errors` — **không trả lỗi HTTP** cho toàn bộ request. Kể cả khi `created` rỗng toàn bộ, vẫn trả 201 kèm `errors` đầy đủ.
- Tất cả testcase hợp lệ phải nằm trong **một transaction**; nếu lỗi giữa chừng (vd mất kết nối DB) thì rollback toàn bộ.
- Sau khi tạo hợp lệ, `Problem.total_number_testcase` tăng = `len(created)`.
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

---

## GET /problems/{problem_id}/testcases — Danh sách testcase của bài tập

**Query parameters**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| is_sample | bool | không | lọc theo `is_sample`. Bỏ trống = tất cả (chỉ áp dụng cho Admin/Teacher; Student luôn bị filter `is_sample = true` bất kể query) |

**Response 200 OK**: mảng object giống response của `POST /problems/{problem_id}/testcases`, sắp xếp theo `testcase_id` tăng dần. Không có testcase nào → `[]`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `problem_id` không tồn tại | `{"error_code": "PROBLEM_NOT_FOUND", "message": "Không tìm thấy bài tập"}` |
| 403 | Student chưa enroll vào course chứa problem, hoặc ngoài khoảng `[start_datetime, end_datetime]` của problem | `{"error_code": "PROBLEM_NOT_OPEN", "message": "Bài tập hiện chưa mở hoặc đã đóng"}` |
| 403 | Teacher không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem bài tập này"}` |
| 403 | Role không thuộc Admin/Teacher/Student | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- **Student**: chỉ trả testcase có `is_sample = true`, bất kể query `is_sample`. Service **lọc ở tầng query** bằng cách luôn query cả 2 rồi filter trong Python (không dùng `WHERE is_sample = ?` với 2 nhánh query khác nhau — tránh **timing attack** Student đoán được testcase ẩn qua thời gian response).
- **Admin / Teacher chủ lớp**: thấy tất cả testcase, tuân theo query `is_sample` nếu có.
- **Teacher không phải chủ lớp**: 403.
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi truy cập theo vai trò.

---

## GET /testcases/{testcase_id} — Chi tiết testcase

**Response 200 OK**: object giống response của `POST /problems/{problem_id}/testcases`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `testcase_id` không tồn tại, **hoặc** Student cố truy cập testcase có `is_sample = false` (giả vờ không tồn tại) | `{"error_code": "TESTCASE_NOT_FOUND", "message": "Không tìm thấy testcase"}` |
| 403 | Student chưa enroll vào course chứa problem, hoặc ngoài khoảng `[start_datetime, end_datetime]` của problem | `{"error_code": "PROBLEM_NOT_OPEN", "message": "Bài tập hiện chưa mở hoặc đã đóng"}` |
| 403 | Teacher không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xem bài tập này"}` |
| 403 | Role không thuộc Admin/Teacher/Student | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Áp dụng đúng § Quy tắc ẩn testcase: Student truy cập testcase ẩn → **404 (không 403)**.
- **Yêu cầu quyền**: Bearer token hợp lệ, đúng phạm vi truy cập theo vai trò.

---

## PATCH /testcases/{testcase_id} — Cập nhật testcase

**Request body** (tất cả optional, chỉ cập nhật field được truyền)

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| input | string | không | tối đa 10.000 ký tự |
| expected_output | string | không | tối đa 10.000 ký tự |
| input_type | string | không | enum `"text"` \| `"number"` \| `"json"` |
| expected_output_type | string | không | enum |
| is_sample | bool | không | thay đổi trạng thái ẩn/hiện |

Field không gửi → giữ nguyên. Field gửi = `null` → **bị bỏ qua** (giữ giá trị cũ). Body rỗng `{}` hoặc toàn `null` → không cập nhật gì, trả 200 với dữ liệu hiện tại.

**Response 200 OK**: object giống response của `POST /problems/{problem_id}/testcases`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `testcase_id` không tồn tại | `{"error_code": "TESTCASE_NOT_FOUND", "message": "Không tìm thấy testcase"}` |
| 403 | Người gọi không phải Admin, hoặc là Teacher nhưng không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền chỉnh sửa testcase này"}` |
| 422 | Sai kiểu dữ liệu | `{"error_code": "VALIDATION_ERROR", "message": "..."}` |
| 422 | `input_type` hoặc `expected_output_type` không thuộc enum | `{"error_code": "INVALID_TESTCASE_TYPE", "message": "..."}` |
| 422 | `input` vượt quá 10.000 ký tự | `{"error_code": "INVALID_TESTCASE_FIELD", "message": "input vượt quá 10000 ký tự"}` |
| 422 | `expected_output` vượt quá 10.000 ký tự | `{"error_code": "INVALID_TESTCASE_FIELD", "message": "expected_output vượt quá 10000 ký tự"}` |

**Quy tắc nghiệp vụ**

- Không cho sửa `testcase_id`, `problem_id` qua endpoint này (field lạ bị bỏ qua).
- Có thể đổi `is_sample` từ `false` → `true` (công khai hoá) hoặc `true` → `false` (ẩn đi). Khi đổi từ `true` → `false`, **sinh viên đã xem testcase đó vẫn thấy giá trị cũ trong cache FE** cho đến khi FE refetch — đây là hành vi chấp nhận được.
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

---

## DELETE /testcases/{testcase_id} — Xoá testcase

**Response**: `204 No Content`

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `testcase_id` không tồn tại | `{"error_code": "TESTCASE_NOT_FOUND", "message": "Không tìm thấy testcase"}` |
| 403 | Người gọi không phải Admin, hoặc là Teacher nhưng không phải chủ lớp | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền xoá testcase này"}` |

**Quy tắc nghiệp vụ**

- Khi xoá thành công, **giảm `Problem.total_number_testcase` đi 1** (cùng transaction với delete Testcase).
- **Yêu cầu quyền**: Admin, hoặc Teacher chủ lớp.

---

## Mở rộng trong tương lai (Phase 3 trở đi, **không implement ở Phase 2**)

- Hỗ trợ upload testcase bằng file (vd `.zip` chứa nhiều cặp `input.txt` / `output.txt`) — chưa chốt, có thể bỏ scope nếu trễ (xem [roadmap.md § Cắt scope](roadmap.md)).
- Hỗ trợ `encoding=base64` cho `input` / `expected_output` khi Phase 3 (Submission) tích hợp Judge0 — xem [judge0-setup.md](judge0-setup.md).
- Xuất bộ testcase ra file `.zip` để share — chưa chốt.

---

## Liên quan tới Phase 3 (Submission & chấm bài)

Testcase **không có endpoint Phase 3 mới**. Tuy nhiên, Testcase bị ảnh hưởng trực tiếp bởi Judge0 (xem [judge0-setup.md](judge0-setup.md)):

### Base64 encoding

- **Phase 2 (hiện tại)**: API nhận và trả `input` / `expected_output` dưới dạng **string thuần** (UTF-8). Nếu input/output chứa ký tự không in được, FE phải tự escape (JSON string).
- **Phase 3**: Khi `Submission` được chấm, `judge_client` sẽ **tự base64-encode `input` / `expected_output` trước khi gửi cho Judge0** (vì Judge0 yêu cầu `base64_encoded=true` theo [judge0-setup.md § Lưu ý bảo mật](judge0-setup.md)). Service **không cần thay đổi Testcase API** — chỉ cần đảm bảo lưu trữ `input` / `expected_output` nguyên văn (UTF-8) trong DB, không ép base64.
- **Tương lai (nếu FE cần)**: bổ sung query param `?encoding=base64` cho `GET /testcases/{id}` để FE render nhanh — **chưa cần ở Phase 3**, có thể làm ở Phase 4 nếu FE gặp khó khăn với ký tự đặc biệt.

### Quy tắc ẩn testcase khi chấm bài (Phase 3)

- Endpoint `POST /problems/{problem_id}/submissions` chạy **toàn bộ testcase** (cả ẩn) qua Judge0 — đây là chỗ duy nhất trong flow của Student mà testcase ẩn được "sử dụng".
- Tuy nhiên, **input/expected_output của testcase ẩn KHÔNG BAO GIỜ trả về response** của bất kỳ endpoint nào cho Student, kể cả `GET /submissions/{id}` (xem [api-design-problem.md § GET /submissions/{submission_id}](api-design-problem.md)). Response chỉ trả `testcase_id`, `status`, `time`, `memory`, `is_sample` — không trả `input` / `expected_output`.
- Judge0 stdout / stderr của testcase ẩn **cũng không trả về** (chỉ trả cho `is_sample = true` khi SV dùng `/run`).

### Cập nhật cột đếm khi có Submission

- Khi tạo Submission mới (xem [api-design-problem.md § POST /problems/{problem_id}/submissions](api-design-problem.md)) → `Problem.total_number_testcase` **không đổi** (chỉ tăng khi thêm Testcase).
- Khi Submission `status = accepted` là lần đầu của SV đó → **tăng `Lesson.total_number_student_finished`** (xem [api-design-lesson.md](api-design-lesson.md)).
