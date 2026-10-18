# Đặc tả Use-case

## Module: Chấm bài (Giáo viên)

### Use-case: Xem danh sách bài nộp cần xử lý

| | |
|---|---|
| **Description** | Giáo viên hoặc Admin xem các bài nộp cần chú ý (đang chờ chấm, sai kết quả, lỗi biên dịch) để kiểm tra và phản hồi cho Sinh viên |
| **Trigger** | Giáo viên/Admin vào trang "Bài nộp cần xử lý" |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống |
| **Post-condition** | Không thay đổi dữ liệu. Admin thấy bài nộp của mọi lớp; Giáo viên chỉ thấy bài nộp thuộc các lớp học do mình tạo |
| **Basic flow** | 1. Giáo viên/Admin vào trang "Bài nộp cần xử lý"<br>2. Giáo viên/Admin có thể chọn bộ lọc (tất cả / lỗi biên dịch) và nhập từ khoá tìm kiếm (mã hoặc tên Sinh viên, mã hoặc tên lớp, mã hoặc tên bài)<br>3. Hệ thống lấy bài nộp trong phạm vi được xem, chỉ giữ các bài có trạng thái `pending`, `wrong_answer`, `compile_error`<br>4. Hệ thống áp dụng tìm kiếm và bộ lọc, sắp xếp bài mới nộp lên trước<br>5. Hệ thống hiển thị danh sách (Sinh viên, lớp, buổi, bài, trạng thái chấm, mô tả lỗi như "Sai 3/10 test case") kèm số lượng theo từng bộ lọc |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 3-4, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case tiếp tục ở bước 1 |

### Use-case: Xem chi tiết bài nộp

| | |
|---|---|
| **Description** | Giáo viên hoặc Admin xem toàn bộ thông tin một bài nộp: code Sinh viên nộp, ngôn ngữ, kết quả chấm, thông báo biên dịch và testcase của bài |
| **Trigger** | Giáo viên/Admin chọn 1 bài nộp trong danh sách |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Bài nộp tồn tại |
| **Post-condition** | Không thay đổi dữ liệu |
| **Basic flow** | 1. Giáo viên/Admin chọn 1 bài nộp<br>2. Hệ thống tìm bài nộp trong phạm vi được xem (Admin mọi lớp, Giáo viên lớp mình tạo)<br>&nbsp;&nbsp;&nbsp;2a. Nếu không tìm thấy hoặc bài nộp thuộc lớp khác, hệ thống hiển thị thông báo lỗi "Không tìm thấy bài nộp", use-case kết thúc<br>3. Hệ thống trả thông tin Sinh viên, lớp, buổi, bài, ngôn ngữ, code đã nộp, trạng thái, số testcase đạt trên tổng, thông báo biên dịch, nhận xét và danh sách testcase<br>4. Hệ thống hiển thị trang chi tiết bài nộp |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 2-3, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case tiếp tục ở bước 1 |

### Use-case: Cập nhật kết quả chấm

| | |
|---|---|
| **Description** | Giáo viên hoặc Admin đổi trạng thái chấm hoặc viết nhận xét cho một bài nộp, ví dụ chấp nhận bài sau khi xem lại code |
| **Trigger** | Giáo viên/Admin đang xem chi tiết bài nộp, sửa trạng thái/nhận xét và nhấn "Lưu" |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Bài nộp tồn tại và thuộc phạm vi Giáo viên/Admin được xem |
| **Post-condition** | Trạng thái và/hoặc nhận xét của bài nộp được cập nhật; nhận xét chỉ toàn khoảng trắng được lưu là rỗng |
| **Basic flow** | 1. Giáo viên/Admin chọn trạng thái mới và/hoặc nhập nhận xét (tối đa 10.000 ký tự)<br>2. Giáo viên/Admin nhấn "Lưu"<br>3. Hệ thống tìm bài nộp trong phạm vi được xem<br>&nbsp;&nbsp;&nbsp;3a. Nếu không tìm thấy, hệ thống hiển thị thông báo lỗi "Không tìm thấy bài nộp", use-case kết thúc<br>4. Hệ thống kiểm tra trạng thái thuộc danh sách cho phép (`pending`, `accepted`, `wrong_answer`, `compile_error`)<br>&nbsp;&nbsp;&nbsp;4a. Nếu không, hệ thống hiển thị thông báo lỗi "Trạng thái bài nộp không hợp lệ", use-case tiếp tục ở bước 1<br>5. Hệ thống lưu thay đổi và hiển thị chi tiết bài nộp sau khi cập nhật |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 3-5, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên dữ liệu đã nhập, use-case tiếp tục ở bước 1 |

