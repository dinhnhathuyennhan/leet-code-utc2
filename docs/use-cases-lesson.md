# Đặc tả Use-case

## Module: Buổi học (Lesson)

### Use-case: Tạo buổi học

| | |
|---|---|
| **Description** | Giáo viên chủ lớp hoặc Admin thêm một buổi học mới vào lớp học, có thể gắn sẵn các bài tập có sẵn vào buổi |
| **Trigger** | Giáo viên/Admin chọn 1 lớp học, nhấn nút "Thêm buổi học" |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Lớp học (`course_id`) tồn tại<br>Nếu người thực hiện là Giáo viên, Giáo viên đó phải là người tạo lớp học (`created_by`) |
| **Post-condition** | Buổi học mới được tạo với `lesson_number` = số thứ tự lớn nhất hiện có của lớp + 1; các bài tập được chọn được gắn vào buổi (bài thuộc buổi khác được sao chép thành bài mới, kèm testcase, thời gian mở/đóng theo ngày của buổi); `total_number_assignment` bằng số bài trong buổi |
| **Basic flow** | 1. Hệ thống hiển thị form tạo buổi học<br>2. Giáo viên/Admin nhập tên buổi, ngày bắt đầu, ngày kết thúc và (tuỳ chọn) chọn các bài tập muốn gắn vào buổi<br>3. Hệ thống kiểm tra định dạng (tên buổi không rỗng, tối đa 255 ký tự; ngày bắt đầu trước hoặc bằng ngày kết thúc)<br>&nbsp;&nbsp;&nbsp;3a. Nếu không hợp lệ, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 2<br>4. Hệ thống kiểm tra lớp học tồn tại và quyền quản lý: Admin mọi lớp, Giáo viên chỉ lớp mình tạo<br>&nbsp;&nbsp;&nbsp;4a. Nếu lớp không tồn tại, hệ thống hiển thị thông báo lỗi "Không tìm thấy lớp học", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;4b. Nếu không có quyền, hệ thống hiển thị thông báo lỗi "Bạn không có quyền tạo buổi học", use-case kết thúc<br>5. Hệ thống kiểm tra các bài tập được chọn: phải tồn tại; với Giáo viên, bài phải thuộc lớp do chính mình tạo<br>&nbsp;&nbsp;&nbsp;5a. Nếu có bài không tồn tại, hệ thống hiển thị thông báo lỗi "Một hoặc nhiều bài tập không tồn tại", use-case tiếp tục ở bước 2<br>&nbsp;&nbsp;&nbsp;5b. Nếu có bài không được phép dùng, hệ thống hiển thị thông báo lỗi "Bạn không có quyền sao chép bài tập này", use-case tiếp tục ở bước 2<br>6. Hệ thống tạo buổi học, sao chép các bài tập (kèm testcase) vào buổi, cập nhật số bài tập<br>7. Hệ thống hiển thị lớp học với buổi học vừa tạo |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 4-6, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên dữ liệu đã nhập, use-case tiếp tục ở bước 2; buổi học và bài sao chép được lưu trong cùng một giao dịch nên không bị tạo dở dang |

### Use-case: Xem chi tiết buổi học

| | |
|---|---|
| **Description** | Giáo viên chủ lớp hoặc Admin xem nội dung một buổi học: danh sách bài tập kèm toàn bộ testcase, số bài nộp và thống kê tiến độ của Sinh viên |
| **Trigger** | Giáo viên/Admin chọn 1 buổi học trong lớp học |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Lớp học và buổi học tồn tại, buổi học thuộc lớp học đó |
| **Post-condition** | Không thay đổi dữ liệu |
| **Basic flow** | 1. Giáo viên/Admin chọn 1 buổi học<br>2. Hệ thống kiểm tra quyền xem lớp học (Admin mọi lớp, Giáo viên lớp mình tạo)<br>&nbsp;&nbsp;&nbsp;2a. Nếu không có quyền, hệ thống hiển thị thông báo lỗi "Bạn không có quyền xem lớp học này", use-case kết thúc<br>3. Hệ thống kiểm tra buổi học thuộc lớp học<br>&nbsp;&nbsp;&nbsp;3a. Nếu không, hệ thống hiển thị thông báo lỗi "Không tìm thấy buổi học", use-case kết thúc<br>4. Hệ thống tổng hợp: danh sách bài tập (đề, ràng buộc, gợi ý, code mẫu, testcase), số bài nộp mỗi bài, số Sinh viên đã nộp trên sĩ số, tỉ lệ nộp, điểm trung bình, hạn nộp<br>5. Hệ thống hiển thị trang chi tiết buổi học |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 2-4, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case tiếp tục ở bước 1 |

