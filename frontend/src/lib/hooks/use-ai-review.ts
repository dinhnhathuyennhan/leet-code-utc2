"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getReviewUsage, reviewSubmission } from "@/lib/api/endpoints/ai-review";
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
  const queryClient = useQueryClient();
  return useMutation<AiReviewResult, unknown, void>({
    mutationKey: ["ai", "review", submissionId, locale],
    mutationFn: () => reviewSubmission(submissionId, locale),
    retry: false,
    // Thành công thì tốn một lượt, lỗi thì backend hoàn lượt: đều tải lại số lượt.
    onSettled: () => queryClient.invalidateQueries({ queryKey: aiReviewUsageKey(submissionId) }),
  });
}

export const aiReviewUsageKey = (submissionId: number | string) =>
  ["ai", "review-usage", String(submissionId)] as const;

/** Số lượt AI review còn lại của sinh viên cho bài tập của bài nộp. */
export function useAiReviewUsage(submissionId: number | string) {
  return useQuery({
    queryKey: aiReviewUsageKey(submissionId),
    queryFn: () => getReviewUsage(submissionId),
  });
}
