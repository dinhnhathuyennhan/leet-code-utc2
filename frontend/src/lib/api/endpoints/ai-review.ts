import type { AxiosError } from "axios";

import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import { ApiError } from "@/lib/api/error";
import type { Locale } from "@/lib/i18n";
import type { AiReviewErrorCode, AiReviewResult, AiReviewUsage } from "@/lib/types/ai-review";

/**
 * Backend chờ Ollama tối đa 180s (lần đầu nạp model ~80s), nên nới timeout so
 * với mặc định 10s của axios, chừa thêm thời gian truyền mạng.
 */
export const AI_REVIEW_TIMEOUT_MS = 200_000;

const KNOWN_CODES: ReadonlySet<string> = new Set<AiReviewErrorCode>([
  "AI_BUSY",
  "AI_UNAVAILABLE",
  "AI_TIMEOUT",
  "AI_INVALID_RESPONSE",
  "SUBMISSION_NOT_ACCEPTED",
  "CODE_TOO_LONG",
  "AI_REVIEW_LIMIT_REACHED",
  "NOT_FOUND",
]);

/**
 * Lỗi AI review mang theo `code` để UI chọn thông báo và quyết định có cho
 * "Thử lại" hay không.
 *
 * Không dùng `wrapAxiosError` chung: hàm đó đổi mọi lỗi 5xx thành
 * "Hệ thống đang gặp sự cố", làm mất phân biệt AI bận / AI mất kết nối / quá giờ.
 */
export class AiReviewError extends ApiError {
  readonly code: AiReviewErrorCode;

  constructor(params: { status: number; code: AiReviewErrorCode; detail: string; isNetworkError?: boolean }) {
    super(params);
    this.name = "AiReviewError";
    this.code = params.code;
  }
}

function toAiReviewError(error: unknown): AiReviewError {
  const axiosError = error as AxiosError<{ error_code?: unknown; message?: unknown }>;
  const response = axiosError.response;

  if (!response) {
    // Hết timeout phía client cũng rơi vào đây (axios báo ECONNABORTED).
    const timedOut = axiosError.code === "ECONNABORTED" || axiosError.code === "ETIMEDOUT";
    return new AiReviewError({
      status: 0,
      code: timedOut ? "AI_TIMEOUT" : "NETWORK",
      detail: timedOut ? "AI xử lý quá thời gian cho phép." : "Mất kết nối, vui lòng thử lại.",
      isNetworkError: true,
    });
  }

  const rawCode = response.data?.error_code;
  const code: AiReviewErrorCode =
    typeof rawCode === "string" && KNOWN_CODES.has(rawCode)
      ? (rawCode as AiReviewErrorCode)
      : response.status === 404
        ? "NOT_FOUND"
        : "UNKNOWN";
  const message = response.data?.message;

  return new AiReviewError({
    status: response.status,
    code,
    // Chỉ dùng message backend cho lỗi đã biết; lỗi lạ (500 có stack trace...)
    // không đưa chi tiết kỹ thuật lên UI.
    detail:
      code !== "UNKNOWN" && typeof message === "string" && message.trim()
        ? message
        : "Đã có lỗi xảy ra, vui lòng thử lại.",
  });
}

/**
 * Nhờ AI review hiệu năng một bài nộp đã pass toàn bộ testcase.
 *
 * Không gửi code: backend tự lấy code, ngôn ngữ và đề bài từ bài nộp. Chỉ gửi
 * `locale` để backend chọn system prompt đúng ngôn ngữ cho phần văn xuôi.
 */
export async function reviewSubmission(
  submissionId: number | string,
  locale: Locale = "vi",
): Promise<AiReviewResult> {
  try {
    const response = await axiosInstance.post<AiReviewResult>(
      `/ai/review/${encodeURIComponent(String(submissionId))}`,
      { locale },
      { timeout: AI_REVIEW_TIMEOUT_MS },
    );
    return response.data;
  } catch (error) {
    throw toAiReviewError(error);
  }
}

/** Số lượt AI review sinh viên đã dùng / còn lại cho bài tập của bài nộp này. */
export async function getReviewUsage(submissionId: number | string): Promise<AiReviewUsage> {
  try {
    const response = await axiosInstance.get<AiReviewUsage>(
      `/ai/review/${encodeURIComponent(String(submissionId))}/usage`,
    );
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}