### Use-case: Cập nhật buổi học

| | |
|---|---|
| **Description** | Giáo viên chủ lớp hoặc Admin sửa tên, thời gian của buổi học, hoặc gắn thêm bài tập vào buổi |
| **Trigger** | Giáo viên/Admin chọn 1 buổi học, nhấn nút "Chỉnh sửa" |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Lớp học và buổi học tồn tại<br>Nếu người thực hiện là Giáo viên, Giáo viên đó phải là người tạo lớp học (`created_by`) |
| **Post-condition** | Các trường được gửi lên được cập nhật; bài tập được chọn được gắn thêm vào buổi (chỉ thêm, không gỡ; muốn gỡ bài dùng use-case "Xoá bài tập"); số bài tập của buổi được tính lại |
| **Basic flow** | 1. Hệ thống hiển thị form chỉnh sửa với thông tin hiện tại của buổi<br>2. Giáo viên/Admin sửa tên, ngày bắt đầu, ngày kết thúc, hoặc chọn thêm bài tập, rồi nhấn "Lưu"<br>3. Hệ thống kiểm tra lớp học tồn tại và quyền quản lý: Admin mọi lớp, Giáo viên chỉ lớp mình tạo<br>&nbsp;&nbsp;&nbsp;3a. Nếu lớp không tồn tại, hệ thống hiển thị thông báo lỗi "Không tìm thấy lớp học", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;3b. Nếu không có quyền, hệ thống hiển thị thông báo lỗi "Bạn không có quyền sửa buổi học", use-case kết thúc<br>4. Hệ thống kiểm tra buổi học thuộc lớp<br>&nbsp;&nbsp;&nbsp;4a. Nếu không, hệ thống hiển thị thông báo lỗi "Không tìm thấy buổi học", use-case kết thúc<br>5. Hệ thống đối chiếu với dữ liệu đang lưu, kiểm tra ngày bắt đầu trước hoặc bằng ngày kết thúc<br>&nbsp;&nbsp;&nbsp;5a. Nếu sai, hệ thống hiển thị thông báo lỗi "start_date phải trước hoặc bằng end_date", use-case tiếp tục ở bước 2<br>6. Nếu có chọn thêm bài tập, hệ thống kiểm tra và sao chép bài như bước 5-6 của use-case "Tạo buổi học"<br>7. Hệ thống lưu thay đổi và hiển thị lớp học sau khi cập nhật |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 3-7, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên dữ liệu đã nhập, use-case tiếp tục ở bước 2 |

### Use-case: Xoá buổi học

| | |
|---|---|
| **Description** | Giáo viên chủ lớp hoặc Admin xoá một buổi học tạo nhầm, chưa có bài tập |
| **Trigger** | Giáo viên/Admin chọn 1 buổi học, nhấn nút "Xoá buổi học" |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Lớp học và buổi học tồn tại<br>Nếu người thực hiện là Giáo viên, Giáo viên đó phải là người tạo lớp học (`created_by`) |
| **Post-condition** | Buổi học bị xoá khỏi database |
| **Basic flow** | 1. Giáo viên/Admin nhấn "Xoá buổi học"<br>2. Hệ thống hiển thị hộp thoại xác nhận<br>&nbsp;&nbsp;&nbsp;2a. Nếu Giáo viên/Admin huỷ, use-case kết thúc<br>3. Hệ thống kiểm tra lớp học tồn tại và quyền quản lý: Admin mọi lớp, Giáo viên chỉ lớp mình tạo<br>&nbsp;&nbsp;&nbsp;3a. Nếu lớp không tồn tại, hệ thống hiển thị thông báo lỗi "Không tìm thấy lớp học", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;3b. Nếu không có quyền, hệ thống hiển thị thông báo lỗi "Bạn không có quyền xoá buổi học", use-case kết thúc<br>4. Hệ thống kiểm tra buổi học còn bài tập không<br>&nbsp;&nbsp;&nbsp;4a. Nếu còn, hệ thống hiển thị thông báo lỗi "Không thể xoá buổi học đã có bài tập", use-case kết thúc<br>5. Hệ thống xoá buổi học và hiển thị thông báo xoá thành công |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 3-5, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case tiếp tục ở bước 1 |

## Module: Bài tập (Problem) và Testcase

### Use-case: Xem đề bài

