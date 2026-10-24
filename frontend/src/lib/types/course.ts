export type CourseLanguage = "java" | "python" | "javascript" | "c" | "cpp";

export type CourseStatus = "ongoing" | "upcoming" | "closed";

export type SessionStatus = "upcoming" | "open" | "closed";

export type CourseView = "grid" | "list";

export interface CourseApiRecord {
  course_id: string;
  course_name: string;
  avt_link: string | null;
  created_by: string;
  term: string;
  start_date: string;
  end_date: string;
  updated_at?: string | null;
  total_number_student: number;
  sessions?: CourseSession[];
  grades?: GradeRow[];
}

export interface CourseTermsResponse {
  academic_years: string[];
  semesters: number[];
}

export interface LessonApiRecord {
  lesson_id: number;
  lesson_number: number;
  lesson_name: string;
  course_id: string;
  total_number_assignment: number;
  total_number_student_finished: number;
  start_date: string;
  end_date: string;
}

export interface ProblemApiRecord {
  problem_id: number;
  lesson_id: number;
  title: string;
  description: string;
  time_limit_seconds: number;
  start_format_code: string;
  constraints: string;
  level: string;
  hint: string | null;
  complexity: string | null;
  start_datetime?: string;
  end_datetime?: string;
  total_number_testcase: number;
  report: string | null;
}

export interface CourseSummary {
  id: string | number;
  code: string;
  name: string;
  language: CourseLanguage;
  status: CourseStatus;
  teacher_name: string;
  semester: number;
  academic_year: string;
  group: number;
  start_date: string;
  sessions?: CourseSession[];
}

export interface CourseListParams {
  search?: string;
  semester?: number;
  academic_year?: string;
}

export interface CourseListStats {
  course_count: number;
  active_course_count: number;
  upcoming_courses: number;
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
  report: string | null;
  level: "easy" | "medium" | "hard";
  time_limit_seconds: number;
  total_number_testcase: number;
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
  start_date: string;
  end_date: string;
  student_count: number;
  updated_at: string | null;
  sessions: CourseSession[];
  grades?: GradeRow[];
}

export interface LessonMutationRequest {
  lesson_name: string;
  start_date: string;
  end_date: string;
  problem_ids: number[];
}

export interface StudentSearchResult {
  user_id: string;
  full_name: string;
  email: string;
  class_id: string | null;
}

export interface ClassApiRecord {
  class_id: string;
  type: string;
  course_number: number;
  department: string;
}

export interface GradeSessionColumn {
  id: number | string;
  order: number;
  title: string;
  status: SessionStatus;
  problems: Array<{ id: number | string; code: string; title: string }>;
}

export interface CourseStudent {
  enrollment_id: number;
  student_id: string;
  full_name: string;
  email: string;
  submitted_lessons: number;
  accepted_problems: number;
  total_lessons: number;
  progress_percent: number;
  submission_history: StudentSubmission[];
  class_id?: string | null;
}

export interface StudentSubmission {
  id: number;
  session: string;
  problem: string;
  status: "accepted" | "wrong_answer" | "compile_error";
  submitted_at: string;
  score: string;
}

export interface GradeRow {
  student_id: string;
  full_name: string;
  class_id: string | null;
  problem_scores: Array<number | null>;
  overall_score: number | null;
  session_scores?: Record<string, GradeScoreValue[]>;
}

export interface GradeScore {
  value: number | null;
  submitted?: boolean;
  is_similar?: boolean;
  is_overridden?: boolean;
  submission_id?: number | null;
  feedback?: string | null;
  status?: string | null;
  submitted_datetime?: string | null;
  manual_score?: number | null;
}

export type GradeScoreValue = number | null | GradeScore;

export interface SessionExercise {
  id: number;
  order: number;
  title: string;
  function_name: string | null;
  report: string | null;
  level: "easy" | "medium" | "hard";
  description: string;
  time_limit_seconds: number;
  total_number_testcase: number;
  submitted_count: number;
  constraints: string;
  hint: string | null;
  complexity: string | null;
  starter_code: string;
  starter_codes?: Record<string, string>;
  start_datetime: string;
  end_datetime: string;
  testcases: Array<{ id: number; input: string; expected_output: string; is_sample: boolean }>;
}

export interface SessionDetailData {
  id: number;
  order: number;
  title: string;
  course_code: string;
  course_name: string;
  start_date: string;
  end_date: string;
  deadline_notice: string;
  submitted_students: number;
  total_students: number;
  stats: {
    submission_rate: number;
    completed_students: number;
    avg_score: number | null  ;
    score_diff: string;
    ast_cases: number;
    ast_similarity: string;
  };
  alert?: {
    problem_code: string;
    missing_students: number;
    problem_name: string;
    deadline_text: string;
  };
  exercises: SessionExercise[];
}

// SỬA: Payload dùng chung cho form chỉnh nội dung bài tập và testcase.
export interface ProblemUpdateRequest {
  title?: string;
  description?: string;
  constraints?: string;
  level?: string;
  hint?: string | null;
  complexity?: string | null;
  time_limit_seconds?: number;
  start_datetime?: string;
  end_datetime?: string;
  starter_code?: string;
  function_name?: string;
  starter_codes?: Record<string, string>;
  testcases?: Array<{ input: unknown[]; expected_output: unknown; is_sample: boolean; input_type?: string; expected_output_type?: string }>;
}

export interface ProblemDetailData {
  id: number;
  lesson_id: number | null;
  course_id: string | null;
  code: string | null;
  title: string;
  function_name: string | null;
  description: string;
  constraints: string;
  level: string;
  hint: string | null;
  complexity: string | null;
  time_limit_seconds: number;
  total_number_testcase: number;
  start_datetime: string;
  end_datetime: string;
  starter_code: string;
  starter_codes?: Record<string, string>;
  testcases: Array<{ id: number; input: string; expected_output: string; is_sample: boolean }>;
  submitted_count?: number;
}
