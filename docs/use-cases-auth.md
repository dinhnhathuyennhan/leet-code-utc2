# Đặc tả Use-case

## Module: Quản lý tài khoản

### Use-case: Cấp phát tài khoản Giáo viên

| | |
|---|---|
| **Description** | Admin cấp một tài khoản mới cho Giáo viên, kèm mật khẩu tạm bắt buộc phải đổi trong lần đăng nhập đầu tiên |
| **Trigger** | Admin nhấn nút "Cấp phát tài khoản Giáo viên" |
| **Pre-condition** | Admin đã đăng nhập thành công vào hệ thống<br>Thiết bị của Admin phải kết nối Internet<br>Email của tài khoản mới chưa tồn tại trong hệ thống |
| **Post-condition** | Tài khoản Giáo viên mới được tạo trong database với `role_id = 2`, mật khẩu tạm (theo ngày sinh, đã băm), `must_change_password = true` |
| **Basic flow** | 1. Hệ thống hiển thị trang quản lý tài khoản<br>2. Admin chọn chức năng "Cấp phát tài khoản Giáo viên"<br>3. Hệ thống hiển thị form nhập thông tin tài khoản<br>4. Admin nhập user_id, họ tên, ngày sinh và email của Giáo viên<br>5. Hệ thống kiểm tra định dạng dữ liệu (email hợp lệ, họ tên không rỗng, ngày sinh hợp lệ)<br>&nbsp;&nbsp;&nbsp;5a. Nếu định dạng không hợp lệ, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;5b. Nếu định dạng hợp lệ, use-case tiếp tục ở bước 6<br>6. Hệ thống kiểm tra người được cấp tài khoản đã đủ 17 tuổi (tính từ ngày sinh) chưa<br>&nbsp;&nbsp;&nbsp;6a. Nếu chưa đủ tuổi, hệ thống hiển thị thông báo lỗi "Người dùng phải đủ 17 tuổi", use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;6b. Nếu đủ tuổi, use-case tiếp tục ở bước 7<br>7. Hệ thống kiểm tra email đã tồn tại trong database chưa<br>&nbsp;&nbsp;&nbsp;7a. Nếu email đã tồn tại, hệ thống hiển thị thông báo lỗi "Email đã tồn tại", use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;7b. Nếu email chưa tồn tại, use-case tiếp tục ở bước 8<br>8. Hệ thống sinh mật khẩu tạm theo ngày sinh (định dạng `ddmmyyyy`), băm mật khẩu, tạo tài khoản với `role_id = 2` và `must_change_password = true`<br>9. Hệ thống hiển thị thông báo tạo thành công kèm mật khẩu tạm để Admin gửi lại cho Giáo viên |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 4-9, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên dữ liệu đã nhập, use-case tiếp tục ở bước 3 |

