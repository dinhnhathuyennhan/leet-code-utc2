/**
 * Dictionary song ngữ (vi / en).
 *
 * Cấu trúc: object lồng nhau, key là đường dẫn phẳng dạng "a.b.c".
 * Mỗi entry có `{ vi, en }` → dùng chung cho cả 2 ngôn ngữ, đảm bảo không
 * sót key (type `Dict` bắt buộc đủ key cho cả hai locale).
 */
export interface TranslationEntry {
  vi: string;
  en: string;
}

/** Kiểu dictionary: cấu trúc của `vi` và `en` phải giống nhau. */
export type Dict = Record<string, TranslationEntry>;

export const common = {
  // ── Điều hướng / layout ────────────────────────────────────────────
  "nav.overview": { vi: "Tổng quan", en: "Overview" },
  "nav.courses": { vi: "Lớp học phần", en: "Courses" },
  "nav.assignments": { vi: "Bài tập", en: "Assignments" },
  "nav.history": { vi: "Lịch sử nộp bài", en: "Submission History" },
  "nav.problemBank": { vi: "Ngân hàng đề", en: "Problem Bank" },
  "nav.accounts": { vi: "Quản lý tài khoản", en: "Account Management" },
  "nav.submissions": { vi: "Bài nộp", en: "Submissions" },
  "nav.settings": { vi: "Cấu hình", en: "Settings" },

  "layout.brandSubtitle": { vi: "Hệ Thống Đánh Giá Lập Trình", en: "Programming Evaluation System" },
  "layout.mainNav": { vi: "Điều hướng chính", en: "Main navigation" },
  "layout.navMenu": { vi: "Menu điều hướng", en: "Navigation menu" },
  "layout.navMenuDesc": { vi: "Chọn mục cần truy cập", en: "Choose a section to visit" },
  "layout.openMenu": { vi: "Mở menu", en: "Open menu" },
  "layout.home": { vi: "Trang chủ", en: "Home" },
  "layout.breadcrumb": { vi: "Breadcrumb", en: "Breadcrumb" },
  "layout.logout": { vi: "Đăng xuất", en: "Log out" },
  "layout.changePassword": { vi: "Đổi mật khẩu", en: "Change password" },
  "layout.accountMenu": { vi: "Menu tài khoản", en: "Account menu" },
  "layout.themeToggle": { vi: "Đổi giao diện sáng/tối", en: "Toggle light/dark theme" },
  "layout.language": { vi: "Ngôn ngữ", en: "Language" },
  "layout.backToTop": { vi: "Lên đầu trang", en: "Back to top" },
  "layout.student": { vi: "Sinh viên", en: "Student" },
  "layout.teacher": { vi: "Giảng viên", en: "Instructor" },

  // ── Hành động chung ────────────────────────────────────────────────
  "action.retry": { vi: "Thử lại", en: "Retry" },
  "action.search": { vi: "Tìm kiếm", en: "Search" },
  "action.cancel": { vi: "Huỷ", en: "Cancel" },
  "action.save": { vi: "Lưu", en: "Save" },
  "action.edit": { vi: "Sửa", en: "Edit" },
  "action.delete": { vi: "Xoá", en: "Delete" },
  "action.create": { vi: "Tạo", en: "Create" },
  "action.back": { vi: "Quay lại", en: "Back" },
  "action.copy": { vi: "Sao chép", en: "Copy" },
  "action.copied": { vi: "Đã copy", en: "Copied" },
  "action.view": { vi: "Xem", en: "View" },
  "action.close": { vi: "Đóng", en: "Close" },

  // ── Trạng thái / filter ────────────────────────────────────────────
  "filter.all": { vi: "Tất cả", en: "All" },
  "filter.allSemesters": { vi: "Tất cả học kỳ", en: "All semesters" },
  "filter.semester": { vi: "Học kỳ", en: "Semester" },
  "filter.viewMode": { vi: "Kiểu hiển thị", en: "View mode" },
  "filter.gridView": { vi: "Dạng lưới", en: "Grid view" },
  "filter.listView": { vi: "Dạng danh sách", en: "List view" },

  "status.ongoing": { vi: "Đang diễn ra", en: "In progress" },
  "status.upcoming": { vi: "Sắp diễn ra", en: "Upcoming" },
  "status.closed": { vi: "Đã kết thúc", en: "Closed" },
  "status.sessionUpcoming": { vi: "Sắp mở", en: "Not yet open" },
  "status.sessionOpen": { vi: "Đang mở", en: "Open" },
  "status.sessionClosed": { vi: "Đã đóng", en: "Closed" },
  "status.notStarted": { vi: "Chưa làm", en: "Not started" },
  "status.submitted": { vi: "Đã nộp", en: "Submitted" },
  "status.graded": { vi: "Đã chấm", en: "Graded" },
  "status.accepted": { vi: "Đạt", en: "Accepted" },
  "status.wrongAnswer": { vi: "Sai kết quả", en: "Wrong answer" },
  "status.compileError": { vi: "Lỗi biên dịch", en: "Compile error" },
  "status.runtimeError": { vi: "Lỗi khi chạy", en: "Runtime error" },
  "status.timeLimitExceeded": { vi: "Quá thời gian", en: "Time limit exceeded" },
  "status.internalError": { vi: "Lỗi hệ thống", en: "System error" },
  "status.error": { vi: "Lỗi", en: "Error" },
  "status.pending": { vi: "Đang chờ chấm", en: "Pending grading" },
  "status.processing": { vi: "Đang chấm", en: "Grading" },
  "status.unknown": { vi: "Không rõ", en: "Unknown" },

  // ── Lỗi / empty state ──────────────────────────────────────────────
  "state.loading": { vi: "Đang tải…", en: "Loading…" },
  "error.retry": { vi: "Thử lại", en: "Retry" },
  "error.network": { vi: "Mất kết nối từ server, vui lòng thử lại.", en: "Lost connection to the server, please try again." },
  "error.generic": { vi: "Đã có lỗi xảy ra, vui lòng thử lại.", en: "Something went wrong, please try again." },
  "error.invalidCredentials": { vi: "Email hoặc mật khẩu không chính xác", en: "Incorrect email or password" },
};

