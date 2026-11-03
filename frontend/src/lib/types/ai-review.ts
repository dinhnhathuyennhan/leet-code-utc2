// ─── AI review code (chỉ cho bài nộp đã pass hết testcase) ────────────────────

/** Hướng tối ưu AI đề xuất. */
export interface AiReviewOptimization {
  is_optimizable: boolean;
  suggestion: string;
  expected_time_complexity: string;
  expected_space_complexity: string;
}

/** Response của `POST /submissions/{id}/ai-review` (khớp `AIReviewResponse` ở backend). */
export interface AiReviewResult {
  time_complexity: string;
  space_complexity: string;
  complexity_explanation: string;
  issues: string[];
  optimization: AiReviewOptimization;
  summary: string;
}

/** Mã lỗi backend trả về cho endpoint AI review. */
export type AiReviewErrorCode =
  | "AI_BUSY"
  | "AI_UNAVAILABLE"
  | "AI_TIMEOUT"
  | "AI_INVALID_RESPONSE"
  | "SUBMISSION_NOT_ACCEPTED"
  | "CODE_TOO_LONG"
  | "NOT_FOUND"
  | "NETWORK"
  | "UNKNOWN";