### Use-case: Cấp phát tài khoản Sinh viên hàng loạt bằng file Excel

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên tải lên một file Excel chứa danh sách nhiều Sinh viên để hệ thống tự động tạo tài khoản hàng loạt, thay vì phải nhập tay từng người |
| **Trigger** | Admin/Giáo viên nhấn nút "Nhập danh sách từ Excel" và chọn file |
| **Pre-condition** | Admin/Giáo viên đã đăng nhập thành công vào hệ thống<br>Thiết bị của Admin/Giáo viên phải kết nối Internet<br>File Excel tồn tại, đúng định dạng mẫu quy định (các cột: họ tên, ngày sinh, email) |
| **Post-condition** | Mọi dòng hợp lệ trong file được tạo thành tài khoản Sinh viên mới với `role_id = 3`, mật khẩu tạm (theo ngày sinh, đã băm), `must_change_password = true`; các dòng lỗi không được tạo tài khoản và được liệt kê lại kèm lý do |
| **Basic flow** | 1. Hệ thống hiển thị trang quản lý tài khoản<br>2. Admin/Giáo viên chọn chức năng "Nhập danh sách từ Excel"<br>3. Hệ thống hiển thị hướng dẫn định dạng file mẫu và ô chọn file<br>4. Admin/Giáo viên chọn file Excel từ máy và nhấn "Tải lên"<br>5. Hệ thống kiểm tra định dạng file (đúng phần mở rộng .xlsx, đúng cấu trúc cột)<br>&nbsp;&nbsp;&nbsp;5a. Nếu file sai định dạng, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;5b. Nếu file đúng định dạng, use-case tiếp tục ở bước 6<br>6. Hệ thống đọc từng dòng dữ liệu trong file, kiểm tra hợp lệ (họ tên không rỗng, ngày sinh hợp lệ, email đúng định dạng, chưa tồn tại trong database, chưa trùng lặp trong chính file) cho từng dòng<br>7. Với mỗi dòng hợp lệ, hệ thống sinh mật khẩu tạm theo ngày sinh của dòng đó (định dạng `ddmmyyyy`), băm mật khẩu, tạo tài khoản Sinh viên với `role_id = 3` và `must_change_password = true`<br>8. Hệ thống hiển thị kết quả tổng hợp: số tài khoản tạo thành công (kèm danh sách mật khẩu tạm để gửi lại cho từng Sinh viên) và danh sách các dòng lỗi kèm lý do cụ thể |
| **Exception flow** | **E1. Toàn bộ file đều lỗi**: ở bước 6-7, không có dòng nào hợp lệ để tạo tài khoản → hệ thống hiển thị thông báo "Không có tài khoản nào được tạo" kèm đầy đủ danh sách lỗi, use-case quay lại bước 4<br>**E2. File rỗng hoặc vượt quá số dòng cho phép**: ở bước 5, file không có dữ liệu hoặc vượt giới hạn số dòng xử lý → hệ thống hiển thị thông báo lỗi tương ứng, use-case quay lại bước 4<br>**E3. Mất kết nối/lỗi hệ thống khi đang xử lý**: ở bước 6-7, nếu quá trình xử lý bị gián đoạn giữa chừng → hệ thống chỉ giữ lại các tài khoản đã tạo thành công trước thời điểm lỗi, hiển thị thông báo lỗi và danh sách các dòng chưa kịp xử lý để Admin/Giáo viên thử lại |

### Use-case: Cấp phát tài khoản Sinh viên

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên cấp một tài khoản mới cho Sinh viên, kèm mật khẩu tạm bắt buộc phải đổi trong lần đăng nhập đầu tiên |
| **Trigger** | Admin/Giáo viên nhấn nút "Cấp phát tài khoản Sinh viên" |
| **Pre-condition** | Admin/Giáo viên đã đăng nhập thành công vào hệ thống<br>Thiết bị của Admin/Giáo viên phải kết nối Internet<br>Email của tài khoản mới chưa tồn tại trong hệ thống |
| **Post-condition** | Tài khoản Sinh viên mới được tạo trong database với `role_id = 3`, mật khẩu tạm (theo ngày sinh, đã băm), `must_change_password = true` |
| **Basic flow** | 1. Hệ thống hiển thị trang quản lý tài khoản<br>2. Admin/Giáo viên chọn chức năng "Cấp phát tài khoản Sinh viên"<br>3. Hệ thống hiển thị form nhập thông tin tài khoản<br>4. Admin/Giáo viên nhập user_id, họ tên, ngày sinh và email của Sinh viên<br>5. Hệ thống kiểm tra định dạng dữ liệu (email hợp lệ, họ tên không rỗng, ngày sinh hợp lệ)<br>&nbsp;&nbsp;&nbsp;5a. Nếu định dạng không hợp lệ, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;5b. Nếu định dạng hợp lệ, use-case tiếp tục ở bước 6<br>6. Hệ thống kiểm tra người được cấp tài khoản đã đủ 17 tuổi (tính từ ngày sinh) chưa<br>&nbsp;&nbsp;&nbsp;6a. Nếu chưa đủ tuổi, hệ thống hiển thị thông báo lỗi "Người dùng phải đủ 17 tuổi", use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;6b. Nếu đủ tuổi, use-case tiếp tục ở bước 7<br>7. Hệ thống kiểm tra email đã tồn tại trong database chưa<br>&nbsp;&nbsp;&nbsp;7a. Nếu email đã tồn tại, hệ thống hiển thị thông báo lỗi "Email đã tồn tại", use-case tiếp tục ở bước 4<br>&nbsp;&nbsp;&nbsp;7b. Nếu email chưa tồn tại, use-case tiếp tục ở bước 8<br>8. Hệ thống sinh mật khẩu tạm theo ngày sinh (định dạng `ddmmyyyy`), băm mật khẩu, tạo tài khoản với `role_id = 3` và `must_change_password = true`<br>9. Hệ thống hiển thị thông báo tạo thành công kèm mật khẩu tạm để Admin/Giáo viên gửi lại cho Sinh viên |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 4-9, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên dữ liệu đã nhập, use-case tiếp tục ở bước 3 |