## Module: Nộp bài (Sinh viên)

> Hai use-case dưới đây là **thiết kế cho Phase 3** trong [roadmap.md](roadmap.md), chưa được triển khai trong code (chưa có `judge_client.py`, `POST /problems/{id}/run`, `POST /problems/{id}/submissions`). Khi code xong cần đối chiếu và sửa lại cho khớp.

### Use-case: Chạy thử code

| | |
|---|---|
| **Description** | Sinh viên chạy code của mình trên các testcase mẫu để kiểm tra trước khi nộp; kết quả không được lưu |
| **Trigger** | Sinh viên nhấn nút "Chạy thử" ở trang làm bài |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Sinh viên đã được thêm vào lớp học chứa bài tập<br>Bài tập đã mở (`start_datetime` đã qua)<br>Hệ thống chấm Judge0 đang hoạt động |
| **Post-condition** | Không thay đổi dữ liệu; Sinh viên nhận kết quả từng testcase mẫu |
| **Basic flow** | 1. Sinh viên viết code, chọn ngôn ngữ và nhấn "Chạy thử"<br>2. Hệ thống kiểm tra Sinh viên được xem bài và bài đã mở<br>&nbsp;&nbsp;&nbsp;2a. Nếu không, hệ thống hiển thị thông báo lỗi, use-case kết thúc<br>3. Hệ thống kiểm tra ngôn ngữ được hỗ trợ (Python, C++, Java, C) và kích thước code trong giới hạn<br>&nbsp;&nbsp;&nbsp;3a. Nếu không, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 1<br>4. Hệ thống gửi code cùng các testcase mẫu sang Judge0<br>5. Judge0 biên dịch, chạy và trả kết quả từng testcase<br>6. Hệ thống hiển thị kết quả: đạt/không đạt, output thực tế so với output mong đợi, thông báo biên dịch nếu lỗi |
| **Exception flow** | **E1. Judge0 không phản hồi**: ở bước 4-5, nếu Judge0 lỗi hoặc quá thời gian → hệ thống hiển thị thông báo "Hệ thống chấm đang bận, vui lòng thử lại", use-case tiếp tục ở bước 1 |

### Use-case: Nộp bài

| | |
|---|---|
| **Description** | Sinh viên nộp code chính thức; hệ thống lưu bài nộp và chấm tự động trên toàn bộ testcase (cả testcase ẩn) |
| **Trigger** | Sinh viên nhấn nút "Nộp bài" ở trang làm bài |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Sinh viên đã được thêm vào lớp học chứa bài tập<br>Bài tập đang trong thời hạn (giữa `start_datetime` và `end_datetime`) |
| **Post-condition** | Bài nộp mới được lưu với trạng thái ban đầu `pending`, sau khi chấm xong được cập nhật thành `accepted`, `wrong_answer` hoặc `compile_error` cùng `passed_count` |
| **Basic flow** | 1. Sinh viên viết code, chọn ngôn ngữ và nhấn "Nộp bài"<br>2. Hệ thống kiểm tra Sinh viên đã được thêm vào lớp và bài còn trong thời hạn<br>&nbsp;&nbsp;&nbsp;2a. Nếu không, hệ thống hiển thị thông báo lỗi không được nộp, use-case kết thúc<br>3. Hệ thống kiểm tra ngôn ngữ, kích thước code và tần suất nộp<br>&nbsp;&nbsp;&nbsp;3a. Nếu vi phạm, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 1<br>4. Hệ thống lưu bài nộp với trạng thái `pending` và trả mã bài nộp ngay cho Sinh viên<br>5. Hệ thống chấm ở nền: gửi code cùng toàn bộ testcase sang Judge0<br>6. Judge0 trả kết quả từng testcase; hệ thống tổng hợp trạng thái và số testcase đạt rồi cập nhật bài nộp<br>7. Trang làm bài tự kiểm tra trạng thái bài nộp cho tới khi chấm xong<br>8. Hệ thống hiển thị kết quả chấm: trạng thái, số testcase đạt trên tổng (không lộ nội dung testcase ẩn) |
| **Exception flow** | **E1. Judge0 không phản hồi**: ở bước 5-6, nếu Judge0 lỗi → bài nộp vẫn được lưu, giữ trạng thái `pending` để chấm lại; Sinh viên được thông báo bài đang chờ chấm<br>**E2. Mất kết nối khi nộp**: ở bước 1-4, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên code đã viết, use-case tiếp tục ở bước 1 |
