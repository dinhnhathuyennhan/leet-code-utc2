# Thiết kế giao diện: Khoá / mở khoá / sửa tài khoản

Frontend cho các API `POST /users/{user_id}/lock`, `POST /users/{user_id}/unlock`,
`PATCH /users/{user_id}` và mã lỗi `ACCOUNT_LOCKED` (hợp đồng ở `api-design-auth.md`,
luồng ở `use-cases-auth.md`). Quyền thật sự do backend quyết định; giao diện chỉ ẩn nút
ở những tài khoản chắc chắn không được phép.

## Màn hình có thao tác

| Màn hình | Người dùng | Hiển thị |
|---|---|---|
| Admin → Quản lý tài khoản (`/admin/accounts`) | Admin | Cột **Trạng thái**: badge "Hoạt động" / "Đã khoá". Nút **Sửa**, **Khoá**/**Mở khoá**, **Đặt lại MK** |
| Giáo viên → Lớp học phần → tab Sinh viên (`/teacher/courses/{id}?tab=students`) | Giáo viên chủ lớp | Badge "Đã khoá" cạnh tên Sinh viên bị khoá. Nút biểu tượng **Sửa**, **Khoá**/**Mở khoá**, **Xoá khỏi lớp** |

Ai thấy nút nào (whitelist theo vai trò của tài khoản đích):

| Người dùng | Sửa | Khoá / Mở khoá |
|---|---|---|
| Admin | Giáo viên, Sinh viên và chính mình | Giáo viên, Sinh viên. Không có nút ở dòng của chính mình, Admin khác và vai trò lạ |
| Giáo viên | Sinh viên trong lớp của mình | Sinh viên trong lớp của mình |

Trang lớp học phần chỉ mở được với lớp do chính Giáo viên tạo (backend trả 403 với lớp khác),
nên mọi Sinh viên trong danh sách đều thuộc phạm vi Giáo viên đó.

## Khoá / mở khoá

1. Nhấn nút → hộp xác nhận ghi tên, MSSV (nếu có) và hệ quả:
   - Khoá: tài khoản bị đăng xuất khỏi mọi thiết bị, không đăng nhập được cho tới khi mở khoá.
   - Mở khoá: người dùng phải đăng nhập lại từ đầu.
2. Xác nhận → gọi API. Thành công: toast "Đã khoá / Đã mở khoá tài khoản {tên}".
3. Lỗi: toast hiện nguyên `message` của backend, ví dụ:
   - `NOT_ALLOWED_TO_MANAGE_ACCOUNT` → "Bạn không có quyền quản lý tài khoản này".
   - Giáo viên mở khoá tài khoản do Admin khoá → "Tài khoản này chỉ Quản trị viên mới được mở khoá".
   - `CONFLICT` (409) → "Trạng thái tài khoản vừa thay đổi, vui lòng thử lại".
4. Thành công hay lỗi đều tải lại danh sách, vì trạng thái trên màn hình có thể đã cũ
   (người khác vừa khoá/mở khoá).

Giao diện không biết ai đã khoá (`locked_by` không có trong response), nên Giáo viên vẫn thấy
nút "Mở khoá" ở tài khoản do Admin khoá; backend từ chối và toast giải thích.

## Sửa tài khoản

- Form theo vai trò tài khoản đích: Giáo viên/Admin sửa **họ tên, email**; Sinh viên sửa
  **họ tên, MSSV, lớp hành chính** (không có ô email; dòng gợi ý email tự đổi thành `<MSSV>@st.utc2.edu.vn`).
- Kiểm tra trước khi gửi: họ tên không rỗng, email có đuôi `@st.utc2.edu.vn`, MSSV đúng 10 chữ số,
  mã lớp không rỗng.
- Chỉ gửi field thực sự đổi và hợp với vai trò, nên bình thường không gặp `FIELD_NOT_EDITABLE`.
  Không có gì thay đổi thì đóng form, toast "Không có thay đổi nào", không gọi API.
- Lỗi backend (409 trùng email/MSSV, 404 lớp không tồn tại, 422...) hiện trong form và toast,
  form giữ nguyên để sửa tiếp.

## Tài khoản bị khoá (`ACCOUNT_LOCKED`)

| Tình huống | Giao diện |
|---|---|
| Đang dùng hệ thống, API bất kỳ trả 403 `ACCOUNT_LOCKED` | Xoá access token và cache dữ liệu (React Query), không gọi refresh, chuyển về `/login` với thông báo "Tài khoản đã bị khoá. Vui lòng liên hệ quản trị viên hoặc giảng viên để được mở khoá." |
| Access token hết hạn (401), refresh trả 403 `ACCOUNT_LOCKED` | Như trên |
| Tải lại trang, refresh lúc khởi động trả 403 `ACCOUNT_LOCKED` | Ở trang đăng nhập kèm thông báo khoá |
| Đăng nhập đúng mật khẩu vào tài khoản bị khoá | Hiện thông báo khoá + toast; ô mật khẩu **không** bị đánh dấu sai |
| Đăng nhập sai mật khẩu (kể cả tài khoản bị khoá) | Lỗi chung "Email hoặc mật khẩu không đúng", không lộ trạng thái khoá |

Lần đăng nhập tiếp theo xoá thông báo khoá cũ. Các lỗi 403 khác (`FORBIDDEN`,
`NOT_ALLOWED_TO_MANAGE_ACCOUNT`...) không đăng xuất người dùng.

Cài đặt: `frontend/src/lib/axios.ts` (interceptor, lý do kết thúc phiên `account-locked`),
`frontend/src/context/auth-context.tsx` (`reason` của trạng thái `unauthenticated`),
`frontend/src/components/shared/account-actions.tsx` (badge, hộp xác nhận, form sửa).
