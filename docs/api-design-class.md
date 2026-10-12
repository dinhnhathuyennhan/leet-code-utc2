# Thiết kế API: Quản lý lớp hành chính (Class)

> **Lớp hành chính (Class)** là lớp sinh hoạt cố định của Sinh viên, ví dụ `CQ.67.CNTT`. Mỗi Sinh viên thuộc đúng 1 lớp hành chính, qua cột `user.class_id`.
> Khác với **lớp học (Course)**, là lớp học phần do Giáo viên tạo để giao bài tập (xem [api-design-course.md](api-design-course.md)).

## Quy ước mã lớp (`class_id`)

- Định dạng: `<hệ>.<khoá>.<ngành>`, ví dụ `CQ.67.CNTT` hoặc `CQ.67.KTXDCTGT.2`. Định dạng này lấy theo cột "Lớp" trong file danh sách lớp học phần của phòng đào tạo.
- `class_id` **luôn do server ghép** từ 3 field: `type` (hệ), `course_number` (khoá), `department` (ngành). Client không gửi `class_id` khi tạo lớp.
- Tách ngược `class_id` thành 3 field theo **2 dấu chấm đầu tiên**: `CQ.67.KTXDCTGT.2` → `type = "CQ"`, `course_number = 67`, `department = "KTXDCTGT.2"`. Vì vậy `type` không được chứa dấu chấm, còn `department` thì được.
- Import Excel (`POST /students/import`) tự tạo lớp còn thiếu và dùng chung quy ước này, nên lớp tạo bằng tay và lớp tạo khi import luôn cùng định dạng.
- `class_id` **phân biệt chữ hoa/thường** và được lưu đúng như ghép ra. `cq.67.cntt` và `CQ.67.CNTT` là 2 lớp khác nhau.
- `class_id` là khoá chính và đang được `user.class_id` tham chiếu, nên **không có API sửa lớp**. Muốn đổi thì xoá lớp sai (khi lớp chưa có Sinh viên) rồi tạo lại.

## POST /classes: Tạo lớp hành chính

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| type | string | có | hệ đào tạo, vd `CQ`. Không được chứa dấu `.` |
| course_number | int | có | khoá, vd `67`. Phải là số nguyên dương |
| department | string | có | ngành, vd `CNTT` hoặc `KTXDCTGT.2` (được chứa dấu `.`) |

- `type` và `department` được tự động trim khoảng trắng hai đầu trước khi ghép.
- `course_number` gửi `67` hay `"067"` đều được hiểu là `67`, và cùng ghép ra `CQ.67.CNTT`.
- `class_id` ghép ra (`"{type}.{course_number}.{department}"`) tối đa 50 ký tự.

Ví dụ:

```json
{ "type": "CQ", "course_number": 67, "department": "CNTT" }
```

**Response 201 Created**

| Field | Kiểu | Ghi chú |
|---|---|---|
| class_id | string | mã lớp server ghép, vd `CQ.67.CNTT` |
| type | string | |
| course_number | int | |
| department | string | |
| student_count | int | số Sinh viên đang thuộc lớp, luôn = 0 lúc tạo |

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Thiếu field; `course_number` không phải số nguyên hoặc là `null` | `{"error_code": "VALIDATION_ERROR", "message": "..."}` (message của pydantic, tiếng Anh) |
| 422 | `type` rỗng, chỉ chứa khoảng trắng hoặc là `null` (use-case "Tạo lớp hành chính" bước 5a) | `{"error_code": "EMPTY_FIELD", "message": "Hệ đào tạo không được trống"}` |
| 422 | `department` rỗng, chỉ chứa khoảng trắng hoặc là `null` (bước 5a) | `{"error_code": "EMPTY_FIELD", "message": "Ngành không được trống"}` |
| 422 | `type` chứa dấu `.` (bước 5a) | `{"error_code": "INVALID_FORMAT", "message": "Hệ đào tạo không được chứa dấu chấm"}` |
| 422 | `course_number` ≤ 0 (bước 5a) | `{"error_code": "INVALID_FORMAT", "message": "Khoá phải là số nguyên dương"}` |
| 422 | `class_id` ghép ra dài quá 50 ký tự (bước 5a) | `{"error_code": "INVALID_FORMAT", "message": "Mã lớp không được dài quá 50 ký tự"}` |
| 403 | Người gọi không phải Admin/Teacher | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |
| 409 | `class_id` ghép ra đã tồn tại (bước 6a) | `{"error_code": "CONFLICT", "message": "Lớp CQ.67.CNTT đã tồn tại"}` |

