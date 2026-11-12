# Đặc tả Use-case

## Module: Quản lý bài tập (Problem)

### Use-case: Tạo Problem trong ngân hàng

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên tạo Problem chưa gắn Lesson để có thể tìm và sử dụng lại |
| **Trigger** | Admin/Giáo viên chọn chức năng tạo Problem |
| **Pre-condition** | Đã đăng nhập với vai trò Admin hoặc Teacher |
| **Post-condition** | Problem được tạo với `lesson_id = null`, chưa thuộc Course nào; có 10–50 testcase, ít nhất 3 mẫu và 5 hidden testcase |
| **Basic flow** | 1. Người dùng nhập tiêu đề, mã bài tùy chọn (`report`), đề bài, ràng buộc, kiểu chấm, mức độ, giới hạn thời gian, starter code và thời gian mở/hạn<br>2. Với function-call, người dùng nhập tên hàm và testcase JSON; với stdin/stdout, để trống tên hàm và nhập testcase dạng chuỗi<br>3. Hệ thống kiểm tra field, ngôn ngữ, datetime, format testcase, số lượng 10–50, tối thiểu 3 mẫu và 5 hidden<br>4. Hệ thống tạo Problem và testcase<br>5. Hệ thống trả ProblemDetailResponse |
| **Exception flow** | **E1. Dữ liệu sai, testcase ngoài giới hạn 10–50, thiếu mẫu/hidden tối thiểu, thiếu UTC offset hoặc lịch không hợp lệ**: hệ thống trả lỗi 422, không tạo Problem<br>**E2. Lỗi lưu dữ liệu**: hệ thống trả lỗi và không tạo dữ liệu một phần |

### Use-case: Tìm Problem

| | |
|---|---|
| **Description** | Admin/Giáo viên tìm và lọc Problem để xem hoặc đưa vào Lesson |
| **Trigger** | Người dùng mở danh sách Problem hoặc nhập tiêu chí tìm kiếm |
| **Pre-condition** | Đã đăng nhập với vai trò Admin hoặc Teacher |
| **Post-condition** | Không thay đổi dữ liệu |
| **Basic flow** | 1. Người dùng gửi tùy chọn `q`, `level`, `course_id`, `page`, `page_size`<br>2. Hệ thống xác thực mức độ và phân trang<br>3. Teacher thấy toàn bộ Problem bank và bài thuộc Course mình quản lý; Admin thấy tất cả<br>4. Nếu có `course_id`, hệ thống chỉ lọc bài thuộc Course đó; bài bank không thuộc Course nên không nằm trong kết quả lọc này<br>5. Hệ thống trả danh sách, tổng số và thông tin trang |
| **Exception flow** | **E1. Mức độ không hợp lệ**: trả lỗi 422<br>**E2. Page/page_size sai giới hạn**: trả lỗi validation 422 |

### Use-case: Import Problem từ file JSON

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên nhập một hoặc nhiều Problem vào ngân hàng từ file JSON đã chuẩn hóa theo schema của hệ thống |
| **Trigger** | Người dùng chọn Import JSON tại ngân hàng đề và gửi file |
| **Pre-condition** | Đã đăng nhập với vai trò Admin hoặc Teacher; file `.json` không quá 25 MB và có tối đa 5.000 Problem |
| **Post-condition** | Tất cả Problem và testcase hợp lệ được tạo trong bank (`lesson_id = null`); hoặc không có dữ liệu nào được tạo nếu import thất bại |
| **Basic flow** | 1. Người dùng chọn file JSON dạng một Problem, danh sách Problem hoặc object `{ "problems": [...] }`; mỗi bài có thể kèm mã tùy chọn `report`<br>2. Với `function_name`, testcase dùng mảng input và output JSON; khi bỏ/null `function_name`, testcase dùng stdin/stdout dạng chuỗi<br>3. Hệ thống preview schema, số bài/testcase, lỗi và nội dung problem lặp; mỗi bài cần 10–50 testcase, ít nhất 3 mẫu và 5 hidden<br>4. Người dùng xác nhận; hệ thống kiểm tra lại và tạo các Problem cùng testcase trong một transaction<br>5. Hệ thống trả số lượng và danh sách ID/mã/tên Problem vừa tạo |
| **Exception flow** | **E1. File hoặc một Problem sai định dạng, starter C/C++ không dựng được harness, trùng nội dung trong file hoặc trùng bài nguồn trong bank**: preview hiển thị lỗi theo số thứ tự Problem và field liên quan; import trả 422, không tự xóa starter và không tạo bài nào<br>**E2. Lỗi lưu dữ liệu**: rollback toàn bộ transaction<br>**E3. File quá lớn hoặc quá nhiều bài**: trả lỗi 422 |