| | |
|---|---|
| **Description** | Người dùng xem nội dung một bài tập: đề, ràng buộc, độ khó, gợi ý, giới hạn thời gian, code mẫu và testcase |
| **Trigger** | Người dùng chọn 1 bài tập trong buổi học |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Lớp học, buổi học và bài tập tồn tại, đúng quan hệ lớp → buổi → bài |
| **Post-condition** | Không thay đổi dữ liệu. Sinh viên chỉ thấy testcase mẫu (`is_sample = true`), testcase ẩn không bao giờ được trả về cho Sinh viên |
| **Basic flow** | 1. Người dùng chọn 1 bài tập<br>2. Hệ thống kiểm tra quyền xem lớp học (Admin mọi lớp, Giáo viên lớp mình tạo, Sinh viên lớp mình đã được thêm vào)<br>&nbsp;&nbsp;&nbsp;2a. Nếu không có quyền, hệ thống hiển thị thông báo lỗi "Bạn không có quyền xem lớp học này", use-case kết thúc<br>3. Hệ thống kiểm tra buổi học thuộc lớp và bài tập thuộc buổi<br>&nbsp;&nbsp;&nbsp;3a. Nếu không, hệ thống hiển thị thông báo lỗi "Không tìm thấy buổi học" hoặc "Không tìm thấy bài tập trong buổi học", use-case kết thúc<br>4. Nếu người xem là Sinh viên, hệ thống kiểm tra bài đã tới thời gian mở (`start_datetime`)<br>&nbsp;&nbsp;&nbsp;4a. Nếu chưa mở, hệ thống xử lý như không tìm thấy bài tập, use-case kết thúc<br>5. Hệ thống lấy testcase của bài; với Sinh viên chỉ giữ testcase mẫu<br>6. Hệ thống hiển thị đề bài và testcase |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 2-5, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case tiếp tục ở bước 1 |

### Use-case: Cập nhật bài tập

| | |
|---|---|
| **Description** | Giáo viên chủ lớp hoặc Admin sửa nội dung bài tập (đề, ràng buộc, độ khó, gợi ý, giới hạn thời gian, code mẫu, thời gian mở/đóng) và có thể thay toàn bộ testcase |
| **Trigger** | Giáo viên/Admin chọn 1 bài tập, nhấn nút "Chỉnh sửa" |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Lớp học, buổi học và bài tập tồn tại<br>Nếu người thực hiện là Giáo viên, Giáo viên đó phải là người tạo lớp học (`created_by`) |
| **Post-condition** | Các trường được gửi lên được cập nhật; nếu có gửi danh sách testcase thì toàn bộ testcase cũ được thay bằng danh sách mới và `total_number_testcase` được tính lại |
| **Basic flow** | 1. Hệ thống hiển thị form chỉnh sửa với nội dung hiện tại của bài<br>2. Giáo viên/Admin sửa các trường cần thay đổi và nhấn "Lưu"<br>3. Hệ thống kiểm tra định dạng (tiêu đề 1-255 ký tự, giới hạn thời gian ≥ 1 giây, thời gian có múi giờ)<br>&nbsp;&nbsp;&nbsp;3a. Nếu không hợp lệ, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 2<br>4. Hệ thống kiểm tra lớp học tồn tại và quyền quản lý: Admin mọi lớp, Giáo viên chỉ lớp mình tạo<br>&nbsp;&nbsp;&nbsp;4a. Nếu lớp không tồn tại, hệ thống hiển thị thông báo lỗi "Không tìm thấy lớp học", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;4b. Nếu không có quyền, hệ thống hiển thị thông báo lỗi "Bạn không có quyền sửa bài tập", use-case kết thúc<br>5. Hệ thống đối chiếu với dữ liệu đang lưu, kiểm tra thời gian mở trước hoặc bằng thời gian đóng<br>&nbsp;&nbsp;&nbsp;5a. Nếu sai, hệ thống hiển thị thông báo lỗi "start_datetime phải trước hoặc bằng end_datetime", use-case tiếp tục ở bước 2<br>6. Nếu có thay testcase, hệ thống kiểm tra bài đã có bài nộp chưa<br>&nbsp;&nbsp;&nbsp;6a. Nếu đã có, hệ thống hiển thị thông báo lỗi "Bài đã có bài nộp, không thể thay đổi testcase", use-case tiếp tục ở bước 2<br>7. Hệ thống lưu thay đổi và hiển thị bài tập sau khi cập nhật |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 4-7, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên dữ liệu đã nhập, use-case tiếp tục ở bước 2 |

### Use-case: Tải lên testcase

