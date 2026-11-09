/**
 * Test API layer của AI review (axios + MSW): URL, method, body rỗng, timeout
 * và việc map từng mã lỗi backend sang `AiReviewError.code`.
 */
import { afterEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";

import { server } from "@/test/mocks/server";
import { setAccessToken } from "@/lib/auth/token-store";
import axiosInstance from "@/lib/axios";
import {
  AI_REVIEW_TIMEOUT_MS,
  AiReviewError,
  reviewSubmission,
} from "@/lib/api/endpoints/ai-review";
import { ApiError } from "@/lib/api/error";

const API = "http://localhost:8000";

const REVIEW = {
  time_complexity: "O(n)",
  space_complexity: "O(1)",
  complexity_explanation: "Duyệt từ 2 tới n-1.",
  issues: ["Duyệt quá số lần cần thiết"],
  optimization: {
    is_optimizable: true,
    suggestion: "Chỉ cần duyệt ước tới sqrt(n).",
    expected_time_complexity: "O(sqrt(n))",
    expected_space_complexity: "O(1)",
  },
  summary: "Có thể giảm xuống O(sqrt(n)).",
};

afterEach(() => {
  server.resetHandlers();
  setAccessToken(null);
});

describe("reviewSubmission", () => {
  it("POSTs to the submission URL, sends no code and attaches the Bearer token", async () => {
    let seen: { method: string; url: string; body: string; auth: string | null } | null = null;
    server.use(
      http.post(`${API}/ai/review/:id`, async ({ request }) => {
        seen = {
          method: request.method,
          url: request.url,
          body: await request.text(),
          auth: request.headers.get("authorization"),
        };
        return HttpResponse.json(REVIEW);
      }),
    );
    setAccessToken("token-abc");

    const result = await reviewSubmission(42);

    expect(result).toEqual(REVIEW);
    expect(seen).not.toBeNull();
    expect(seen!.method).toBe("POST");
    expect(seen!.url).toBe(`${API}/ai/review/42`);
    // Backend tự lấy code từ DB: client chỉ gửi ngôn ngữ hiển thị, không gửi code.
    expect(JSON.parse(seen!.body)).toEqual({ locale: "vi" });
    expect(seen!.body).not.toContain("submitted_code");
    expect(seen!.auth).toBe("Bearer token-abc");
  });

  it("encodes the submission id so no other path can be injected", async () => {
    let url = "";
    server.use(
      http.post(`${API}/ai/review/:id`, ({ request }) => {
        url = request.url;
        return HttpResponse.json(REVIEW);
      }),
    );

    await reviewSubmission("1/../../admin");

    expect(url).toContain("/ai/review/1%2F..%2F..%2Fadmin");
  });

  it("sends the current locale in the body, defaulting to vi", async () => {
    const bodies: unknown[] = [];
    server.use(
      http.post(`${API}/ai/review/:id`, async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json(REVIEW);
      }),
    );

    await reviewSubmission(1);
    await reviewSubmission(1, "en");

    expect(bodies).toEqual([{ locale: "vi" }, { locale: "en" }]);
  });

  it("uses a long timeout (200s) instead of the default 10s", async () => {
    let timeout: number | undefined;
    const id = axiosInstance.interceptors.request.use((config) => {
      timeout = config.timeout;
      return config;
    });
    server.use(http.post(`${API}/ai/review/:id`, () => HttpResponse.json(REVIEW)));

    try {
      await reviewSubmission(1);
    } finally {
      axiosInstance.interceptors.request.eject(id);
    }

    expect(AI_REVIEW_TIMEOUT_MS).toBe(200_000);
    expect(timeout).toBe(200_000);
  });

  it.each([
    [503, "AI_BUSY", "AI đang phân tích bài khác, vui lòng thử lại sau"],
    [503, "AI_UNAVAILABLE", "Không thể kết nối AI Server."],
    [504, "AI_TIMEOUT", "AI xử lý quá thời gian cho phép."],
    [502, "AI_INVALID_RESPONSE", "AI trả về dữ liệu không hợp lệ."],
    [409, "SUBMISSION_NOT_ACCEPTED", "Bài nộp phải pass toàn bộ testcase mới được review code"],
    [422, "CODE_TOO_LONG", "Mã nguồn dài hơn 15000 ký tự, AI không review được"],
    [404, "NOT_FOUND", "Không tìm thấy bài nộp"],
  ])("HTTP %i %s -> AiReviewError keeps the original code and message", async (status, code, message) => {
    server.use(
      http.post(`${API}/ai/review/:id`, () =>
        HttpResponse.json({ error_code: code, message }, { status }),
      ),
    );

    const error = await reviewSubmission(1).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(AiReviewError);
    // Vẫn là ApiError để code khác (getErrorMessage, ErrorState) dùng chung được.
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status, code, detail: message, message });
  });

  it("an unexpected 5xx error does not leak technical details to the UI", async () => {
    server.use(
      http.post(`${API}/ai/review/:id`, () =>
        HttpResponse.json(
          { error_code: "INTERNAL_ERROR", message: "Traceback: sqlalchemy.exc.OperationalError" },
          { status: 500 },
        ),
      ),
    );

    const error = (await reviewSubmission(1).catch((e: unknown) => e)) as AiReviewError;

    expect(error.code).toBe("UNKNOWN");
    expect(error.detail).not.toContain("Traceback");
  });

  it("a 404 without a body still maps to NOT_FOUND", async () => {
    server.use(
      http.post(`${API}/ai/review/:id`, () => new HttpResponse(null, { status: 404 })),
    );

    const error = (await reviewSubmission(1).catch((e: unknown) => e)) as AiReviewError;

    expect(error.code).toBe("NOT_FOUND");
  });

  it("network failure -> code NETWORK, isNetworkError = true", async () => {
    server.use(http.post(`${API}/ai/review/:id`, () => HttpResponse.error()));

    const error = (await reviewSubmission(1).catch((e: unknown) => e)) as AiReviewError;

    expect(error.code).toBe("NETWORK");
    expect(error.isNetworkError).toBe(true);
  });
});