export const student = {
  // ── Dashboard ───────────────────────────────────────────────────────
  "student.dashboard.stats.enrolled": { vi: "Lớp đang ký", en: "Enrolled courses" },
  "student.dashboard.stats.completed": { vi: "Bài hoàn thành", en: "Completed problems" },
  "student.dashboard.stats.dueThisWeek": { vi: "Hạn tuần này", en: "Due this week" },
  "student.dashboard.searchPlaceholder": { vi: "Tìm kiếm lớp học phần…", en: "Search courses…" },
  "student.dashboard.searchLabel": { vi: "Tìm kiếm lớp học phần", en: "Search courses" },
  "student.dashboard.empty.title": { vi: "Chưa có lớp học phần nào", en: "No courses yet" },
  "student.dashboard.empty.desc": {
    vi: "Bạn chưa được ghi danh vào lớp nào trong kỳ này. Liên hệ giáo viên hoặc admin.",
    en: "You are not enrolled in any course this semester. Contact your instructor or admin.",
  },

  // ── Danh sách lớp ───────────────────────────────────────────────────
  "student.classes.heading": { vi: "Lớp đang học", en: "Enrolled courses" },
  "student.classes.stats.teaching": { vi: "Lớp phụ trách", en: "Courses teaching" },
  "student.classes.stats.learning": { vi: "Lớp đang học", en: "Courses learning" },
  "student.classes.stats.upcoming": { vi: "Lớp sắp mở", en: "Upcoming courses" },
  "student.classes.searchPlaceholder": { vi: "Tìm kiếm lớp học phần...", en: "Search courses..." },
  "student.classes.empty.title": { vi: "Chưa có lớp đang học", en: "No enrolled courses yet" },
  "student.classes.empty.noMatch": { vi: "Không tìm thấy lớp phù hợp", en: "No matching course found" },
  "student.classes.empty.desc": { vi: "Các lớp của bạn sẽ hiển thị tại đây.", en: "Your courses will appear here." },
  "student.classes.empty.noMatchDesc": { vi: "Thử đổi từ khoá khác.", en: "Try a different keyword." },

  // ── Chi tiết lớp ────────────────────────────────────────────────────
  "student.classDetail.tabs.info": { vi: "Thông tin lớp", en: "Class info" },
  "student.classDetail.tabs.roster": { vi: "Sinh viên cùng lớp", en: "Classmates" },
  "student.classDetail.sessionsTitle": { vi: "Danh sách buổi học & bài tập", en: "Sessions & assignments" },
  "student.classDetail.sessionNo": { vi: "Buổi", en: "Session" },
  "student.classDetail.opensAt": { vi: "Mở", en: "Opens" },
  "student.classDetail.deadline": { vi: "Hạn", en: "Due" },
  "student.classDetail.noProblems": { vi: "Buổi này chưa có bài tập hoặc chưa mở.", en: "No assignments in this session yet, or it hasn't opened." },
  "student.classDetail.noSessions": { vi: "Chưa có buổi học nào.", en: "No sessions yet." },
  "student.classDetail.col.code": { vi: "Mã bài", en: "Code" },
  "student.classDetail.col.title": { vi: "Tên bài", en: "Title" },
  "student.classDetail.col.status": { vi: "Trạng thái", en: "Status" },
  "student.classDetail.col.score": { vi: "Điểm", en: "Score" },
  "student.classDetail.doIt": { vi: "Làm bài", en: "Start" },
  "student.classDetail.viewIt": { vi: "Xem bài", en: "View" },
  "student.classDetail.endsAt": { vi: "Kết thúc", en: "Ends" },
  "student.classDetail.studentCount": { vi: "Sĩ số", en: "Enrolled" },
  "student.classDetail.students": { vi: "sinh viên", en: "students" },
  "student.classDetail.notFound": { vi: "Không tìm thấy lớp học phần", en: "Course not found" },
  "student.classDetail.notFoundDesc": { vi: "Lớp này không tồn tại hoặc bạn không có quyền xem.", en: "This course does not exist or you do not have permission to view it." },

  // ── Danh sách bài tập ───────────────────────────────────────────────
  "student.assignments.title": { vi: "Bài tập", en: "Assignments" },
  "student.assignments.desc": { vi: "Toàn bộ bài tập của các lớp bạn đang học.", en: "All assignments from the courses you are taking." },
  "student.assignments.searchPlaceholder": { vi: "Tìm theo tên bài hoặc mã bài…", en: "Search by title or code…" },
  "student.assignments.searchLabel": { vi: "Tìm bài tập", en: "Search assignments" },
  "student.assignments.empty.title": { vi: "Chưa có bài tập nào", en: "No assignments yet" },
  "student.assignments.empty.desc": {
    vi: "Khi giảng viên mở bài tập trong các lớp bạn đang học, chúng sẽ xuất hiện tại đây.",
    en: "When your instructors publish assignments, they will appear here.",
  },
  "student.assignments.noMatch.title": { vi: "Không tìm thấy bài tập", en: "No assignments found" },
  "student.assignments.noMatch.desc": { vi: "Thử đổi từ khoá tìm kiếm.", en: "Try a different search keyword." },
  "student.assignments.sessionPrefix": { vi: "Buổi", en: "Session" },
  "student.assignments.testCount": { vi: "test", en: "tests" },

  // ── Chi tiết bài tập ────────────────────────────────────────────────
  "student.assignment.backToClass": { vi: "Quay lại lớp", en: "Back to class" },
  "student.assignment.due": { vi: "Hạn", en: "Due" },
  "student.assignment.stat.runtime": { vi: "Thời gian chạy", en: "Time limit" },
  "student.assignment.stat.testcases": { vi: "Test cases", en: "Test cases" },
  "student.assignment.stat.level": { vi: "Mức độ", en: "Difficulty" },
  "student.assignment.stat.language": { vi: "Ngôn ngữ", en: "Language" },
  "student.assignment.section.statement": { vi: "Đề bài", en: "Problem statement" },
  "student.assignment.section.constraints": { vi: "Ràng buộc", en: "Constraints" },
  "student.assignment.section.hint": { vi: "Gợi ý", en: "Hint" },
  "student.assignment.section.samples": { vi: "Testcase mẫu", en: "Sample test cases" },
  "student.assignment.noSamples": { vi: "Bài chưa có testcase mẫu.", en: "This problem has no sample test cases." },
  "student.assignment.sampleInput": { vi: "Input", en: "Input" },
  "student.assignment.sampleOutput": { vi: "Output", en: "Output" },
  "student.assignment.actualOutput": { vi: "Thực tế", en: "Actual" },
  "student.assignment.submit": { vi: "Nộp bài", en: "Submit" },
  "student.assignment.submitting": { vi: "Đang chấm...", en: "Grading..." },
  "student.assignment.checkAnswer": { vi: "Kiểm tra đáp án", en: "Check answer" },
  "student.assignment.checking": { vi: "Đang kiểm tra...", en: "Checking..." },
  "student.assignment.checkTitle": { vi: "Kết quả kiểm tra", en: "Check result" },
  "student.assignment.checkDesc": {
    vi: "Chạy code với các testcase mẫu của bài. Thao tác này không tạo bài nộp và không ảnh hưởng điểm.",
    en: "Runs your code against the sample test cases. This does not create a submission and does not affect your grade.",
  },
  "student.assignment.checkPassed": { vi: "testcase mẫu đạt", en: "sample tests passed" },
  "student.assignment.checkNoSamples": {
    vi: "Bài tập này chưa có testcase mẫu để kiểm tra.",
    en: "This assignment has no sample test cases to check.",
  },
  "student.assignment.gradingWait": { vi: "Đang chấm bài, vui lòng chờ...", en: "Grading your submission, please wait..." },
  "student.assignment.resultTitle": { vi: "Kết quả bài nộp", en: "Submission result" },
  "student.assignment.emptySource": { vi: "Vui lòng nhập mã nguồn trước khi nộp bài.", en: "Please enter your source code before submitting." },
  "student.assignment.toastAccepted": { vi: "Chúc mừng! Bài nộp của bạn đã đạt.", en: "Congratulations! Your submission was accepted." },
  "student.assignment.toastSubmitted": { vi: "Đã nộp bài. Xem kết quả chấm bên dưới.", en: "Submitted. See the grading result below." },
  "student.assignment.notFound": { vi: "Không tìm thấy bài tập", en: "Assignment not found" },
  "student.assignment.notFoundDesc": { vi: "Bài tập này không tồn tại hoặc đã bị ẩn khỏi lớp học.", en: "This assignment does not exist or is hidden from the course." },
  "student.assignment.notFoundDesc2": { vi: "Bài tập này không tồn tại hoặc chưa mở trong buổi học hiện tại.", en: "This assignment does not exist or has not opened in the current session." },

  // ── Editor ──────────────────────────────────────────────────────────
  "editor.reset": { vi: "Khôi phục mẫu", en: "Reset template" },
  "editor.sourceLabel": { vi: "Mã nguồn bài nộp", en: "Submission source code" },
  "editor.fileName": { vi: "Main", en: "Main" },

  // ── Kết quả chấm ────────────────────────────────────────────────────
  "result.heading": { vi: "Kết quả chấm", en: "Grading result" },
  "result.score": { vi: "Điểm", en: "Score" },
  "result.passed": { vi: "Đạt", en: "Passed" },
  "result.submittedAt": { vi: "Nộp lúc", en: "Submitted at" },
  "result.language": { vi: "Ngôn ngữ", en: "Language" },
  "result.errorTitle": { vi: "Thông báo lỗi", en: "Error message" },
  "result.feedbackTitle": { vi: "Nhận xét của giảng viên", en: "Instructor feedback" },
  "result.testcaseDetails": { vi: "Chi tiết từng test case", en: "Test case details" },
  "result.sample": { vi: "mẫu", en: "sample" },
  "result.correct": { vi: "Đúng", en: "Correct" },
  "result.incorrect": { vi: "Sai", en: "Incorrect" },

  // ── Lịch sử nộp bài ─────────────────────────────────────────────────
  "history.title": { vi: "Lịch sử nộp bài", en: "Submission history" },
  "history.desc": { vi: "Xem lại toàn bộ bài tập đã nộp và kết quả chấm của bạn.", en: "Review all your submitted assignments and grading results." },
  "history.searchPlaceholder": { vi: "Tìm theo tên bài hoặc mã bài…", en: "Search by title or code…" },
  "history.searchLabel": { vi: "Tìm bài nộp", en: "Search submissions" },
  "history.filter.accepted": { vi: "Đạt", en: "Accepted" },
  "history.filter.wrongAnswer": { vi: "Sai kết quả", en: "Wrong answer" },
  "history.filter.compileError": { vi: "Lỗi biên dịch", en: "Compile error" },
  "history.filter.pending": { vi: "Đang chờ", en: "Pending" },
  "history.empty.title": { vi: "Chưa có bài nộp nào", en: "No submissions yet" },
  "history.empty.desc": { vi: "Khi bạn nộp bài trong một lớp học phần, kết quả chấm sẽ xuất hiện ở đây.", en: "Once you submit an assignment, grading results will show up here." },
  "history.noMatch.title": { vi: "Không có bài nộp phù hợp", en: "No matching submissions" },
  "history.noMatch.desc": { vi: "Thử đổi bộ lọc hoặc từ khoá tìm kiếm.", en: "Try changing the filter or search keyword." },
  "history.loading": { vi: "Đang tải lịch sử nộp bài", en: "Loading submission history" },
  "history.testSuffix": { vi: "test", en: "tests" },
  "history.problemFallback": { vi: "Bài", en: "Problem" },

  // ── Chi tiết bài nộp ───────────────────────────────────────────────
  "submission.backToHistory": { vi: "Quay lại lịch sử nộp bài", en: "Back to submission history" },
  "submission.resultFallback": { vi: "Kết quả bài nộp", en: "Submission result" },
  "submission.resultNumbered": { vi: "Kết quả #", en: "Result #" },
  "submission.sourceTitle": { vi: "Mã nguồn đã nộp", en: "Submitted source code" },

  // ── AI review code (chỉ cho bài đã pass hết testcase) ───────────────
  "aiReview.button": { vi: "Review code", en: "Review code" },
  "aiReview.prompt": { vi: "Bài đã pass toàn bộ testcase. Xem AI nhận xét về hiệu năng code?", en: "All testcases passed. Get AI feedback on performance?" },
  "aiReview.running": { vi: "Đang review…", en: "Reviewing…" },
  "aiReview.runningDesc": { vi: "AI đang phân tích độ phức tạp và hướng tối ưu.", en: "The AI is analyzing complexity and optimizations." },
  "aiReview.warmup": { vi: "Lần đầu có thể mất 1–2 phút do AI đang khởi động.", en: "The first run may take 1–2 minutes while the AI warms up." },
  "aiReview.title": { vi: "AI Review", en: "AI Review" },
  "aiReview.close": { vi: "Đóng AI review", en: "Close AI review" },
  "aiReview.summary": { vi: "Tóm tắt", en: "Summary" },
  "aiReview.time": { vi: "Thời gian", en: "Time" },
  "aiReview.space": { vi: "Bộ nhớ", en: "Space" },
  "aiReview.explanation": { vi: "Giải thích", en: "Explanation" },
  "aiReview.issues": { vi: "Điểm chưa tối ưu", en: "Inefficiencies" },
  "aiReview.noIssues": { vi: "Không phát hiện điểm chưa tối ưu.", en: "No inefficiencies found." },
  "aiReview.optimization": { vi: "Hướng cải thiện", en: "How to improve" },
  "aiReview.alreadyOptimal": { vi: "Code đã ở mức tối ưu hợp lý", en: "Code is already reasonably optimal" },
  "aiReview.disclaimer": { vi: "Nhận xét do AI tạo, có thể chưa chính xác. Không ảnh hưởng tới điểm.", en: "AI-generated, may be inaccurate. Does not affect your grade." },
  "aiReview.retry": { vi: "Thử lại", en: "Retry" },
  "aiReview.reviewAgain": { vi: "Review lại", en: "Review again" },
  "aiReview.errorTitle": { vi: "Không review được", en: "Review failed" },
  "aiReview.error.AI_BUSY": { vi: "AI đang phân tích bài khác, vui lòng thử lại sau.", en: "The AI is busy with another review, please try again later." },
  "aiReview.error.AI_UNAVAILABLE": { vi: "Không thể kết nối AI Server.", en: "Cannot connect to the AI server." },
  "aiReview.error.AI_TIMEOUT": { vi: "AI xử lý quá thời gian cho phép.", en: "The AI took too long to respond." },
  "aiReview.error.AI_INVALID_RESPONSE": { vi: "AI trả về dữ liệu không hợp lệ.", en: "The AI returned an invalid response." },
  "aiReview.error.SUBMISSION_NOT_ACCEPTED": { vi: "Bài nộp phải pass toàn bộ testcase mới được review code.", en: "Only submissions that pass all testcases can be reviewed." },
  "aiReview.error.CODE_TOO_LONG": { vi: "Mã nguồn quá dài, AI không review được.", en: "The source code is too long to review." },
  "aiReview.error.NOT_FOUND": { vi: "Không tìm thấy bài nộp.", en: "Submission not found." },
  "aiReview.error.NETWORK": { vi: "Mất kết nối, vui lòng thử lại.", en: "Connection lost, please try again." },
  "aiReview.error.UNKNOWN": { vi: "Đã có lỗi xảy ra, vui lòng thử lại.", en: "Something went wrong, please try again." },

  // ── Roster ──────────────────────────────────────────────────────────
  "student.roster.empty": { vi: "Chưa có sinh viên nào", en: "No students yet" },
  "student.roster.emptyDesc": { vi: "Danh sách sẽ hiển thị khi có sinh viên được thêm vào lớp.", en: "The roster will appear once students are added to the course." },
  "student.roster.col.id": { vi: "Mã sinh viên", en: "Student ID" },
  "student.roster.col.name": { vi: "Họ và tên", en: "Full name" },
  "student.roster.col.email": { vi: "Email", en: "Email" },
  "student.roster.loading": { vi: "Đang tải danh sách sinh viên", en: "Loading student roster" },
};

