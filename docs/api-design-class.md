# Thiết kế API: Quản lý lớp hành chính (Class)

> **Lớp hành chính (Class)** là lớp sinh hoạt cố định của Sinh viên, ví dụ `CQ.67.CNTT`. Mỗi Sinh viên thuộc đúng 1 lớp hành chính, qua cột `user.class_id`.
> Khác với **lớp học (Course)**, là lớp học phần do Giáo viên tạo để giao bài tập (xem [api-design-course.md](api-design-course.md)).

## Quy ước mã lớp (`class_id`)

- Định dạng: `<hệ>.<khoá>.<ngành>`, ví dụ `CQ.67.CNTT` hoặc `CQ.67.KTXDCTGT.2`. Định dạng này lấy theo cột "Lớp" trong file danh sách lớp học phần của phòng đào tạo.
- `class_id` **luôn do server ghép** từ 3 field: `type` (hệ), `course_number` (khoá), `department` (ngành). Client không gửi `class_id` khi tạo lớp.
- Tách ngược `class_id` thành 3 field theo **2 dấu chấm đầu tiên**: `CQ.67.KTXDCTGT.2` → `type = "CQ"`, `course_number = 67`, `department = "KTXDCTGT.2"`. Vì vậy `type` chỉ được gồm chữ cái không dấu (không có dấu chấm), còn `department` thì được chứa dấu chấm.
- `department` chỉ gồm chữ cái (có dấu cũng được, vd `Đ`), chữ số và 3 ký tự `.` `&` `-`; dấu chấm không được ở đầu, ở cuối hoặc đứng liền nhau. Quy tắc này lấy theo file thật (vd `XDDD&CN.1`, `TC-NH`, `ĐK&TTĐSHĐ`) và áp dụng cho cả `POST /classes` lẫn import. Ký tự `/` bị chặn vì lớp có `/` trong mã sẽ không gọi được qua `/classes/{class_id}`.
- Mã lớp được chuẩn hoá Unicode (NFC) trước khi lưu, để cùng một chữ có dấu gõ theo 2 kiểu không tạo ra 2 lớp khác nhau.
- Import Excel (`POST /students/import`) tự tạo lớp còn thiếu và dùng chung quy ước này, nên lớp tạo bằng tay và lớp tạo khi import luôn cùng định dạng.
- `class_id` **phân biệt chữ hoa/thường** và được lưu đúng như ghép ra. `cq.67.cntt` và `CQ.67.CNTT` là 2 lớp khác nhau.
- `class_id` là khoá chính và đang được `user.class_id` tham chiếu. Muốn sửa hệ/khoá/ngành thì dùng `PATCH /classes/{class_id}` (chỉ Admin): server tạo lớp với mã mới, chuyển toàn bộ Sinh viên sang, rồi xoá lớp cũ. Lớp tạo nhầm chưa có Sinh viên thì cũng có thể xoá rồi tạo lại.

## POST /classes: Tạo lớp hành chính

**Request body**

| Field | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| type | string | có | hệ đào tạo, vd `CQ`. Chỉ gồm chữ cái không dấu (`A-Z`, `a-z`): không có số, khoảng trắng, dấu `.` hay ký tự đặc biệt |
| course_number | int | có | khoá, vd `67`. Phải là số nguyên dương |
| department | string | có | ngành, vd `CNTT`, `KTXDCTGT.2`, `XDDD&CN.1`, `TC-NH`. Chỉ gồm chữ cái (có dấu được), chữ số và `.` `&` `-`; dấu chấm không ở đầu, cuối hoặc liền nhau |

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
| 422 | `department` không phải chuỗi, vd `["CNTT"]`, `123` (bước 5a) | `{"error_code": "INVALID_FORMAT", "message": "Ngành phải là chuỗi"}` |
| 422 | `department` có ký tự khác chữ cái, chữ số, `.` `&` `-` (vd `CNTT/1`, `CN TT`, `CNTT_1`), hoặc dấu chấm ở đầu/cuối/liền nhau (bước 5a) | `{"error_code": "INVALID_FORMAT", "message": "Ngành chỉ được gồm chữ cái, chữ số và các ký tự . & - (dấu chấm không được ở đầu, ở cuối hoặc đứng liền nhau)"}` |
| 422 | `type` có ký tự không phải chữ cái không dấu, vd `C.Q`, `CQ1`, `C Q`, `CQ-`, `CQ@`, `Đ` (bước 5a) | `{"error_code": "INVALID_FORMAT", "message": "Hệ đào tạo chỉ được gồm chữ cái không dấu"}` |
| 422 | `course_number` ≤ 0 hoặc là `true`/`false` (bước 5a) | `{"error_code": "INVALID_FORMAT", "message": "Khoá phải là số nguyên dương"}` |
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
- Danh sách tài khoản Sinh viên của một lớp (quản lý tài khoản) xem qua `GET /users?class_id=<class_id>`, endpoint này đã giới hạn dữ liệu theo vai trò người gọi. Để xem trước Sinh viên của lớp khi thêm cả lớp vào Course, dùng `GET /classes/{class_id}/students`.
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

## GET /classes/{class_id}/students: Sinh viên của lớp hành chính

Dùng ở hộp thoại "Thêm sinh viên vào lớp" (chế độ Theo lớp) để Giáo viên xem trước những Sinh viên sẽ được ghi danh bằng `POST /courses/{course_id}/enrollments/class`.

**Response 200 OK**: mảng, sắp xếp theo `user_id`. Lớp chưa có Sinh viên thì trả `[]`.