### Use-case: Gắn Problem vào Lesson

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên đưa Problem vào một Lesson; bài bank hoặc bài ở Lesson khác được sao chép thành bản riêng cho Lesson đích |
| **Trigger** | Người dùng chọn Problem và yêu cầu thêm vào Lesson |
| **Pre-condition** | Đã đăng nhập; Course/Lesson đích tồn tại; người dùng có quyền quản lý Course |
| **Post-condition** | Lesson có Problem riêng với `lesson_id` đích; nguồn bank vẫn giữ `lesson_id = null`; testcase được sao chép, Submission không được sao chép |
| **Basic flow** | 1. Người dùng gửi danh sách `problem_ids`<br>2. Hệ thống kiểm tra quyền quản lý Course và sự tồn tại của Problem<br>3. Problem bank được mọi Teacher dùng chung; Problem thuộc Course khác chỉ được Teacher sao chép khi là chủ Course nguồn<br>4. Nếu Problem đã nằm trong Lesson đích, hệ thống giữ nguyên; nếu là bài bank hoặc thuộc Lesson khác, hệ thống tạo Problem mới cùng testcase, giữ nguyên `report`, tạo `problem_id` mới và dùng ngày Lesson đích cho `start_datetime`/`end_datetime`<br>5. Hệ thống cập nhật số lượng bài và trả Course |
| **Exception flow** | **E1. Danh sách rỗng**: trả lỗi 422<br>**E2. Có ID không tồn tại**: trả lỗi 404<br>**E3. Teacher không có quyền sao chép nguồn**: trả lỗi 403 |

### Use-case: Sửa hoặc xóa Problem trong Lesson

| | |
|---|---|
| **Description** | Admin hoặc chủ Course chỉnh sửa hoặc xóa Problem đã gắn Lesson |
| **Trigger** | Người dùng mở chức năng sửa/xóa Problem |
| **Pre-condition** | Đã đăng nhập; Problem thuộc Lesson trong Course; người dùng có quyền quản lý Course |
| **Post-condition** | Problem được cập nhật hoặc xóa cùng testcase nếu chưa có Submission |
| **Basic flow** | 1. Người dùng gửi các field cần sửa hoặc yêu cầu xóa<br>2. Hệ thống kiểm tra quyền và quan hệ Problem/Lesson/Course<br>3. Nếu sửa testcase, hệ thống thay toàn bộ danh sách sau khi kiểm tra chưa có Submission<br>4. Nếu xóa, hệ thống xóa testcase và Problem sau khi kiểm tra chưa có Submission<br>5. Hệ thống trả dữ liệu mới hoặc 204 |
| **Exception flow** | **E1. Đã có Submission**: sửa/xóa bị từ chối với 409<br>**E2. Problem không thuộc Lesson chỉ định**: trả lỗi 404<br>**E3. Không có quyền quản lý Course**: trả lỗi 403 |

**Giới hạn hiện tại:** Problem bank chưa có archive riêng hoặc Topic. `report` là mã bài tùy chọn, không yêu cầu duy nhất và được trả ra dưới tên `code`; kiểm tra trùng khi import nhận diện nội dung có cùng tên, tên hàm, mô tả và ràng buộc sau khi chuẩn hóa. Testcase được đếm theo số lượng; độ bao phủ theo ý nghĩa của từng đề vẫn cần người quản trị review.
