# Đặc tả Use-case

## Module: Quản lý lớp hành chính (Class)

> Lớp hành chính là lớp sinh hoạt cố định của Sinh viên (vd `CQ.67.CNTT`), khác với lớp học (Course) do Giáo viên tạo để giao bài tập. Lớp hành chính còn được **tự tạo khi import danh sách Sinh viên từ Excel** (use-case "Cấp phát tài khoản Sinh viên hàng loạt bằng Excel" trong [use-cases-auth.md](use-cases-auth.md)). Các use-case dưới đây dùng cho trường hợp cần tạo, đổi mã hoặc dọn lớp bằng tay, ví dụ trước khi cấp tài khoản cho một Sinh viên lẻ vào lớp chưa từng được import.

### Use-case: Tạo lớp hành chính

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên tạo một lớp hành chính mới, để có thể cấp tài khoản Sinh viên vào lớp đó |
| **Trigger** | Admin/Giáo viên nhấn nút "Tạo lớp hành chính" |
| **Pre-condition** | Admin/Giáo viên đã đăng nhập thành công vào hệ thống<br>Thiết bị phải kết nối Internet<br>Mã lớp ghép từ hệ, khoá, ngành chưa tồn tại trong hệ thống |
| **Post-condition** | Lớp hành chính mới được tạo trong database với `class_id = <hệ>.<khoá>.<ngành>` (vd `CQ.67.CNTT`), chưa có Sinh viên nào |
| **Basic flow** | 1. Hệ thống hiển thị trang quản lý lớp hành chính<br>2. Admin/Giáo viên chọn chức năng "Tạo lớp hành chính"<br>3. Hệ thống hiển thị form nhập thông tin lớp<br>4. Admin/Giáo viên nhập hệ đào tạo (`type`, vd `CQ`), khoá (`course_number`, vd `67`), ngành (`department`, vd `CNTT`)<br>5. Hệ thống kiểm tra định dạng dữ liệu (hệ và ngành không rỗng, hệ chỉ gồm chữ cái không dấu, ngành chỉ gồm chữ cái, chữ số và các ký tự `.` `&` `-`, khoá là số nguyên dương, mã lớp ghép ra không quá 50 ký tự)<br>&nbsp;&nbsp;&nbsp;5a. Nếu định dạng không hợp lệ, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;5b. Nếu định dạng hợp lệ, use-case tiếp tục ở bước 6<br>6. Hệ thống ghép mã lớp `<hệ>.<khoá>.<ngành>` và kiểm tra mã lớp đã tồn tại trong database chưa<br>&nbsp;&nbsp;&nbsp;6a. Nếu đã tồn tại, hệ thống hiển thị thông báo lỗi "Lớp `<mã lớp>` đã tồn tại", use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;6b. Nếu chưa tồn tại, use-case tiếp tục ở bước 7<br>7. Hệ thống tạo lớp hành chính mới<br>8. Hệ thống hiển thị thông báo tạo thành công kèm mã lớp vừa tạo |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 4-8, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên dữ liệu đã nhập, use-case tiếp tục ở bước 3 |

### Use-case: Xem danh sách lớp hành chính

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên xem toàn bộ lớp hành chính trong hệ thống kèm số lượng Sinh viên của từng lớp |
| **Trigger** | Admin/Giáo viên vào trang "Lớp hành chính" |
| **Pre-condition** | Admin/Giáo viên đã đăng nhập thành công vào hệ thống |
| **Post-condition** | Không thay đổi dữ liệu (chỉ đọc) |
| **Basic flow** | 1. Hệ thống hiển thị trang "Lớp hành chính"<br>2. Hệ thống kiểm tra vai trò của người dùng đang đăng nhập<br>&nbsp;&nbsp;&nbsp;2a. Nếu không phải Admin hoặc Giáo viên, hệ thống hiển thị thông báo lỗi "Bạn không có quyền thực hiện hành động này", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;2b. Nếu hợp lệ, use-case tiếp tục ở bước 3<br>3. Hệ thống truy vấn toàn bộ lớp hành chính kèm số lượng Sinh viên của từng lớp, sắp xếp theo mã lớp<br>4. Hệ thống hiển thị danh sách lớp hành chính |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 2-4, nếu truy vấn thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case kết thúc |

