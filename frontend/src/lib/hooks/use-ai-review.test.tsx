/**
 * Lượt AI review tính theo (sinh viên, bài tập), không theo bài nộp: review một bài nộp
 * phải làm mới số lượt đang cache của mọi bài nộp khác.
 */
import { describe, expect, it } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";

import { aiReviewUsageKey, useAiReview } from "./use-ai-review";
import { server } from "@/test/mocks/server";

const REVIEW = {
  time_complexity: "O(n)",
  space_complexity: "O(1)",
  complexity_explanation: "x",
  issues: [],
  optimization: { is_optimizable: false, suggestion: "x", expected_time_complexity: "O(n)", expected_space_complexity: "O(1)" },
  summary: "x",
};

describe("useAiReview", () => {
  it("invalidates the cached usage of every submission after a review", async () => {
    server.use(http.post("http://localhost:8000/ai/review/:id", () => HttpResponse.json(REVIEW)));
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 30_000 } } });
    // Bài nộp #1 và #2 của cùng bài tập đã cache "còn 3 lượt"
    queryClient.setQueryData(aiReviewUsageKey(1), { limit: 3, used: 0, remaining: 3 });
    queryClient.setQueryData(aiReviewUsageKey(2), { limit: 3, used: 0, remaining: 3 });
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useAiReview(2, "vi"), { wrapper });
    await act(() => result.current.mutateAsync());

    await waitFor(() => {
      expect(queryClient.getQueryState(aiReviewUsageKey(1))?.isInvalidated).toBe(true);
      expect(queryClient.getQueryState(aiReviewUsageKey(2))?.isInvalidated).toBe(true);
    });
  });
});
