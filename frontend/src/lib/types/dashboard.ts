import type { CourseSummary } from "@/lib/types/course";

export type JudgeKind = "wrong_answer" | "similarity" | "compile_error";

export type PendingFilter = "all" | "late_appeal" | "similarity" | "error";

export interface TeacherOverview {
  teacher_name: string;
  term_label: string;
  stats: {
    active_courses: number;
    pending_grading: number;
    plagiarism_cases: number;
  };
  recent_courses: CourseSummary[];
}

export interface PendingSubmission {
  id: number;
  student_name: string;
  student_code: string;
  course_code: string;
  session_label: string;
  topic: string;
  judge_kind: JudgeKind;
  judge_label: string;
  issue: string;
}

export interface PendingSubmissionParams {
  filter: PendingFilter;
  search?: string;
  limit?: number;
}

export interface PendingSubmissionsResponse {
  items: PendingSubmission[];
  total: number;
  counts: Record<PendingFilter, number>;
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
  passed_count: number;
  total_testcases: number;
  submitted_datetime: string;
  testcases: SubmissionTestcase[];
}

export interface PlagiarismAlert {
  id: number;
  problem_code: string;
  student_names: string[];
  reason: string;
  similarity: number;
}