### Use-case: Đặt lại mật khẩu

| | |
|---|---|
| **Description** | Admin hoặc Giáo viên đặt lại mật khẩu cho một tài khoản khác khi chủ tài khoản quên mật khẩu và không thể tự khôi phục; hệ thống cấp một mật khẩu tạm mới và bắt buộc đổi mật khẩu ở lần đăng nhập tiếp theo |
| **Trigger** | Admin/Giáo viên chọn một tài khoản trong danh sách và nhấn nút "Đặt lại mật khẩu" |
| **Pre-condition** | Admin/Giáo viên đã đăng nhập thành công vào hệ thống<br>Thiết bị của Admin/Giáo viên phải kết nối Internet<br>Tài khoản mục tiêu tồn tại trong hệ thống<br>Nếu người thực hiện là Giáo viên, tài khoản mục tiêu phải là Sinh viên (Giáo viên không được đặt lại mật khẩu của Giáo viên khác hoặc Admin) |
| **Post-condition** | Mật khẩu tạm mới (theo ngày sinh hiện có của tài khoản mục tiêu) được băm và lưu vào tài khoản mục tiêu; `must_change_password` được đặt về `true`; `token_version` của tài khoản mục tiêu tăng lên 1, khiến toàn bộ access/refresh token đã phát hành trước đó (trên mọi thiết bị) bị vô hiệu hoá ngay lập tức |
| **Basic flow** | 1. Hệ thống hiển thị danh sách tài khoản<br>2. Admin/Giáo viên tìm và chọn tài khoản cần đặt lại mật khẩu<br>3. Hệ thống hiển thị thông tin tài khoản kèm nút "Đặt lại mật khẩu"<br>4. Admin/Giáo viên nhấn nút "Đặt lại mật khẩu"<br>5. Hệ thống hiển thị hộp thoại xác nhận hành động<br>6. Admin/Giáo viên xác nhận<br>7. Hệ thống kiểm tra quyền thực hiện trên tài khoản mục tiêu<br>&nbsp;&nbsp;&nbsp;7a. Nếu người thực hiện là Giáo viên và tài khoản mục tiêu không phải Sinh viên, hệ thống hiển thị thông báo lỗi "Bạn không có quyền đặt lại mật khẩu cho tài khoản này", use-case kết thúc<br>&nbsp;&nbsp;&nbsp;7b. Nếu hợp lệ, use-case tiếp tục ở bước 8<br>8. Hệ thống sinh lại mật khẩu tạm theo ngày sinh (`date_of_birth`) hiện có của tài khoản mục tiêu (định dạng `ddmmyyyy`), băm mật khẩu, cập nhật `hashed_password`, đặt `must_change_password = true`, tăng `token_version` của tài khoản mục tiêu<br>9. Hệ thống hiển thị thông báo thành công kèm mật khẩu tạm mới để Admin/Giáo viên gửi lại cho chủ tài khoản |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 4-9, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, không thay đổi mật khẩu, use-case tiếp tục ở bước 3 |

## Module: Auth (Xác thực)

### Use-case: Đăng nhập

