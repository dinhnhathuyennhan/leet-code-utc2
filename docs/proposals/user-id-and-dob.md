# Đề xuất: tách `user_id` / bỏ `date_of_birth` trong bảng `user`

Trạng thái: **đang thảo luận**, chưa sửa code.

Hai thay đổi này động vào cùng một nhóm file nên nên làm chung trong **một PR refactor `user`**.

---

## Tóm tắt

| | Việc 1: Tách `user_id` | Việc 2: Bỏ `date_of_birth` |
|---|---|---|
| Thay đổi | `user_id` thành số tự tăng (khoá chính), thêm cột `code` (MSSV / mã cán bộ) | Xoá cột `date_of_birth` |
| Lợi ích chính | Sửa được MSSV khi nhập nhầm; Admin/Giáo viên không phải bịa mã | Bớt lưu dữ liệu cá nhân; import Excel và tạo tay thống nhất với nhau |
| Chi phí | Khoảng 200 chỗ ở backend, 150 ở test, 55 ở frontend; 3 khoá ngoại đổi kiểu | Khoảng 15 chỗ ở backend, 3 file test, 2 file frontend |
| Phụ thuộc | — | Cần Việc 1 (dùng `code` thay ngày sinh để làm mật khẩu tạm cho Giáo viên) |

**Cần nhóm chốt trước khi làm:**

1. Giáo viên có **mã cán bộ** để làm `code` không?
2. Quy tắc **tuổi tối thiểu** (Giáo viên ≥ 22, Sinh viên ≥ 17) có phải yêu cầu bắt buộc của đề tài không?

---

## Việc 1: Tách `user_id` thành `user_id` tự tăng + `code`

### Hiện trạng

`user.user_id` (varchar 50) vừa là khoá chính, vừa là MSSV (Sinh viên) hoặc mã Giáo viên. Các chỗ đang dựa vào điều này:

- **Khoá ngoại** trỏ vào `user_id`: `course.created_by`, `enrollment.student_id`, `submission.student_id` ([entities.py](../../backend/app/models/entities.py)).
- **Mật khẩu tạm Sinh viên** = `user_id`; **email** = `{user_id}@st.utc2.edu.vn`.
- **Import Excel** gộp dòng trùng và đối chiếu tài khoản đã có theo `user_id` ([students/service.py](../../backend/app/modules/students/service.py)).
- **JWT** có `sub = user_id` ([tokens.py](../../backend/app/core/security/tokens.py)).
- **URL**: `/users/{user_id}/reset-password`, `/courses/{id}/enrollments/{student_id}`.

### Lợi ích

1. **Sửa được MSSV/mã khi nhập nhầm.** Hiện tại MSSV là khoá chính và bị 3 bảng tham chiếu, gần như không sửa được. Sau khi tách, sửa chỉ là đổi một cột.
2. **Admin/Giáo viên không phải bịa mã** khi họ không có MSSV.
3. Join và index trên kiểu int gọn hơn varchar (lợi ích phụ).

### Rủi ro

- **Phạm vi sửa lớn**: mọi nơi đang lấy MSSV từ `user_id` phải chuyển sang `code`; 3 cột khoá ngoại đổi sang int; frontend đổi theo.
- **ID tự tăng dễ đoán** (`/users/5`, `/users/6`...). API đều đã kiểm tra quyền nên không lộ dữ liệu, nhưng người ngoài đoán được tổng số tài khoản. Muốn tránh thì dùng UUID thay int.
- **Vẫn phải chặn trùng mã** bằng `UNIQUE` trên `code`. Việc này giải quyết luôn phần backend còn nợ từ PR #36 (kiểm tra trùng `user_id`).
- **Dữ liệu cũ**: schema đang trong giai đoạn thay đổi, có thể xoá DB rồi chạy lại `seed_data.py` thay vì viết migration chuyển dữ liệu.

### Thiết kế đề xuất

```
user
  user_id    int PK (tự tăng)            -- hoặc uuid
  code       varchar(50) UNIQUE NOT NULL -- MSSV với SV, mã cán bộ với GV/Admin
  ...
course.created_by, enrollment.student_id, submission.student_id  →  int FK
```

Phương án tuỳ vào câu hỏi 1:

- **Giáo viên có mã cán bộ**: dùng một cột chung `code` NOT NULL (như trên).
- **Giáo viên không có mã**: dùng cột `mssv` cho phép NULL + `UNIQUE` (PostgreSQL cho nhiều dòng NULL trong cột UNIQUE). Khi đó Việc 2 sẽ thiếu nguồn mật khẩu tạm cho Giáo viên (xem bên dưới).

### Thời điểm

Nên làm **trước Phase 3** (nộp bài và chấm bài). Phase 3 sẽ thêm nhiều code và dữ liệu `submission` dựa trên `student_id`, để càng lâu càng tốn công sửa.

---