**Quy tắc nghiệp vụ**

- Field lạ trong body (kể cả `class_id`) bị bỏ qua. `class_id` luôn do server ghép.
- Nếu có 2 request tạo cùng một lớp cùng lúc, request đến sau nhận 409 như trên, không phải 500.
- **Yêu cầu quyền**: Admin hoặc Teacher (`require_role(Role.ADMIN, Role.TEACHER)`). Teacher được tạo lớp, giống như khi import Excel thì Teacher cũng tự tạo được lớp.

## GET /classes: Danh sách lớp hành chính

**Response 200 OK**: mảng object giống response của `POST /classes`, sắp xếp theo `class_id`. Không có lớp nào thì trả `[]`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 403 | Người gọi không phải Admin/Teacher | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- `student_count` đếm số tài khoản có `class_id` bằng lớp đó. Lớp chưa có Sinh viên vẫn hiện, với `student_count = 0`.
- **Không giới hạn danh sách theo Giáo viên**: Admin và Teacher đều thấy toàn bộ lớp hành chính. Lý do:
  - lớp hành chính là danh mục dùng chung, response chỉ có mã lớp và số lượng Sinh viên, không có dữ liệu cá nhân;
  - Teacher cần thấy hết để không tạo trùng lớp.
- Danh sách Sinh viên của một lớp xem qua `GET /users?class_id=<class_id>`, endpoint này đã giới hạn dữ liệu theo vai trò người gọi.
- Không phân trang, vì số lớp hành chính ít (vài chục tới vài trăm).
- **Yêu cầu quyền**: Admin hoặc Teacher.

## GET /classes/{class_id}: Chi tiết lớp hành chính

`class_id` đặt thẳng trên đường dẫn, kể cả dấu chấm, ví dụ `GET /classes/CQ.67.CNTT`.

**Response 200 OK**: object giống response của `POST /classes`.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `class_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp CQ.67.CNTT"}` |
| 403 | Người gọi không phải Admin/Teacher | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- **Yêu cầu quyền**: Admin hoặc Teacher.

## DELETE /classes/{class_id}: Xoá lớp hành chính

**Request body**: không có

**Response**: `204 No Content`

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `class_id` không tồn tại (use-case "Xoá lớp hành chính" bước 5a) | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp CQ.67.CNTT"}` |
| 409 | Lớp còn Sinh viên (bước 6a) | `{"error_code": "CONFLICT", "message": "Lớp CQ.67.CNTT đang có 97 sinh viên, không thể xoá"}` |
| 409 | Có Sinh viên được thêm vào lớp ngay lúc đang xoá (E2) | `{"error_code": "CONFLICT", "message": "Lớp CQ.67.CNTT đang có sinh viên, không thể xoá"}` |
| 403 | Người gọi không phải Admin (kể cả Teacher) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Chỉ xoá được lớp **không còn Sinh viên nào**. Endpoint này không bao giờ xoá hay sửa tài khoản Sinh viên.
- Dùng để dọn lớp tạo nhầm (vd gõ sai hệ/khoá/ngành). Muốn xoá lớp đang có Sinh viên thì phải chuyển hết Sinh viên sang lớp khác trước.
- **Yêu cầu quyền**: chỉ Admin (`require_role(Role.ADMIN)`).