| | |
|---|---|
| **Description** | Người dùng (Admin/Teacher/Student) đăng nhập vào hệ thống bằng email và mật khẩu để nhận quyền truy cập tương ứng với vai trò của mình |
| **Trigger** | Người dùng nhập email, mật khẩu và nhấn nút "Đăng nhập" |
| **Pre-condition** | Người dùng đã có tài khoản trong hệ thống (được Admin/Teacher tạo sẵn)<br>Thiết bị của người dùng phải kết nối Internet<br>Người dùng chưa đăng nhập (chưa có phiên hợp lệ) |
| **Post-condition** | Người dùng được xác thực thành công, hệ thống cấp access token + refresh token tương ứng với tài khoản |
| **Basic flow** | 1. Hệ thống hiển thị trang đăng nhập<br>2. Người dùng nhập email và mật khẩu<br>3. Người dùng nhấn nút "Đăng nhập"<br>4. Hệ thống kiểm tra định dạng dữ liệu đầu vào<br>&nbsp;&nbsp;&nbsp;4a. Nếu định dạng không hợp lệ, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 2<br>&nbsp;&nbsp;&nbsp;4b. Nếu định dạng hợp lệ, use-case tiếp tục ở bước 5<br>5. Hệ thống tìm tài khoản theo email và so khớp mật khẩu đã băm (hashed)<br>&nbsp;&nbsp;&nbsp;5a. Nếu không tìm thấy tài khoản khớp hoặc mật khẩu không đúng, hệ thống hiển thị thông báo lỗi chung "Email hoặc mật khẩu không đúng" (không tiết lộ cụ thể sai cái nào), use-case tiếp tục ở bước 2<br>&nbsp;&nbsp;&nbsp;5b. Nếu khớp, use-case tiếp tục ở bước 6<br>6. Hệ thống sinh access token và refresh token, gắn access token vào response body và refresh token vào cookie HttpOnly<br>7. Hệ thống trả về thông tin người dùng (họ tên, vai trò, cờ must_change_password)<br>8. Nếu `must_change_password = true`, hệ thống chuyển hướng người dùng sang trang bắt buộc đổi mật khẩu; ngược lại chuyển vào trang chính theo vai trò |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 3-7, nếu request thất bại (mất mạng, server lỗi) → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên dữ liệu người dùng đã nhập, use-case tiếp tục ở bước 3 |

### Use-case: Đổi mật khẩu

| | |
|---|---|
| **Description** | Người dùng đã đăng nhập thay đổi mật khẩu của chính mình — bao gồm cả trường hợp bắt buộc đổi mật khẩu tạm ngay sau lần đăng nhập đầu tiên, lẫn trường hợp chủ động đổi mật khẩu sau này |
| **Trigger** | Người dùng nhập mật khẩu hiện tại, mật khẩu mới, xác nhận mật khẩu mới và nhấn nút "Đổi mật khẩu" (hoặc bị hệ thống tự động điều hướng tới trang này nếu `must_change_password = true`) |
| **Pre-condition** | Người dùng đã đăng nhập thành công, có access token hợp lệ<br>Thiết bị của người dùng phải kết nối Internet |
| **Post-condition** | Mật khẩu mới được băm (hashed) và lưu vào tài khoản; `must_change_password` được đặt về `false`; `token_version` của tài khoản tăng lên 1, khiến toàn bộ access/refresh token đã phát hành trước đó (trên mọi thiết bị) bị vô hiệu hoá; hệ thống cấp lại access token mới + cookie refresh mới cho phiên hiện tại |
| **Basic flow** | 1. Hệ thống hiển thị trang đổi mật khẩu (chủ động hoặc do bị bắt buộc)<br>2. Người dùng nhập mật khẩu hiện tại, mật khẩu mới và xác nhận mật khẩu mới<br>3. Người dùng nhấn nút "Đổi mật khẩu"<br>4. Hệ thống kiểm tra định dạng dữ liệu (mật khẩu mới đủ độ mạnh, khớp với xác nhận)<br>&nbsp;&nbsp;&nbsp;4a. Nếu định dạng không hợp lệ, hệ thống hiển thị thông báo lỗi, use-case tiếp tục ở bước 2<br>&nbsp;&nbsp;&nbsp;4b. Nếu định dạng hợp lệ, use-case tiếp tục ở bước 5<br>5. Hệ thống xác thực mật khẩu hiện tại có khớp với mật khẩu đã lưu không<br>&nbsp;&nbsp;&nbsp;5a. Nếu không khớp, hệ thống hiển thị thông báo lỗi "Mật khẩu hiện tại không đúng", use-case tiếp tục ở bước 2<br>&nbsp;&nbsp;&nbsp;5b. Nếu khớp, use-case tiếp tục ở bước 6<br>6. Hệ thống kiểm tra mật khẩu mới có trùng với mật khẩu hiện tại không<br>&nbsp;&nbsp;&nbsp;6a. Nếu trùng, hệ thống hiển thị thông báo lỗi "Mật khẩu mới phải khác mật khẩu hiện tại", use-case tiếp tục ở bước 2<br>&nbsp;&nbsp;&nbsp;6b. Nếu khác, use-case tiếp tục ở bước 7<br>7. Hệ thống băm mật khẩu mới, cập nhật `hashed_password`, đặt `must_change_password = false`, tăng `token_version`<br>8. Hệ thống sinh access token và refresh token mới (theo `token_version` mới), trả access token trong response và refresh token vào cookie HttpOnly<br>9. Hệ thống hiển thị thông báo đổi mật khẩu thành công và chuyển người dùng vào trang chính theo vai trò |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: ở bất kỳ bước nào từ 3-8, nếu request thất bại → hệ thống hiển thị thông báo lỗi kết nối, giữ nguyên dữ liệu đã nhập (trừ mật khẩu), use-case tiếp tục ở bước 3 |

