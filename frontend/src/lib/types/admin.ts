import type { CourseApiRecord, LessonMutationRequest } from "@/lib/types/course";
import type { SubmissionDetail } from "@/lib/types/dashboard";

export interface AdminClass {
  class_id: string;
  type: string;
  course_number: number;
  department: string;
  student_count: number;
}

export interface AdminEnrollment {
  enrollment_id: number;
  student_id: string;
  full_name: string;
  email: string;
}

export interface AdminTestcase {
  id: number;
  input: unknown;
  expected_output: unknown;
  is_sample: boolean;
  input_type: "json_args" | "stdin";
  expected_output_type: "json" | "stdout";
}

export type AdminTestcasePayload = Omit<AdminTestcase, "id">;

export interface AdminPreviewResult {
  status: string;
  compile_output: string | null;
  review_token?: string | null;
  cases: Array<{
    index: number;
    status: string;
    input: unknown;
    expected_output: unknown;
    actual_output: unknown | null;
    stderr: string | null;
    time: number | null;
  }>;
}

export interface AdminAIReview {
  time_complexity: string;
  space_complexity: string;
  complexity_explanation: string;
  issues: string[];
  optimization: {
    is_optimizable: boolean;
    suggestion: string;
    expected_time_complexity: string;
    expected_space_complexity: string;
  };
  summary: string;
}

export interface AdminAIConnection {
  connected: boolean;
  model: string;
  model_available: boolean;
}

export interface AdminProblem {
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
  starter_codes: Record<string, string>;
  testcases: AdminTestcase[];
}

export interface AdminProblemItem {
  id: number;
  code: string | null;
  title: string;
  level: string;
  lesson_id: number | null;
  total_number_testcase: number;
}

export interface AdminProblemList {
  items: AdminProblemItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminProblemPayload {
  title: string;
  function_name: string;
  description: string;
  constraints: string;
  level: "easy" | "medium" | "hard";
  time_limit_seconds: number;
  start_datetime: string;
  end_datetime: string;
  starter_codes: Record<string, string>;
  hint: string | null;
  complexity: string | null;
  testcases: Array<{ input: unknown[]; expected_output: unknown; is_sample: boolean }>;
}

export interface AdminLesson {
  id: number;
  order: number;
  title: string;
  course_code: string;
  course_name: string;
  start_date: string;
  end_date: string;
  deadline_notice: string;
  submitted_students: number | null;
  total_students: number | null;
  stats: { submission_rate: number; completed_students: number; avg_score: number } | null;
  exercises: Array<Omit<AdminProblem, "lesson_id" | "course_id" | "code" | "start_datetime" | "end_datetime"> & {
    order: number; report: string | null; submitted_count: number | null;
  }>;
}

export interface JudgeResult {
  stdout: string | null;
  stderr: string | null;
  compile_output: string | null;
  status: { id: number; description: string } | null;
  time?: string | null;
  memory?: number | null;
}

export type AdminSubmissionDetail = Omit<SubmissionDetail, "testcases"> & {
  problem_id: number;
  problem_description: string;
  problem_constraints: string;
  problem_level: string;
  problem_function_name: string | null;
  testcases: AdminTestcase[];
};

export type AdminCourse = CourseApiRecord;
export type AdminLessonPayload = LessonMutationRequest;