### Use-case: Xem chi tiết lớp hành chính

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên xem thông tin một lớp hành chính (hệ, khoá, ngành, số lượng Sinh viên) |
| **Trigger** | Admin/Giáo viên chọn 1 lớp trong danh sách lớp hành chính |
| **Pre-condition** | Admin/Giáo viên đã đăng nhập thành công vào hệ thống |
| **Post-condition** | Không thay đổi dữ liệu (chỉ đọc) |
| **Basic flow** | 1. Admin/Giáo viên chọn 1 lớp trong danh sách lớp hành chính<br>2. Hệ thống kiểm tra lớp có tồn tại không<br>&nbsp;&nbsp;&nbsp;2a. Nếu không tồn tại, hệ thống hiển thị thông báo lỗi "Không tìm thấy lớp `<mã lớp>`", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;2b. Nếu tồn tại, use-case tiếp tục ở bước 3<br>3. Hệ thống hiển thị thông tin lớp; danh sách Sinh viên của lớp được lấy từ chức năng xem danh sách tài khoản, lọc theo lớp |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 2-3, nếu truy vấn thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case kết thúc |

### Use-case: Đổi mã lớp hành chính

| | |
|---|---|
| **Description** | Admin sửa hệ, khoá hoặc ngành của một lớp hành chính (vd lớp gõ sai khoá), toàn bộ Sinh viên của lớp được chuyển sang mã lớp mới |
| **Trigger** | Admin chọn 1 lớp trong danh sách lớp hành chính, nhấn nút "Sửa lớp" |
| **Pre-condition** | Admin đã đăng nhập thành công vào hệ thống<br>Lớp hành chính tồn tại<br>Mã lớp mới ghép từ hệ, khoá, ngành chưa thuộc lớp nào khác |
| **Post-condition** | Lớp với mã mới được tạo, mọi Sinh viên của lớp cũ chuyển sang mã mới, lớp cũ bị xoá. Ghi danh lớp học phần của Sinh viên không thay đổi |
| **Basic flow** | 1. Admin chọn 1 lớp trong danh sách lớp hành chính, nhấn nút "Sửa lớp"<br>2. Hệ thống hiển thị form với hệ đào tạo, khoá, ngành hiện tại của lớp<br>3. Admin sửa hệ đào tạo (`type`), khoá (`course_number`), ngành (`department`) và nhấn "Lưu"<br>4. Hệ thống kiểm tra vai trò người thực hiện<br>&nbsp;&nbsp;&nbsp;4a. Nếu không phải Admin (kể cả Giáo viên), hệ thống hiển thị thông báo lỗi "Bạn không có quyền thực hiện hành động này", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;4b. Nếu là Admin, use-case tiếp tục ở bước 5<br>5. Hệ thống kiểm tra định dạng dữ liệu (giống bước 5 của use-case "Tạo lớp hành chính")<br>&nbsp;&nbsp;&nbsp;5a. Nếu định dạng không hợp lệ, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 3<br>&nbsp;&nbsp;&nbsp;5b. Nếu định dạng hợp lệ, use-case tiếp tục ở bước 6<br>6. Hệ thống kiểm tra lớp hiện tại có tồn tại không<br>&nbsp;&nbsp;&nbsp;6a. Nếu không tồn tại, hệ thống hiển thị thông báo lỗi "Không tìm thấy lớp `<mã lớp>`", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;6b. Nếu tồn tại, use-case tiếp tục ở bước 7<br>7. Hệ thống ghép mã lớp mới `<hệ>.<khoá>.<ngành>` và so sánh<br>&nbsp;&nbsp;&nbsp;7a. Nếu mã mới đã thuộc một lớp khác, hệ thống hiển thị thông báo lỗi "Lớp `<mã lớp mới>` đã tồn tại", use-case tiếp tục ở bước 3<br>&nbsp;&nbsp;&nbsp;7b. Nếu mã mới trùng mã hiện tại, hệ thống không thay đổi gì, use-case tiếp tục ở bước 9<br>&nbsp;&nbsp;&nbsp;7c. Nếu mã mới chưa tồn tại, use-case tiếp tục ở bước 8<br>8. Trong cùng một giao dịch, hệ thống tạo lớp với mã mới, chuyển toàn bộ Sinh viên của lớp cũ sang mã mới, rồi xoá lớp cũ<br>9. Hệ thống hiển thị thông báo cập nhật thành công kèm mã lớp mới và số Sinh viên của lớp |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 3-9, nếu request thất bại → không thay đổi dữ liệu (lưu trong một giao dịch), hệ thống hiển thị thông báo lỗi kết nối, use-case tiếp tục ở bước 2<br>**E2. Có Sinh viên được thêm vào lớp cũ ngay lúc đang đổi mã** (trong bước 8): hệ thống huỷ toàn bộ thay đổi, hiển thị thông báo lỗi "Lớp `<mã lớp>` vừa có sinh viên mới, vui lòng thử lại", use-case tiếp tục ở bước 3 |

