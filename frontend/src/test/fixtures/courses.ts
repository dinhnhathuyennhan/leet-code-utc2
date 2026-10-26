import type { CourseSummary } from "@/lib/types/course";

/** Mock data theo shape BACKEND trả về (CourseResponseRaw). */
const rawCourses = [
  {
    course_id: "CS101",
    course_name: "Nhập môn lập trình",
    term: "2024-2025 - HK1",
    start_date: "2024-09-01",
    end_date: "2025-01-15",
    avt_link: null,
    created_by: "Nguyễn Văn A",
    total_number_student: 60,
  },
  {
    course_id: "CS201",
    course_name: "Cấu trúc dữ liệu và giải thuật",
    term: "2024-2025 - HK1",
    start_date: "2024-09-01",
    end_date: "2025-01-15",
    avt_link: null,
    created_by: "Trần Thị B",
    total_number_student: 45,
  },
  {
    course_id: "PY101",
    course_name: "Lập trình Python cơ bản",
    term: "2024-2025 - HK2",
    start_date: "2025-01-15",
    end_date: "2025-05-30",
    avt_link: null,
    created_by: "Lê Văn C",
    total_number_student: 30,
  },
  {
    course_id: "JS101",
    course_name: "JavaScript nâng cao",
    term: "2024-2025 - HK2",
    start_date: "2025-01-15",
    end_date: "2025-05-30",
    avt_link: null,
    created_by: "Phạm Thị D",
    total_number_student: 25,
  },
];

/** Mock trả về shape CourseSummary (FE UI) — dùng cho component test. */
export const mockCourses: CourseSummary[] = rawCourses.map((r) => ({
  id: r.course_id,
  code: r.course_id,
  name: r.course_name,
  start_date: r.start_date,
  language: "java" as const,
  status: "ongoing" as const,
  teacher_name: r.created_by,
  semester: 1,
  academic_year: "2024-2025",
  group: 1,
}));

/** Mock theo shape API raw (CourseResponseRaw[]) — dùng cho endpoint test. */
export const mockCoursesRaw = rawCourses;

/** Mock cho student overview endpoint. */
export const mockOverview = {
  student_name: "Sinh viên Test",
  total_classes: rawCourses.length,
  ongoing_classes: 2,
  upcoming_classes: 2,
  classes: rawCourses, // BE trả raw shape
  courses: rawCourses, // alias — API có thể dùng `classes` hoặc `courses`
};

/** Helper: filter theo ngôn ngữ. */
export const mockCoursesByLanguage = (lang: string) =>
  mockCourses.filter((c) => c.code.toLowerCase().includes(lang.toLowerCase()));