export const auth = {
  "auth.login.title": { vi: "Đăng nhập", en: "Sign in" },
  "auth.login.subtitle": { vi: "Sử dụng tài khoản nội bộ UTC2 để truy cập hệ thống lập trình", en: "Use your UTC2 account to access the programming system" },
  "auth.login.email": { vi: "Email UTC2", en: "UTC2 Email" },
  "auth.login.password": { vi: "Mật khẩu", en: "Password" },
  "auth.login.remember": { vi: "Ghi nhớ phiên đăng nhập", en: "Remember me" },
  "auth.login.submit": { vi: "Đăng nhập", en: "Sign in" },
  "auth.login.welcome": { vi: "Chào mừng {name} quay lại!", en: "Welcome back, {name}!" },
  "auth.login.welcomeFallback": { vi: "bạn", en: "there" },
  "auth.logout": { vi: "Đăng xuất", en: "Log out" },
};

export const teacher = {
  "teacher.courses.heading": { vi: "Lớp phụ trách", en: "Courses teaching" },
  "teacher.sessions.empty": { vi: "Chưa có buổi học nào", en: "No sessions yet" },
  "teacher.sessions.emptyDesc": { vi: "Nhấn Tạo buổi học để bắt đầu.", en: "Press Create session to get started." },
  "teacher.sessions.create": { vi: "Tạo buổi học", en: "Create session" },
  "teacher.sessions.editSession": { vi: "Sửa buổi học", en: "Edit session" },
  "teacher.sessions.editCourse": { vi: "Chỉnh sửa lớp", en: "Edit course" },
  "teacher.sessions.sessionActions": { vi: "Thao tác buổi học", en: "Session actions" },
  "teacher.sessions.openEarly": { vi: "Mở sớm", en: "Open early" },
  "teacher.sessions.problemCount": { vi: "bài tập", en: "assignments" },
  "teacher.tabs.sessions": { vi: "Buổi học", en: "Sessions" },
  "teacher.tabs.students": { vi: "Sinh viên", en: "Students" },
  "teacher.tabs.grades": { vi: "Bảng điểm", en: "Grades" },
  "teacher.course.endsAt": { vi: "Ngày kết thúc", en: "End date" },
  "teacher.course.updatedAt": { vi: "Cập nhật lúc", en: "Updated at" },
};

/** Toàn bộ dictionary của app. */
export const DICTIONARY = {
  ...common,
  ...student,
  ...auth,
  ...teacher,
};

/** Key hợp lệ của dictionary. */
export type TranslationKey = keyof typeof DICTIONARY;

/** Bản dịch của một key bất kỳ (dùng cho test/đối chiếu). */
export type DictShape = Dict;