### Use-case: Xoá lớp hành chính

| | |
|---|---|
| **Description** | Admin xoá một lớp hành chính không còn Sinh viên, ví dụ lớp tạo nhầm do gõ sai hệ, khoá hoặc ngành |
| **Trigger** | Admin chọn 1 lớp trong danh sách lớp hành chính, nhấn nút "Xoá lớp" |
| **Pre-condition** | Admin đã đăng nhập thành công vào hệ thống<br>Lớp hành chính tồn tại và không còn Sinh viên nào |
| **Post-condition** | Lớp hành chính bị xoá khỏi database; không tài khoản nào bị thay đổi |
| **Basic flow** | 1. Admin chọn 1 lớp trong danh sách lớp hành chính, nhấn nút "Xoá lớp"<br>2. Hệ thống hiển thị hộp thoại xác nhận<br>3. Admin xác nhận<br>4. Hệ thống kiểm tra vai trò người thực hiện<br>&nbsp;&nbsp;&nbsp;4a. Nếu không phải Admin (kể cả Giáo viên), hệ thống hiển thị thông báo lỗi "Bạn không có quyền thực hiện hành động này", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;4b. Nếu là Admin, use-case tiếp tục ở bước 5<br>5. Hệ thống kiểm tra lớp có tồn tại không<br>&nbsp;&nbsp;&nbsp;5a. Nếu không tồn tại, hệ thống hiển thị thông báo lỗi "Không tìm thấy lớp `<mã lớp>`", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;5b. Nếu tồn tại, use-case tiếp tục ở bước 6<br>6. Hệ thống kiểm tra lớp còn Sinh viên không<br>&nbsp;&nbsp;&nbsp;6a. Nếu còn, hệ thống hiển thị thông báo lỗi "Lớp `<mã lớp>` đang có N sinh viên, không thể xóa", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;6b. Nếu không còn, use-case tiếp tục ở bước 7<br>7. Hệ thống xoá lớp hành chính<br>8. Hệ thống hiển thị thông báo xoá thành công |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 3-8, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case tiếp tục ở bước 1<br>**E2. Có Sinh viên được thêm vào lớp ngay lúc đang xoá** (sau bước 6, trước khi bước 7 hoàn tất): hệ thống không xoá lớp, hiển thị thông báo lỗi "Lớp `<mã lớp>` đang có sinh viên, không thể xóa", use-case kết thúc |
