# Đặc tả Use-case

## Module: Quản lý buổi học (Lesson)

### Use-case: Tạo buổi học

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên tạo một buổi học trong Course và có thể đưa Problem vào buổi ngay khi tạo |
| **Trigger** | Admin/Giáo viên chọn Course và nhấn "Tạo buổi học" |
| **Pre-condition** | Đã đăng nhập; Course tồn tại; nếu là Giáo viên thì là chủ Course |
| **Post-condition** | Lesson được tạo với `lesson_number` tiếp theo; mỗi Problem bank được chọn tạo thành bản riêng của Lesson, kèm testcase |
| **Basic flow** | 1. Người dùng mở Course và chọn tạo Lesson<br>2. Nhập `lesson_name`, `start_date`, `end_date`, có thể gửi `problem_ids`<br>3. Hệ thống kiểm tra tên không rỗng và ngày bắt đầu không sau ngày kết thúc<br>4. Hệ thống kiểm tra quyền quản lý Course<br>5. Hệ thống tạo Lesson, tự gán số thứ tự tiếp theo<br>6. Nếu có Problem, hệ thống kiểm tra quyền sử dụng; bài bank hoặc bài từ Lesson khác được sao chép cùng testcase thành Problem mới, đặt lịch theo ngày Lesson đích và không sao chép Submission<br>7. Hệ thống trả Course mới và thông báo tạo thành công |
| **Exception flow** | **E1. Dữ liệu không hợp lệ**: tại bước 3, trả lỗi 422 và không tạo Lesson<br>**E2. Không có quyền**: tại bước 4 hoặc 6, trả lỗi 403<br>**E3. Problem không tồn tại**: tại bước 6, trả lỗi 404 và thao tác không hoàn tất<br>**E4. Lỗi hệ thống**: thao tác lưu thất bại, client hiển thị lỗi và cho phép thử lại |

### Use-case: Xem chi tiết buổi học

| | |
|---|---|
| **Description** | Người dùng có quyền xem Course đọc thông tin Lesson và các Problem trong buổi |
| **Trigger** | Người dùng mở một Lesson trong Course |
| **Pre-condition** | Đã đăng nhập; Course và Lesson tồn tại; người dùng có quyền xem Course |
| **Post-condition** | Không thay đổi dữ liệu |
| **Basic flow** | 1. Người dùng mở Lesson<br>2. Hệ thống kiểm tra quyền xem Course và Lesson thuộc Course<br>3. Hệ thống lấy các Problem trong Lesson<br>4. Với Student, hệ thống chỉ giữ Problem đã tới `start_datetime`, chỉ trả testcase mẫu và trả các trường thống kê/số lượt nộp là `null`<br>5. Hệ thống trả chi tiết Lesson |
| **Exception flow** | **E1. Không có quyền hoặc không tìm thấy Course/Lesson**: hệ thống trả lỗi tương ứng; không trả dữ liệu chi tiết<br>**E2. Lỗi truy vấn**: hệ thống trả lỗi chung |

### Use-case: Cập nhật và sắp xếp buổi học

| | |
|---|---|
| **Description** | Admin hoặc chủ Course cập nhật thông tin Lesson hoặc thay đổi thứ tự các buổi |
| **Trigger** | Người dùng sửa thông tin Lesson hoặc chọn chức năng sắp xếp |
| **Pre-condition** | Đã đăng nhập; Lesson/Course tồn tại; người dùng có quyền quản lý Course |
| **Post-condition** | Thông tin hoặc thứ tự Lesson được cập nhật |
| **Basic flow** | 1. Người dùng gửi field cần sửa hoặc danh sách `order` gồm các `lesson_id`<br>2. Hệ thống kiểm tra quyền và dữ liệu<br>3. Với reorder, hệ thống xác nhận danh sách chứa chính xác mọi Lesson trong Course, không trùng ID<br>4. Hệ thống cập nhật dữ liệu/thứ tự và trả Course |
| **Exception flow** | **E1. Ngày không hợp lệ**: `start_date` sau `end_date`, trả lỗi 422<br>**E2. Danh sách reorder không hợp lệ**: trả lỗi 422, không cập nhật thứ tự<br>**E3. Không có quyền**: trả lỗi 403 |

### Use-case: Nhân bản buổi học

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên nhân bản Lesson và các Problem/testcase sang một Lesson mới |
| **Trigger** | Người dùng chọn "Nhân bản buổi học" |
| **Pre-condition** | Đã đăng nhập; Lesson nguồn tồn tại; có quyền xem Course nguồn và quản lý Course đích |
| **Post-condition** | Lesson mới được thêm cuối danh sách Course đích với ngày do người dùng chọn; Problem và testcase được sao chép |
| **Basic flow** | 1. Người dùng gửi `new_start_date`, `new_end_date`, tùy chọn `target_course_id`<br>2. Hệ thống kiểm tra ngày hợp lệ và quyền Course nguồn/đích<br>3. Hệ thống tạo Lesson mới, giữ tên nguồn và gán thứ tự tiếp theo<br>4. Hệ thống sao chép Problem/testcase<br>5. Hệ thống trả Course đích |
| **Exception flow** | **E1. Ngày không hợp lệ**: trả lỗi 422<br>**E2. Course đích không tồn tại**: trả lỗi 404<br>**E3. Không có quyền quản lý Course đích**: trả lỗi 403 |

### Use-case: Xóa buổi học

| | |
|---|---|
| **Description** | Admin hoặc chủ Course xóa Lesson chưa có Problem |
| **Trigger** | Người dùng chọn xóa Lesson và xác nhận |
| **Pre-condition** | Đã đăng nhập; Lesson tồn tại; người dùng có quyền quản lý Course |
| **Post-condition** | Lesson bị xóa nếu không còn Problem |
| **Basic flow** | 1. Người dùng yêu cầu xóa Lesson<br>2. Hệ thống kiểm tra quyền và tìm Lesson trong Course<br>3. Hệ thống xác nhận Lesson không có Problem<br>4. Hệ thống xóa Lesson và trả 204 |
| **Exception flow** | **E1. Lesson còn Problem**: trả lỗi 409, không xóa Lesson<br>**E2. Không có quyền hoặc không tìm thấy Lesson**: trả lỗi tương ứng |

**Phạm vi hiện tại:** Problem trong Lesson là bản riêng được lưu trực tiếp bằng `Problem.lesson_id`. Bản nguồn trong bank vẫn có `lesson_id = null`; chưa có Assignment snapshot hoặc lịch sử xóa Lesson.
