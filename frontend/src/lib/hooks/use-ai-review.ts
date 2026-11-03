"use client";

import { useMutation } from "@tanstack/react-query";

import { reviewSubmission } from "@/lib/api/endpoints/ai-review";
import type { Locale } from "@/lib/i18n";
import type { AiReviewResult } from "@/lib/types/ai-review";

/**
 * Gọi AI review cho một bài nộp theo ngôn ngữ hiện tại.
 *
 * Dùng mutation (không phải query) vì chỉ chạy khi sinh viên bấm nút, không tự
 * gọi khi mount, không refetch nền và không retry tự động (mỗi lượt tốn GPU,
 * retry khi `AI_BUSY` còn làm hàng đợi tắc hơn).
 *
 * `locale` được đưa vào mutationKey để mỗi ngôn ngữ là một mutation riêng:
 * cache của `useMutation` trong React Query là per-observer (theo key), nên
 * tách key giúp panel giữ được kết quả của cả hai ngôn ngữ và đổi qua lại
 * không phải chờ Ollama sinh lại.
 */
export function useAiReview(submissionId: number | string, locale: Locale) {
  return useMutation<AiReviewResult, unknown, void>({
    mutationKey: ["submissions", "ai-review", submissionId, locale],
    mutationFn: () => reviewSubmission(submissionId, locale),
    retry: false,
  });
}
