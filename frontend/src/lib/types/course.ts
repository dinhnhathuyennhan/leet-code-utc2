/**
 * Type cho Course, khớp với backend `CourseResponse`
 * (xem `docs/api-design-course.md`).
 *
 * Backend chưa hỗ trợ các field: `language`, `status`, `room`, `sessions`,
 * `group`, `student_count`, `code` riêng (lấy từ `course_id`),
 * `teacher_name`, `academic_year`, `semester` (lấy từ `term`), `updated_at`.
 * Phía FE tự suy ra những field này từ dữ liệu sẵn có hoặc để trống cho tới
 * khi BE bổ sung. Tránh đặt giả định không đúng vào type chính.
 *
 * Một số type phụ trợ (`CourseLanguage`, `CourseStatus`, `CourseSession`...)
 * vẫn được giữ để các màn hình Phase 2 (Lesson/Problem) chưa được code vẫn
 * type-check được; khi đó xoá.
 */

export type CourseLanguage = "java" | "python" | "javascript" | "c" | "cpp";
export type CourseStatus = "ongoing" | "upcoming" | "closed";
export type SessionStatus = "upcoming" | "open" | "closed";
export type CourseView = "grid" | "list";

export interface CourseSummary {
  id: string;
  code: string;
  name: string;
  term: string;
  start_date: string;
  end_date: string;
  avt_link: string | null;
  created_by: string;
  total_number_student: number;
}

/** Chi tiết lớp — hiện trùng `CourseSummary`. Sau này BE thêm session/lesson sẽ mở rộng. */
export type CourseDetail = CourseSummary;

export interface CourseStudent {
  enrollment_id: number;
  student_id: string;
  full_name: string;
  email: string;
}

export interface CourseListParams {
  /**
   * Filter server-side theo `term` (vd: "HK1 (2024-2025)").
   * BE sẽ `contains` (LIKE %term%) — match một phần nên user có thể gõ
   * "HK1" hay "2024" đều được.
   */
  term?: string;
  /** Giữ các field cũ để tương thích callers cũ, sẽ dùng khi BE tách cột. */
  search?: string;
  semester?: number;
  academic_year?: string;
}

export interface CourseListStats {
  course_count: number;
  completed_problems: number;
  total_problems: number;
  due_this_week: number;
}

/** ─── Type dùng cho Phase 2/4 (Lesson, Problem, Session) — BE chưa có endpoint, giữ tạm để file cũ build được. ─── */
export interface ProblemRow {
  id: number;
  order: number;
  title: string;
  code: string;
  topic: string;
  time_limit_s: number;
  memory_limit_mb: number;
  submitted_count: number;
  accepted_rate: number;
}

export interface SessionProgress {
  students_submitted: number;
  completed_count: number;
  compile_error_count: number;
}

export interface CourseSession {
  id: number;
  order: number;
  title: string;
  status: SessionStatus;
  opens_at: string | null;
  deadline: string;
  problems: ProblemRow[];
  participant_count: number | null;
  progress?: SessionProgress;
}