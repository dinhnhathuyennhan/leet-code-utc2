// ─── Sinh viên: nộp bài và xem kết quả chấm ──────────────────────────────────

/** Trạng thái bài nộp sau khi Judge0 chấm. */
export type StudentSubmissionStatus =
  | "accepted"
  | "wrong_answer"
  | "compile_error"
  | "runtime_error"
  | "time_limit_exceeded"
  | "internal_error"
  | "error"
  | "pending"
  | "processing";

export interface StudentSubmission {
  id: number;
  problem_id: number;
  problem_code: string | null;
  problem_title: string;
  course_id: string;
  course_name: string;
  lesson_id: number;
  session_label: string;
  language: string;
  status: StudentSubmissionStatus;
  passed_count: number;
  total_testcases: number;
  submitted_datetime: string;
}

export interface StudentSubmissionsResponse {
  items: StudentSubmission[];
  total: number;
  counts: {
    all: number;
    accepted: number;
    wrong_answer: number;
    compile_error: number;
    pending: number;
  };
}

export interface StudentSubmissionTestcase {
  id: number;
  input: unknown;
  expected_output: unknown;
  is_sample: boolean;
}

export interface StudentSubmissionDetail {
  id: number;
  problem_id: number;
  problem_code: string | null;
  problem_title: string;
  course_id: string;
  course_name: string;
  lesson_id: number;
  session_label: string;
  language: string;
  submitted_code: string;
  status: StudentSubmissionStatus;
  compile_output: string | null;
  feedback: string | null;
  passed_count: number;
  total_testcases: number;
  submitted_datetime: string;
  testcases: StudentSubmissionTestcase[];
}

/**
 * Kết quả chấm rút gọn từ `GET /submissions/{id}/result`.
 *
 * Dùng để poll trong lúc backend chấm nền xong.
 */
export interface SubmissionResult {
  submission_id: number;
  status: StudentSubmissionStatus;
  passed_count: number;
  total_testcases: number;
  compile_output: string | null;
}

/**
 * Shape tối thiểu để hiển thị kết quả chấm.
 *
 * Nhận được cả `SubmissionResult` (rút gọn, dùng khi poll) lẫn
 * `StudentSubmissionDetail` (đầy đủ, dùng khi mở trang chi tiết bài nộp),
 * nên các trường không có trong bản rút gọn đều là optional.
 */
export type GradingResultView = Pick<
  StudentSubmissionDetail,
  "status" | "passed_count" | "total_testcases" | "compile_output"
> &
  Partial<
    Pick<
      StudentSubmissionDetail,
      "feedback" | "language" | "submitted_datetime" | "problem_code" | "problem_title" | "problem_id" | "testcases"
    >
  >;

/** Body cho POST nộp bài / chạy thử. */
export interface SubmitCodePayload {
  code: string;
  language: string;
}
