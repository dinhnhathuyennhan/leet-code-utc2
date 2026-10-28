import type { CourseSummary } from "@/lib/types/course";

export type JudgeKind = "pending" | "accepted" | "wrong_answer" | "similarity" | "compile_error" | "graded";

export type PendingFilter = "all" | "pending" | "wrong_answer" | "compile_error";

export interface TeacherOverview {
  teacher_name: string;
  term_label: string;
  stats: {
    active_courses: number;
    pending_grading: number;
  };
  recent_courses: CourseSummary[];
}

export interface PendingSubmission {
  id: number;
  course_id: string;
  lesson_id: number;
  problem_id: number;
  student_name: string;
  student_code: string;
  course_code: string;
  session_label: string;
  topic: string;
  judge_kind: JudgeKind;
  judge_label: string;
  issue: string;
  /** Trạng thái thật trong database, dùng để lọc và hiển thị thay cho judge_kind. */
  status: string;
  manual_score?: number | null;
  passed_count: number;
  total_testcases: number;
}

export interface PendingSubmissionParams {
  filter: PendingFilter;
  search?: string;
  limit?: number;
  course?: string;
  lesson_id?: number;
  problem_id?: number;
  include_graded?: boolean;
}

export interface PendingSubmissionsResponse {
  items: PendingSubmission[];
  total: number;
  counts: Record<PendingFilter, number> & { graded?: number; ungraded?: number; needs_grading?: number; late_appeal?: number; similarity?: number; error?: number };
}

export interface SubmissionTestcase {
  id: number;
  input: string;
  expected_output: string;
  is_sample: boolean;
}

export interface SubmissionDetail {
  id: number;
  student_name: string;
  student_code: string;
  class_id: string | null;
  course_code: string;
  course_name: string;
  session_label: string;
  problem_code: string | null;
  problem_title: string;
  language: string;
  submitted_code: string;
  status: string;
  compile_output: string | null;
  feedback: string | null;
  manual_score?: number | null;
  passed_count: number;
  total_testcases: number;
  submitted_datetime: string;
  testcases: SubmissionTestcase[];
}

// ─── Student Dashboard ──────────────────────────────────────────────

/**
 * Response cho `GET /students/{student_id}/dashboard`.
 * Cấu trúc trùng với `StudentDashboardResponse` ở backend.
 */
export interface StudentOverview {
  total_classes: number;
  completed_problems: number;
  total_problems: number;
  /** 0-10; `null` khi SV chưa có submission nào. */
  average_score: number | null;
  courses: CourseSummary[];
}