### Use-case: Đăng xuất

| | |
|---|---|
| **Description** | Người dùng đã đăng nhập chủ động kết thúc phiên làm việc hiện tại trên thiết bị đang dùng |
| **Trigger** | Người dùng nhấn nút "Đăng xuất" |
| **Pre-condition** | Người dùng đã đăng nhập thành công, có access token và cookie refresh token hợp lệ trên thiết bị hiện tại |
| **Post-condition** | Cookie refresh token trên thiết bị hiện tại bị xoá; access token phía client bị huỷ (không còn được gửi kèm request); các phiên đăng nhập trên thiết bị khác của cùng tài khoản không bị ảnh hưởng |
| **Basic flow** | 1. Người dùng nhấn nút "Đăng xuất"<br>2. Hệ thống xoá access token đang lưu ở phía client<br>3. Hệ thống gửi yêu cầu đăng xuất lên server<br>4. Server xoá cookie refresh token (đặt cookie hết hạn ngay lập tức)<br>5. Hệ thống chuyển người dùng về trang đăng nhập |
| **Exception flow** | **E1. Mất kết nối khi gửi yêu cầu đăng xuất**: ở bước 3, request thất bại do mất mạng → hệ thống vẫn xoá access token phía client và chuyển về trang đăng nhập (coi như đăng xuất cục bộ thành công); cookie refresh token trên server có thể vẫn còn hiệu lực đến khi hết hạn tự nhiên |

### Use-case: Làm mới phiên đăng nhập (Refresh token)

| | |
|---|---|
| **Description** | Hệ thống tự động cấp access token mới cho người dùng khi access token hiện tại sắp/đã hết hạn, dựa trên refresh token còn hiệu lực, để người dùng không phải đăng nhập lại giữa phiên làm việc |
| **Trigger** | Client phát hiện access token sắp hết hạn hoặc nhận lỗi 401 từ một API bất kỳ, tự động gọi API làm mới phiên (không do người dùng chủ động thao tác) |
| **Pre-condition** | Người dùng đã đăng nhập trước đó và cookie refresh token trên trình duyệt vẫn còn hiệu lực (chưa hết hạn, chưa bị xoá do đăng xuất)<br>Thiết bị của người dùng phải kết nối Internet |
| **Post-condition** | Access token mới được cấp và trả về client; cookie refresh token giữ nguyên (không bị thay đổi/rotate); phiên làm việc của người dùng được tiếp tục mà không bị gián đoạn |
| **Basic flow** | 1. Client gửi yêu cầu làm mới phiên kèm cookie refresh token<br>2. Hệ thống xác thực chữ ký và hạn sử dụng của refresh token<br>&nbsp;&nbsp;&nbsp;2a. Nếu cookie refresh token không có, sai chữ ký hoặc đã hết hạn, hệ thống trả lỗi 401 và chuyển người dùng về trang đăng nhập, use-case kết thúc<br>&nbsp;&nbsp;&nbsp;2b. Nếu hợp lệ, use-case tiếp tục ở bước 3<br>3. Hệ thống kiểm tra `token_version` trong refresh token có khớp với `token_version` hiện tại của tài khoản trong database không<br>&nbsp;&nbsp;&nbsp;3a. Nếu không khớp (đã bị thu hồi do đổi mật khẩu ở nơi khác), hệ thống trả lỗi 401, xoá cookie hiện tại và chuyển người dùng về trang đăng nhập, use-case kết thúc<br>&nbsp;&nbsp;&nbsp;3b. Nếu khớp, use-case tiếp tục ở bước 4<br>4. Hệ thống sinh access token mới (giữ nguyên `token_version`) và trả về client<br>5. Client lưu access token mới và tiếp tục gọi lại API trước đó (nếu có) |
| **Exception flow** | **E1. Mất kết nối/lỗi hệ thống**: request ở bước 1 thất bại → client giữ nguyên access token cũ, thử lại sau; nếu access token cũ đã hết hạn, người dùng tạm thời không thao tác được cho tới khi làm mới phiên thành công |