## Việc 2: Bỏ `date_of_birth`

### Ngày sinh đang được dùng ở đâu

| Chỗ dùng | File |
|---|---|
| Mật khẩu tạm Giáo viên/Admin = ngày sinh `ddmmyyyy` (khi tạo tài khoản) | [users/service.py:51](../../backend/app/modules/users/service.py#L51) |
| Mật khẩu tạm Giáo viên/Admin khi reset, kèm lỗi nếu thiếu ngày sinh | [users/service.py:171-176](../../backend/app/modules/users/service.py#L171-L176) |
| Kiểm tra tuổi Giáo viên ≥ 22 | [users/service.py:38-45](../../backend/app/modules/users/service.py#L38-L45) |
| Kiểm tra tuổi Sinh viên ≥ 17 (khi tạo tay) | [users/service.py:72-79](../../backend/app/modules/users/service.py#L72-L79) |
| `DateOfBirthRequiredError` | [users/service.py:18](../../backend/app/modules/users/service.py#L18) |
| `parse_date_of_birth`, `password_from_date`, các field trong request/response | [modules/users/schemas.py](../../backend/app/modules/users/schemas.py) |
| `age_calculation` | [core/utils/dates.py](../../backend/app/core/utils/dates.py) |
| Form cấp tài khoản và kiểu dữ liệu | [account-management.tsx](../../frontend/src/components/admin/account-management.tsx), [types.ts](../../frontend/src/lib/api/types.ts) |
| Test | `test_user_service.py`, `test_user_routes.py`, `test_student_service.py` |
| Seed data, docs | `seed_data.py`, use case "Cấp phát tài khoản Giáo viên" / "Sinh viên" trong [use-cases-auth.md](../use-cases-auth.md) |

Hiện tại ngày sinh **không thống nhất**: import Excel không có ngày sinh (để NULL), nhưng tạo Sinh viên bằng tay lại bắt buộc nhập.

### Thay thế cho từng việc

**Mật khẩu tạm**: nếu có `code` (Việc 1), quy tắc trở thành **mật khẩu tạm = `code` cho mọi vai trò**. Sinh viên vốn đã làm như vậy, nên quy tắc đơn giản hơn. Nhánh "thiếu ngày sinh" và `DateOfBirthRequiredError` cũng không cần nữa.

Nếu Giáo viên **không có mã cán bộ** thì bỏ ngày sinh xong sẽ không còn nguồn mật khẩu tạm cho Giáo viên. Nhóm đã chốt không dùng mật khẩu ngẫu nhiên, nên khi đó phải tìm nguồn khác.

**Kiểm tra tuổi 22/17**: bỏ ngày sinh thì quy tắc này mất theo. Cần xác nhận đây có phải yêu cầu của đề tài/thầy cô không. Thực tế tài khoản do Admin/Giáo viên cấp từ danh sách của trường, nên kiểm tra tuổi không chặn được gì nhiều.

### Lợi ích

- Bớt lưu dữ liệu cá nhân nhạy cảm.
- Thống nhất giữa import Excel và tạo tay (file Excel của trường không có ngày sinh).
- Form cấp tài khoản gọn hơn, ít validate hơn.

### Lưu ý bảo mật (không chặn việc bỏ)

Mật khẩu tạm = mã người dùng thì **ai biết mã cũng đoán được mật khẩu**, trong khoảng thời gian từ lúc cấp tài khoản cho tới khi chủ tài khoản đổi mật khẩu. MSSV thường công khai trong danh sách lớp. Sinh viên hiện đã chịu rủi ro này. Ngày sinh khó đoán hơn một chút nhưng không mạnh hơn bao nhiêu. `must_change_password = true` giúp thu hẹp khoảng thời gian rủi ro.

---

## Kế hoạch gộp (khi nhóm đã chốt)

Một PR refactor `user`, không gộp tính năng khác:

1. **Schema + migration**: `user_id` tự tăng, thêm `code` UNIQUE, bỏ `date_of_birth`; 3 khoá ngoại đổi sang int. Reset DB và seed lại.
2. **Backend**: mật khẩu tạm = `code`; email Sinh viên = `{code}@st.utc2.edu.vn`; import/dedupe theo `code`; kiểm tra trùng `code` thì trả `ConflictError` (kế thừa `AppError`); bỏ kiểm tra tuổi (nếu nhóm đồng ý); response trả thêm `code`, không trả `hashed_password`.
3. **Test**: sửa test cũ; thêm test trùng `code`, sửa `code`, reset mật khẩu theo `code` cho từng vai trò, vai trò lạ bị chặn.
4. **Frontend**: form cấp tài khoản bỏ ngày sinh, hiển thị `code`; đổi các chỗ đang dùng `user_id` làm MSSV.
5. **Docs**: cập nhật ERD, use case cấp tài khoản / đặt lại mật khẩu / import, API design.
