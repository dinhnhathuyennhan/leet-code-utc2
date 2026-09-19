# Đặc tả Use-case

## Module: Quản lý lớp học (Course)

### Use-case: Tạo lớp học

| | |
|---|---|
| **Description** | Giáo viên (hoặc Admin) tạo một lớp học mới để quản lý Sinh viên và bài tập trong lớp |
| **Trigger** | Giáo viên/Admin nhấn nút "Tạo lớp học" |
| **Pre-condition** | Giáo viên/Admin đã đăng nhập thành công vào hệ thống<br>Thiết bị phải kết nối Internet<br>Mã lớp học (`course_id`) chưa tồn tại trong hệ thống |
| **Post-condition** | Lớp học mới được tạo trong database với `created_by` = `user_id` của người tạo, `total_number_student = 0` |
| **Basic flow** | 1. Hệ thống hiển thị trang quản lý lớp học<br>2. Giáo viên/Admin chọn chức năng "Tạo lớp học"<br>3. Hệ thống hiển thị form nhập thông tin lớp học<br>4. Giáo viên/Admin nhập mã lớp (`course_id`), tên lớp (`course_name`), học kỳ (`term`), ngày bắt đầu (`start_date`), ngày kết thúc (`end_date`)<br>5. Hệ thống kiểm tra định dạng dữ liệu (các trường bắt buộc không rỗng, `start_date` phải trước `end_date`)<br>&nbsp;&nbsp;&nbsp;5a. Nếu định dạng không hợp lệ, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;5b. Nếu định dạng hợp lệ, use-case tiếp tục ở bước 6<br>6. Hệ thống kiểm tra `course_id` đã tồn tại trong database chưa<br>&nbsp;&nbsp;&nbsp;6a. Nếu đã tồn tại, hệ thống hiển thị thông báo lỗi "Mã lớp học đã tồn tại", use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;6b. Nếu chưa tồn tại, use-case tiếp tục ở bước 7<br>7. Hệ thống tạo lớp học mới với `created_by` = `user_id` của người đang đăng nhập, `total_number_student = 0`<br>8. Hệ thống hiển thị thông báo tạo thành công |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 4-8, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên dữ liệu đã nhập, use-case tiếp tục ở bước 3 |

### Use-case: Xem danh sách lớp học

| | |
|---|---|
| **Description** | Người dùng xem danh sách lớp học; kết quả trả về được giới hạn theo vai trò để không lộ dữ liệu của người/lớp khác |
| **Trigger** | Người dùng vào trang "Danh sách lớp học" |
| **Pre-condition** | Người dùng đã đăng nhập thành công vào hệ thống |
| **Post-condition** | Không thay đổi dữ liệu (chỉ đọc) |
| **Basic flow** | 1. Hệ thống hiển thị trang "Danh sách lớp học"<br>2. Hệ thống xác định vai trò của người dùng đang đăng nhập<br>&nbsp;&nbsp;&nbsp;2a. Nếu là Admin, hệ thống truy vấn toàn bộ lớp học trong hệ thống<br>&nbsp;&nbsp;&nbsp;2b. Nếu là Giáo viên, hệ thống chỉ truy vấn các lớp học có `created_by` = `user_id` của Giáo viên đó<br>&nbsp;&nbsp;&nbsp;2c. Nếu là Sinh viên, hệ thống chỉ truy vấn các lớp học mà Sinh viên có `Enrollment`<br>3. Hệ thống hiển thị danh sách lớp học tương ứng |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 2-3, nếu truy vấn thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case kết thúc |

### Use-case: Thêm sinh viên vào lớp

