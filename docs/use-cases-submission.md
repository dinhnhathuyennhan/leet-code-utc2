# Đặc tả Use-case

## Module: Theo dõi và xử lý bài nộp (Submission)

Các use-case quản lý Submission hiện chỉ bao gồm bài thuộc Lesson/Course vì quyền xem được giới hạn theo Course. Problem bank với `lesson_id = null` không xuất hiện trong các luồng này. Khi bank Problem được sao chép vào Lesson, bản sao có `problem_id` riêng và Submission cũ không được sao chép.

### Use-case: Xem danh sách bài nộp cần xử lý

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên theo dõi các Submission đang pending, sai kết quả hoặc lỗi biên dịch |
| **Trigger** | Admin/Giáo viên mở màn hình bài nộp cần xử lý |
| **Pre-condition** | Đã đăng nhập với vai trò Admin hoặc Teacher |
| **Post-condition** | Không thay đổi dữ liệu |
| **Basic flow** | 1. Người dùng gửi filter, từ khóa tìm kiếm và giới hạn kết quả<br>2. Hệ thống lấy Submission có status pending, wrong_answer hoặc compile_error<br>3. Teacher chỉ nhận Submission thuộc Course mình quản lý; Admin nhận toàn bộ<br>4. Hệ thống áp dụng filter/search và trả danh sách cùng counts |
| **Exception flow** | **E1. Filter ngoài tập hỗ trợ**: hệ thống trả dữ liệu theo nhánh mặc định hiện tại<br>**E2. Lỗi truy vấn**: hệ thống trả lỗi chung |

### Use-case: Xem chi tiết bài nộp

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên xem code, kết quả và testcase của một Submission |
| **Trigger** | Người dùng chọn một Submission trong danh sách |
| **Pre-condition** | Đã đăng nhập với vai trò Admin/Teacher; Submission nằm trong phạm vi được xem |
| **Post-condition** | Không thay đổi dữ liệu |
| **Basic flow** | 1. Người dùng yêu cầu chi tiết theo `submission_id`<br>2. Hệ thống kiểm tra vai trò và phạm vi Course<br>3. Hệ thống lấy thông tin Student, Course, Lesson, Problem, code, trạng thái, feedback, số test đạt và testcase<br>4. Hệ thống trả chi tiết Submission |
| **Exception flow** | **E1. Submission không tồn tại hoặc ngoài phạm vi Teacher**: trả lỗi 404<br>**E2. Người gọi không phải Admin/Teacher**: trả lỗi 403 |

### Use-case: Cập nhật phản hồi hoặc trạng thái

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên ghi feedback hoặc điều chỉnh trạng thái Submission |
| **Trigger** | Người dùng chỉnh phản hồi/trạng thái và lưu |
| **Pre-condition** | Đã đăng nhập với vai trò Admin/Teacher; Submission nằm trong phạm vi được quản lý |
| **Post-condition** | Feedback và/hoặc status được cập nhật |
| **Basic flow** | 1. Người dùng gửi `feedback` và/hoặc `status`<br>2. Hệ thống kiểm tra Submission và quyền truy cập<br>3. Hệ thống xác thực status thuộc `pending`, `accepted`, `wrong_answer`, `compile_error`<br>4. Hệ thống lưu thay đổi và trả chi tiết Submission |
| **Exception flow** | **E1. Status không hợp lệ**: trả lỗi 422, không cập nhật<br>**E2. Submission không tồn tại/ngoài phạm vi**: trả lỗi 404<br>**E3. Người gọi không có quyền**: trả lỗi 403 |

**Phạm vi hiện tại:** các use case Student tạo Submission, Run code, Judge0 async, deadline, Assignment snapshot và công bố điểm chưa được triển khai trong API hiện có.
