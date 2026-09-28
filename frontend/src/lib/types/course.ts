export type CourseLanguage = "java" | "python" | "javascript" | "c" | "cpp";

export type CourseStatus = "ongoing" | "upcoming" | "closed";

export type SessionStatus = "upcoming" | "open" | "closed";

export type CourseView = "grid" | "list";

export interface CourseSummary {
  id: number;
  code: string;
  name: string;
  language: CourseLanguage;
  status: CourseStatus;
  teacher_name: string;
  semester: number;
  academic_year: string;
  group: number;
}

export interface CourseListParams {
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

export interface CourseListResponse {
  items: CourseSummary[];
  stats: CourseListStats;
}

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

export interface CourseDetail extends CourseSummary {
  room: string;
  end_date: string;
  student_count: number;
  updated_at: string;
  sessions: CourseSession[];
}