| | |
|---|---|
| **Description** | Giáo viên chủ lớp hoặc Admin thêm một Sinh viên vào lớp học để Sinh viên tham gia làm bài tập trong lớp |
| **Trigger** | Giáo viên/Admin chọn 1 lớp học, nhấn nút "Thêm sinh viên" |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Lớp học (`course_id`) tồn tại<br>Nếu người thực hiện là Giáo viên, phải là người tạo lớp học đó (`created_by = user_id`) |
| **Post-condition** | Một bản ghi `Enrollment` mới được tạo; `total_number_student` của lớp học tăng lên 1 |
| **Basic flow** | 1. Hệ thống hiển thị thông tin lớp học kèm nút "Thêm sinh viên"<br>2. Giáo viên/Admin nhấn nút "Thêm sinh viên", nhập `user_id` của Sinh viên cần thêm<br>3. Hệ thống kiểm tra quyền thực hiện trên lớp học<br>&nbsp;&nbsp;&nbsp;3a. Nếu người thực hiện là Giáo viên và không phải người tạo lớp học này, hệ thống hiển thị thông báo lỗi "Bạn không có quyền thêm sinh viên vào lớp này", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;3b. Nếu hợp lệ, use-case tiếp tục ở bước 4<br>4. Hệ thống kiểm tra `user_id` tồn tại và có `role_id = 3` (Sinh viên)<br>&nbsp;&nbsp;&nbsp;4a. Nếu không tồn tại hoặc không phải Sinh viên, hệ thống hiển thị thông báo lỗi "Không tìm thấy sinh viên", use-case tiếp tục ở bước 2<br>&nbsp;&nbsp;&nbsp;4b. Nếu hợp lệ, use-case tiếp tục ở bước 5<br>5. Hệ thống kiểm tra Sinh viên đã có trong lớp học này chưa<br>&nbsp;&nbsp;&nbsp;5a. Nếu đã có, hệ thống hiển thị thông báo lỗi "Sinh viên đã có trong lớp học", use-case tiếp tục ở bước 2<br>&nbsp;&nbsp;&nbsp;5b. Nếu chưa có, use-case tiếp tục ở bước 6<br>6. Hệ thống tạo bản ghi `Enrollment` mới, tăng `total_number_student` của lớp học lên 1<br>7. Hệ thống hiển thị thông báo thêm thành công |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 2-7, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case tiếp tục ở bước 1 |

### Use-case: Xem danh sách sinh viên trong lớp

| | |
|---|---|
| **Description** | Xem danh sách Sinh viên đã được thêm vào một lớp học cụ thể, giới hạn theo vai trò người xem |
| **Trigger** | Người dùng chọn 1 lớp học, xem tab "Danh sách sinh viên" |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Lớp học (`course_id`) tồn tại |
| **Post-condition** | Không thay đổi dữ liệu (chỉ đọc) |
| **Basic flow** | 1. Người dùng chọn 1 lớp học, xem tab "Danh sách sinh viên"<br>2. Hệ thống kiểm tra quyền xem danh sách sinh viên của lớp học này<br>&nbsp;&nbsp;&nbsp;2a. Nếu là Giáo viên và không phải người tạo lớp học này, hệ thống hiển thị thông báo lỗi "Bạn không có quyền xem lớp học này", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;2b. Nếu là Sinh viên và không có `Enrollment` trong chính lớp học này, hệ thống hiển thị thông báo lỗi "Bạn không có quyền xem lớp học này", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;2c. Nếu hợp lệ (Admin, hoặc Giáo viên chủ lớp, hoặc Sinh viên đã được thêm vào lớp), use-case tiếp tục ở bước 3<br>3. Hệ thống truy vấn danh sách `Enrollment` của lớp học, hiển thị thông tin các Sinh viên tương ứng |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 2-3, nếu truy vấn thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case kết thúc |

### Use-case: Xoá sinh viên khỏi lớp

| | |
|---|---|
| **Description** | Giáo viên chủ lớp hoặc Admin xoá một Sinh viên khỏi lớp học (ví dụ Sinh viên nghỉ học, đăng ký nhầm lớp) |
| **Trigger** | Giáo viên/Admin chọn 1 Sinh viên trong danh sách lớp, nhấn nút "Xoá khỏi lớp" |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Bản ghi `Enrollment` giữa Sinh viên và lớp học tồn tại<br>Nếu người thực hiện là Giáo viên, phải là người tạo lớp học đó |
| **Post-condition** | Bản ghi `Enrollment` bị xoá; `total_number_student` của lớp học giảm đi 1 |
| **Basic flow** | 1. Giáo viên/Admin chọn 1 Sinh viên trong danh sách lớp, nhấn nút "Xoá khỏi lớp"<br>2. Hệ thống hiển thị hộp thoại xác nhận<br>3. Giáo viên/Admin xác nhận<br>4. Hệ thống kiểm tra quyền thực hiện trên lớp học<br>&nbsp;&nbsp;&nbsp;4a. Nếu người thực hiện là Giáo viên và không phải người tạo lớp học này, hệ thống hiển thị thông báo lỗi "Bạn không có quyền thực hiện hành động này", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;4b. Nếu hợp lệ, use-case tiếp tục ở bước 5<br>5. Hệ thống kiểm tra bản ghi `Enrollment` giữa Sinh viên và lớp học có tồn tại không<br>&nbsp;&nbsp;&nbsp;5a. Nếu không tồn tại, hệ thống hiển thị thông báo lỗi "Sinh viên không thuộc lớp học này", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;5b. Nếu tồn tại, use-case tiếp tục ở bước 6<br>6. Hệ thống xoá bản ghi `Enrollment`, giảm `total_number_student` của lớp học đi 1<br>7. Hệ thống hiển thị thông báo xoá thành công |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 3-7, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, không thay đổi dữ liệu, use-case tiếp tục ở bước 2 |
