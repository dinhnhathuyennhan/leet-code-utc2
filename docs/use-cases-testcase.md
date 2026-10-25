# Đặc tả Use-case

## Module: Quản lý Testcase

Testcase ban đầu của Problem bank được khai báo cùng `POST /problems`. Các use-case dưới đây áp dụng cho Problem đã gắn vào Lesson; nguồn bank không có route riêng để đọc hoặc sửa testcase, còn bản sao trong Lesson dùng các route `BASE`.

### Use-case: Xem testcase

| | |
|---|---|
| **Description** V| Người dùng có quyền xem Course đọc testcase của Problem trong Lesson |
| **Trigger** | Người dùng mở danh sách testcase hoặc chi tiết Problem |
| **Pre-condition** | Đã đăng nhập; Course/Lesson/Problem tồn tại; người dùng có quyền xem Course |
| **Post-condition** | Không thay đổi dữ liệu |
| **Basic flow** | 1. Người dùng yêu cầu danh sách, có thể lọc `is_sample`<br>2. Hệ thống kiểm tra quyền và Problem thuộc Lesson<br>3. Student chỉ nhận testcase mẫu; Admin/Teacher nhận testcase theo filter<br>4. Hệ thống trả danh sách và số lượng sample/hidden |
| **Exception flow** | **E1. Problem chưa mở với Student**: hệ thống trả lỗi 404<br>**E2. Không có quyền/Problem không tồn tại**: hệ thống trả lỗi tương ứng |

### Use-case: Thêm, sửa hoặc xóa testcase

| | |
|---|---|
| **Description** | Admin hoặc chủ Course quản lý testcase của Problem trong Lesson |
| **Trigger** | Người dùng thêm, sửa hoặc xóa testcase |
| **Pre-condition** | Đã đăng nhập; Problem thuộc Lesson; người dùng có quyền quản lý Course; Problem chưa có Submission |
| **Post-condition** | Testcase được tạo, cập nhật hoặc xóa; số lượng testcase của Problem được làm mới khi cần |
| **Basic flow** | 1. Người dùng gửi mảng đối số JSON, output JSON mong đợi hoặc chọn testcase cần sửa/xóa<br>2. Hệ thống kiểm tra quyền, kiểu JSON và testcase thuộc đúng Problem<br>3. Hệ thống kiểm tra Problem chưa có Submission<br>4. Hệ thống lưu thay đổi và trả ProblemDetailResponse (xóa trả 204) |
| **Exception flow** | **E1. Problem đã có Submission**: trả lỗi 409, giữ nguyên testcase<br>**E2. Testcase không tồn tại/không thuộc Problem**: trả lỗi 404<br>**E3. Yêu cầu xóa testcase cuối cùng**: trả lỗi 409, giữ nguyên testcase<br>**E4. Không có quyền**: trả lỗi 403 |

### Use-case: Phân loại testcase mẫu

| | |
|---|---|
| **Description** | Admin hoặc chủ Course đánh dấu một hay nhiều testcase là mẫu hoặc ẩn |
| **Trigger** | Người dùng chọn testcase và đổi trạng thái mẫu |
| **Pre-condition** | Problem chưa có Submission; các ID testcase thuộc Problem |
| **Post-condition** | `is_sample` được cập nhật cho toàn bộ testcase đã chọn |
| **Basic flow** | 1. Người dùng gửi `testcase_ids` và giá trị `is_sample`<br>2. Hệ thống xác nhận danh sách không rỗng và mọi testcase thuộc Problem<br>3. Hệ thống cập nhật trạng thái và trả chi tiết Problem |
| **Exception flow** | **E1. Danh sách rỗng hoặc ID không hợp lệ**: trả lỗi 422/404<br>**E2. Problem đã có Submission**: trả lỗi 409 |

### Use-case: Preview, import và export testcase

| | |
|---|---|
| **Description** | Admin hoặc chủ Course kiểm tra payload, thay toàn bộ testcase từ JSON/ZIP hoặc tải testcase hiện có |
| **Trigger** | Người dùng chọn preview, upload hoặc download testcase |
| **Pre-condition** | Preview cần đăng nhập Admin/Teacher; import/export cần quyền quản lý Course và Problem chưa có Submission nếu import |
| **Post-condition** | Preview không đổi dữ liệu; import thay toàn bộ testcase; export tải JSON hoặc ZIP |
| **Basic flow** | 1. Với preview, hệ thống kiểm tra từng testcase và trả lỗi/cảnh báo theo vị trí<br>2. Với import, hệ thống đọc JSON/ZIP, kiểm tra định dạng, kiểu dữ liệu và giới hạn kích thước<br>3. Nếu toàn bộ payload hợp lệ và Problem chưa có Submission, hệ thống thay testcase trong transaction<br>4. Với export, hệ thống đóng gói toàn bộ testcase, bao gồm testcase ẩn, thành JSON hoặc ZIP |
| **Exception flow** | **E1. File/payload sai hoặc quá lớn**: trả lỗi 422, giữ nguyên testcase cũ<br>**E2. Problem đã có Submission**: import bị từ chối 409<br>**E3. Format export không hỗ trợ**: trả lỗi 422 |

**Giới hạn hiện tại:** các route quản lý testcase yêu cầu Problem đã gắn Lesson; chưa có route testcase riêng cho Problem bank hoặc snapshot Assignment.