```json
[
  {
    "user_id": "6f1c...-uuid",
    "student_code": "6751071001",
    "full_name": "Nguyễn Văn A",
    "email": "6751071001@st.utc2.edu.vn",
    "class_id": "CQ.67.CNTT"
  }
]
```

`user_id` là UUID (khoá gọi API), `student_code` là MSSV để hiển thị; không dùng lẫn hai trường.

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `class_id` không tồn tại | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp hành chính"}` |
| 403 | Người gọi không phải Admin/Teacher | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Chỉ trả tài khoản Sinh viên (`role_id = 3`) có `class_id` bằng lớp đó, đúng tập mà `POST /courses/{course_id}/enrollments/class` sẽ ghi danh.
- Teacher xem được mọi lớp: Teacher đã có quyền ghi danh cả lớp vào Course của mình, nên được xem trước danh sách sẽ được thêm. Response chỉ gồm thông tin định danh, không có tiến độ hay điểm.
- **Yêu cầu quyền**: Admin hoặc Teacher.

## PATCH /classes/{class_id}: Đổi mã lớp hành chính

`class_id` trên đường dẫn là mã lớp **hiện tại**, ví dụ `PATCH /classes/CQ.67.CNTT`.

**Request body**: giống `POST /classes`, **bắt buộc đủ cả 3 field** `type`, `course_number`, `department`, cùng quy tắc kiểm tra và chuẩn hoá. Mã lớp mới do server ghép từ 3 field này.

Ví dụ đổi `CQ.67.CNTT` thành `CQ.68.CNTT`:

```json
{ "type": "CQ", "course_number": 68, "department": "CNTT" }
```

**Response 200 OK**: object giống response của `POST /classes`, là lớp với **mã mới**, `student_count` là số Sinh viên đã được chuyển sang.

```json
{ "class_id": "CQ.68.CNTT", "type": "CQ", "course_number": 68, "department": "CNTT", "student_count": 97 }
```

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 422 | Body sai, giống bảng lỗi 422 của `POST /classes` (thiếu field, `type`/`department`/`course_number` sai định dạng, mã lớp mới dài quá 50 ký tự) (use-case "Đổi mã lớp hành chính" bước 5a) | như `POST /classes` |
| 404 | `class_id` hiện tại không tồn tại (bước 6a) | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp CQ.67.CNTT"}` |
| 409 | Mã lớp mới đã tồn tại, kể cả khi request khác vừa tạo đúng mã đó cùng lúc (bước 7a) | `{"error_code": "CONFLICT", "message": "Lớp CQ.68.CNTT đã tồn tại"}` |
| 409 | Có Sinh viên được thêm vào lớp cũ ngay lúc đang đổi mã (E2) | `{"error_code": "CONFLICT", "message": "Lớp CQ.67.CNTT vừa có sinh viên mới, vui lòng thử lại"}` |
| 403 | Người gọi không phải Admin (kể cả Teacher) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- `class_id` là khoá chính và khoá ngoại `user.class_id` không tự cập nhật theo, nên server làm 3 bước: tạo lớp mới, chuyển mọi tài khoản có `class_id` cũ sang mã mới, xoá lớp cũ. Cả 3 bước nằm trong **một transaction**: lỗi ở bước nào thì rollback, lớp cũ và Sinh viên giữ nguyên như trước.
- Mã mới ghép ra **trùng mã hiện tại**: không thay đổi gì, trả 200 với dữ liệu hiện tại.
- Sau khi đổi, `GET /classes/<mã cũ>` trả 404; danh sách Sinh viên xem qua `GET /users?class_id=<mã mới>`. Ghi danh lớp học phần (Enrollment) không bị ảnh hưởng.
- **Yêu cầu quyền**: chỉ Admin (`require_role(Role.ADMIN)`).

## DELETE /classes/{class_id}: Xoá lớp hành chính

**Request body**: không có

**Response**: `204 No Content`

**Response lỗi**

| Status | Khi nào | Body |
|---|---|---|
| 404 | `class_id` không tồn tại (use-case "Xoá lớp hành chính" bước 5a) | `{"error_code": "NOT_FOUND", "message": "Không tìm thấy lớp CQ.67.CNTT"}` |
| 409 | Lớp còn Sinh viên (bước 6a) | `{"error_code": "CONFLICT", "message": "Lớp CQ.67.CNTT đang có 97 sinh viên, không thể xóa"}` |
| 409 | Có Sinh viên được thêm vào lớp ngay lúc đang xoá (E2) | `{"error_code": "CONFLICT", "message": "Lớp CQ.67.CNTT đang có sinh viên, không thể xóa"}` |
| 403 | Người gọi không phải Admin (kể cả Teacher) | `{"error_code": "FORBIDDEN", "message": "Bạn không có quyền thực hiện hành động này"}` |

**Quy tắc nghiệp vụ**

- Chỉ xoá được lớp **không còn Sinh viên nào**. Endpoint này không bao giờ xoá hay sửa tài khoản Sinh viên.
- Dùng để dọn lớp tạo nhầm (vd gõ sai hệ/khoá/ngành). Muốn xoá lớp đang có Sinh viên thì phải chuyển hết Sinh viên sang lớp khác trước. Nếu chỉ cần sửa mã lớp gõ sai thì dùng `PATCH /classes/{class_id}`, Sinh viên được chuyển theo.
- **Yêu cầu quyền**: chỉ Admin (`require_role(Role.ADMIN)`).