| | |
|---|---|
| **Description** | Giáo viên chủ lớp hoặc Admin tải lên file testcase (JSON, hoặc ZIP chứa JSON) để thay toàn bộ testcase của một bài tập |
| **Trigger** | Giáo viên/Admin chọn 1 bài tập, nhấn "Tải lên testcase" và chọn file |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Lớp học, buổi học và bài tập tồn tại<br>Nếu người thực hiện là Giáo viên, Giáo viên đó phải là người tạo lớp học (`created_by`)<br>File tối đa 5 MB; với ZIP, tổng dung lượng giải nén tối đa 20 MB |
| **Post-condition** | Toàn bộ testcase cũ của bài được thay bằng testcase trong file; `total_number_testcase` bằng số testcase mới. Trường không có trong file nhận mặc định: `is_sample = false`, `input_type = stdin`, `expected_output_type = stdout` |
| **Basic flow** | 1. Giáo viên/Admin chọn file và nhấn "Tải lên"<br>2. Hệ thống kiểm tra dung lượng file<br>&nbsp;&nbsp;&nbsp;2a. Nếu quá 5 MB, hệ thống hiển thị thông báo lỗi "File testcase quá lớn (tối đa 5MB)", use-case tiếp tục ở bước 1<br>3. Hệ thống đọc file: JSON đọc trực tiếp; ZIP thì tìm các file .json bên trong<br>&nbsp;&nbsp;&nbsp;3a. Nếu file không phải JSON hợp lệ hoặc ZIP không chứa JSON, hoặc nội dung giải nén quá 20 MB, hệ thống hiển thị thông báo lỗi tương ứng, use-case tiếp tục ở bước 1<br>4. Hệ thống kiểm tra danh sách testcase không rỗng và mỗi testcase có đủ `input`, `expected_output`<br>&nbsp;&nbsp;&nbsp;4a. Nếu sai, hệ thống hiển thị thông báo lỗi chỉ rõ testcase thứ mấy bị thiếu, use-case tiếp tục ở bước 1<br>5. Hệ thống kiểm tra lớp học tồn tại và quyền quản lý: Admin mọi lớp, Giáo viên chỉ lớp mình tạo<br>&nbsp;&nbsp;&nbsp;5a. Nếu lớp không tồn tại, hệ thống hiển thị thông báo lỗi "Không tìm thấy lớp học", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;5b. Nếu không có quyền, hệ thống hiển thị thông báo lỗi "Bạn không có quyền sửa testcase", use-case kết thúc<br>6. Hệ thống kiểm tra bài đã có bài nộp chưa<br>&nbsp;&nbsp;&nbsp;6a. Nếu đã có, hệ thống hiển thị thông báo lỗi "Bài đã có bài nộp, không thể thay đổi testcase", use-case kết thúc<br>7. Hệ thống xoá testcase cũ, lưu testcase mới và hiển thị bài tập với testcase đã cập nhật |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 5-7, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case tiếp tục ở bước 1; testcase cũ và mới được thay trong cùng một giao dịch nên bài không bị mất testcase giữa chừng |

### Use-case: Xoá bài tập

| | |
|---|---|
| **Description** | Giáo viên chủ lớp hoặc Admin gỡ một bài tập khỏi buổi học khi bài chưa có Sinh viên nộp |
| **Trigger** | Giáo viên/Admin chọn 1 bài tập, nhấn nút "Xoá bài tập" |
| **Pre-condition** | Đã đăng nhập thành công vào hệ thống<br>Lớp học, buổi học và bài tập tồn tại<br>Nếu người thực hiện là Giáo viên, Giáo viên đó phải là người tạo lớp học (`created_by`) |
| **Post-condition** | Bài tập và toàn bộ testcase của bài bị xoá; `total_number_assignment` của buổi được tính lại |
| **Basic flow** | 1. Giáo viên/Admin nhấn "Xoá bài tập"<br>2. Hệ thống hiển thị hộp thoại xác nhận<br>&nbsp;&nbsp;&nbsp;2a. Nếu Giáo viên/Admin huỷ, use-case kết thúc<br>3. Hệ thống kiểm tra lớp học tồn tại và quyền quản lý: Admin mọi lớp, Giáo viên chỉ lớp mình tạo<br>&nbsp;&nbsp;&nbsp;3a. Nếu lớp không tồn tại, hệ thống hiển thị thông báo lỗi "Không tìm thấy lớp học", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;3b. Nếu không có quyền, hệ thống hiển thị thông báo lỗi "Bạn không có quyền xoá bài tập", use-case kết thúc<br>4. Hệ thống kiểm tra bài đã có bài nộp chưa<br>&nbsp;&nbsp;&nbsp;4a. Nếu đã có, hệ thống hiển thị thông báo lỗi "Bài đã có bài nộp, không thể xoá", use-case kết thúc<br>5. Hệ thống xoá testcase và bài tập, cập nhật số bài tập của buổi, hiển thị thông báo xoá thành công |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bước 3-5, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, use-case tiếp tục ở bước 1 |
