/**
 * Component test cho AI review: điều kiện hiện nút, chỉ gọi AI khi bấm,
 * các trạng thái đang chạy / lỗi / thành công, hiển thị kết quả và i18n.
 *
 * Gọi API thật qua axios + MSW (không mock module) để kiểm tra cả đường đi
 * request -> map lỗi -> hiển thị.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse, delay } from "msw";

import { AiReviewSection, AI_REVIEW_WARMUP_HINT_MS } from "./ai-review-panel";
import { server } from "@/test/mocks/server";
import { renderWithProviders } from "@/test/utils/render";
import { LocaleProvider, resetLocaleStore, useLocale } from "@/lib/i18n";
import type { AiReviewResult } from "@/lib/types/ai-review";

const URL = "http://localhost:8000/ai/review/:id";

const PRIME_REVIEW: AiReviewResult = {
  time_complexity: "O(n)",
  space_complexity: "O(1)",
  complexity_explanation: "Vòng lặp chạy từ 2 tới n-1.",
  issues: ["Duyệt quá số lần cần thiết", "  "],
  optimization: {
    is_optimizable: true,
    suggestion: "Chỉ cần duyệt ước tới sqrt(n).",
    expected_time_complexity: "O(sqrt(n))",
    expected_space_complexity: "O(1)",
  },
  summary: "Code đúng nhưng chưa tối ưu.",
};

const OPTIMAL_REVIEW: AiReviewResult = {
  time_complexity: "O(n)",
  space_complexity: "O(n)",
  complexity_explanation: "Duyệt một lần với hash map.",
  issues: [],
  optimization: {
    is_optimizable: false,
    suggestion: "Không cần cải thiện thêm.",
    expected_time_complexity: "O(n)",
    expected_space_complexity: "O(n)",
  },
  summary: "Đã tối ưu.",
};

const ACCEPTED = { id: 7, status: "accepted", passed_count: 3, total_testcases: 3 };

/** Đếm số lần gọi AI và trả về response tuỳ chọn. */
function mockReview(respond: () => Response | Promise<Response> = () => HttpResponse.json(PRIME_REVIEW)) {
  const calls: string[] = [];
  server.use(
    http.post(URL, async ({ request }) => {
      calls.push(request.url);
      return respond();
    }),
  );
  return calls;
}

function renderSection(submission: Parameters<typeof AiReviewSection>[0]["submission"] = ACCEPTED) {
  return renderWithProviders(<AiReviewSection submission={submission} />);
}

const reviewButton = () => screen.getByRole("button", { name: /Review code/ });

beforeEach(() => {
  window.localStorage.clear();
  resetLocaleStore();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("AiReviewSection — điều kiện hiện nút", () => {
  it.each([
    ["wrong_answer", 2, 3],
    ["compile_error", 0, 3],
    ["runtime_error", 1, 3],
    ["time_limit_exceeded", 2, 3],
    ["pending", 0, 3],
    ["processing", 0, 3],
    ["accepted", 2, 3],
    ["accepted", 0, 0],
  ])("không render gì khi status=%s, passed=%i/%i", (status, passed, total) => {
    const calls = mockReview();
    const { container } = renderSection({ id: 1, status, passed_count: passed, total_testcases: total });

    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByRole("button", { name: /Review code/ })).toBeNull();
    expect(calls).toHaveLength(0);
  });

  it("không render khi chưa có bài nộp", () => {
    const { container } = renderSection(null);
    expect(container).toBeEmptyDOMElement();
  });

  it("hiện nút + lời mời khi pass hết testcase", () => {
    renderSection();

    expect(reviewButton()).toBeEnabled();
    expect(screen.getByText(/Bài đã pass toàn bộ testcase/)).toBeInTheDocument();
  });
});

describe("AiReviewSection — chỉ gọi AI khi bấm", () => {
  it("không gọi API khi mount, chỉ gọi đúng 1 lần sau khi bấm", async () => {
    const calls = mockReview();
    const user = userEvent.setup();
    renderSection();

    // Chờ một nhịp để chắc chắn không có request tự động.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(calls).toHaveLength(0);

    await user.click(reviewButton());

    await screen.findByTestId("ai-review-result");
    expect(calls).toEqual(["http://localhost:8000/ai/review/7"]);
  });

  it("bấm liên tục khi đang chạy cũng chỉ gửi 1 request", async () => {
    const calls = mockReview(async () => {
      await delay(150);
      return HttpResponse.json(PRIME_REVIEW);
    });
    const user = userEvent.setup();
    renderSection();

    await user.click(reviewButton());
    const running = screen.getByRole("button", { name: /Đang review/ });
    expect(running).toBeDisabled();
    expect(running).toHaveAttribute("aria-busy", "true");
    await user.click(running);
    await user.click(running);

    await screen.findByTestId("ai-review-result");
    expect(calls).toHaveLength(1);
  });

  it("lỗi thì không tự retry", async () => {
    const calls = mockReview(() =>
      HttpResponse.json({ error_code: "AI_BUSY", message: "bận" }, { status: 503 }),
    );
    const user = userEvent.setup();
    renderSection();

    await user.click(reviewButton());
    await screen.findByRole("alert");
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(calls).toHaveLength(1);
  });
});

describe("AiReviewSection — đang chạy", () => {
  it("hiện skeleton, vùng kết quả aria-busy và nhắc khởi động sau 15 giây", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    mockReview(async () => {
      await delay("infinite");
      return HttpResponse.json(PRIME_REVIEW);
    });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderSection();

    await user.click(reviewButton());

    expect(await screen.findByTestId("ai-review-loading")).toBeInTheDocument();
    expect(screen.getByTestId("ai-review-loading").parentElement).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByText(/Lần đầu có thể mất/)).toBeNull();

    await act(async () => {
      vi.advanceTimersByTime(AI_REVIEW_WARMUP_HINT_MS - 1_000);
    });
    expect(screen.queryByText(/Lần đầu có thể mất/)).toBeNull();

    await act(async () => {
      vi.advanceTimersByTime(1_000);
    });
    expect(screen.getByText(/Lần đầu có thể mất 1–2 phút/)).toBeInTheDocument();
  });
});

describe("AiReviewSection — kết quả", () => {
  async function openReview(review: AiReviewResult = PRIME_REVIEW) {
    mockReview(() => HttpResponse.json(review));
    const user = userEvent.setup();
    renderSection();
    await user.click(reviewButton());
    const card = await screen.findByTestId("ai-review-result");
    return { user, card };
  }

  it("bài tối ưu được: hiện trước → sau ở thẻ thời gian, bộ nhớ không đổi thì không có mũi tên", async () => {
    await openReview();

    const time = screen.getByTestId("ai-review-time");
    expect(within(time).getByText("O(n)")).toBeInTheDocument();
    expect(within(time).getByText("O(sqrt(n))")).toBeInTheDocument();
    expect(within(time).getByLabelText("→")).toBeInTheDocument();

    const space = screen.getByTestId("ai-review-space");
    expect(within(space).getByText("O(1)")).toBeInTheDocument();
    expect(within(space).queryByLabelText("→")).toBeNull();
  });

  it("hiện tóm tắt, giải thích, điểm chưa tối ưu (bỏ dòng rỗng) và hướng cải thiện", async () => {
    await openReview();

    expect(screen.getByText("Code đúng nhưng chưa tối ưu.")).toBeInTheDocument();
    expect(screen.getByText("Vòng lặp chạy từ 2 tới n-1.")).toBeInTheDocument();
    expect(screen.getByText("Điểm chưa tối ưu")).toBeInTheDocument();
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(1);
    expect(items[0]).toHaveTextContent("Duyệt quá số lần cần thiết");
    expect(screen.getByText("(1)")).toBeInTheDocument();
    expect(screen.getByText("Hướng cải thiện")).toBeInTheDocument();
    expect(screen.getByText("Chỉ cần duyệt ước tới sqrt(n).")).toBeInTheDocument();
    expect(screen.queryByText("Code đã ở mức tối ưu hợp lý")).toBeNull();
  });

  it("luôn có chú thích AI không ảnh hưởng điểm", async () => {
    await openReview();
    expect(screen.getByText(/Không ảnh hưởng tới điểm/)).toBeInTheDocument();
  });

  it("bài đã tối ưu: không có mũi tên, không có danh sách vấn đề, hiện khối 'đã tối ưu'", async () => {
    await openReview(OPTIMAL_REVIEW);

    expect(screen.queryByLabelText("→")).toBeNull();
    expect(screen.queryByRole("listitem")).toBeNull();
    expect(screen.getByText("Không phát hiện điểm chưa tối ưu.")).toBeInTheDocument();
    expect(screen.getByText("Code đã ở mức tối ưu hợp lý")).toBeInTheDocument();
    expect(screen.queryByText("Hướng cải thiện")).toBeNull();
  });

  it("is_optimizable=true nhưng độ phức tạp sau giống trước (khác hoa thường/khoảng trắng) thì không hiện mũi tên", async () => {
    await openReview({
      ...PRIME_REVIEW,
      time_complexity: "O(n log n)",
      optimization: { ...PRIME_REVIEW.optimization, expected_time_complexity: "O(N logN)" },
    });

    expect(within(screen.getByTestId("ai-review-time")).queryByLabelText("→")).toBeNull();
  });

  it("nội dung AI hiển thị dạng text thuần, không render HTML", async () => {
    await openReview({
      ...PRIME_REVIEW,
      summary: '<img src=x onerror="alert(1)"><b>đậm</b>',
    });

    const card = screen.getByTestId("ai-review-result");
    expect(card.querySelector("img")).toBeNull();
    expect(card.querySelector("b")).toBeNull();
    expect(screen.getByText('<img src=x onerror="alert(1)"><b>đậm</b>')).toBeInTheDocument();
  });

  it("nút Đóng ẩn kết quả và quay về nút Review code", async () => {
    const { user } = await openReview();

    await user.click(screen.getByRole("button", { name: "Đóng AI review" }));

    expect(screen.queryByTestId("ai-review-result")).toBeNull();
    expect(reviewButton()).toBeEnabled();
  });

  it("Review lại gửi request mới", async () => {
    const calls = mockReview(() => HttpResponse.json(PRIME_REVIEW));
    const user = userEvent.setup();
    renderSection();
    await user.click(reviewButton());
    await screen.findByTestId("ai-review-result");

    await user.click(screen.getByRole("button", { name: /Review lại/ }));

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(await screen.findByTestId("ai-review-result")).toBeInTheDocument();
  });
});

describe("AiReviewSection — lỗi", () => {
  it.each([
    [503, "AI_BUSY", "AI đang phân tích bài khác, vui lòng thử lại sau.", true],
    [503, "AI_UNAVAILABLE", "Không thể kết nối AI Server.", true],
    [504, "AI_TIMEOUT", "AI xử lý quá thời gian cho phép.", true],
    [502, "AI_INVALID_RESPONSE", "AI trả về dữ liệu không hợp lệ.", true],
    [500, "INTERNAL", "Đã có lỗi xảy ra, vui lòng thử lại.", true],
    [409, "SUBMISSION_NOT_ACCEPTED", "Bài nộp phải pass toàn bộ testcase mới được review code.", false],
    [422, "CODE_TOO_LONG", "Mã nguồn quá dài, AI không review được.", false],
    [404, "NOT_FOUND", "Không tìm thấy bài nộp.", false],
  ])("HTTP %i %s -> thông báo đúng, có nút Thử lại = %s", async (status, code, text, retry) => {
    mockReview(() => HttpResponse.json({ error_code: code, message: "x" }, { status }));
    const user = userEvent.setup();
    renderSection();

    await user.click(reviewButton());

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Không review được");
    expect(alert).toHaveTextContent(text);
    if (retry) {
      expect(within(alert).getByRole("button", { name: /Thử lại/ })).toBeInTheDocument();
    } else {
      expect(within(alert).queryByRole("button", { name: /Thử lại/ })).toBeNull();
    }
  });

  it("mất mạng -> báo mất kết nối", async () => {
    mockReview(() => HttpResponse.error());
    const user = userEvent.setup();
    renderSection();

    await user.click(reviewButton());

    expect(await screen.findByRole("alert")).toHaveTextContent("Mất kết nối, vui lòng thử lại.");
  });

  it("Thử lại sau lỗi gọi lại API và hiện kết quả khi thành công", async () => {
    let attempt = 0;
    const calls = mockReview(() => {
      attempt += 1;
      return attempt === 1
        ? HttpResponse.json({ error_code: "AI_BUSY", message: "bận" }, { status: 503 })
        : HttpResponse.json(PRIME_REVIEW);
    });
    const user = userEvent.setup();
    renderSection();

    await user.click(reviewButton());
    const alert = await screen.findByRole("alert");
    await user.click(within(alert).getByRole("button", { name: /Thử lại/ }));

    expect(await screen.findByTestId("ai-review-result")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(calls).toHaveLength(2);
  });
});

describe("AiReviewSection — đổi bài nộp", () => {
  it("đổi sang bài nộp khác (key mới) thì kết quả cũ bị xoá", async () => {
    mockReview();
    const user = userEvent.setup();
    const { rerender } = renderWithProviders(<AiReviewSection key={7} submission={ACCEPTED} />);
    await user.click(reviewButton());
    await screen.findByTestId("ai-review-result");

    rerender(<AiReviewSection key={8} submission={{ ...ACCEPTED, id: 8 }} />);

    expect(screen.queryByTestId("ai-review-result")).toBeNull();
    expect(reviewButton()).toBeEnabled();
  });

  it("lần nộp mới chưa pass thì nút biến mất", async () => {
    mockReview();
    const { rerender } = renderWithProviders(<AiReviewSection key={7} submission={ACCEPTED} />);
    expect(reviewButton()).toBeInTheDocument();

    rerender(
      <AiReviewSection key={8} submission={{ id: 8, status: "wrong_answer", passed_count: 1, total_testcases: 3 }} />,
    );

    expect(screen.queryByRole("button", { name: /Review code/ })).toBeNull();
  });
});

describe("AiReviewSection — i18n", () => {
  function Toggle() {
    const { setLocale } = useLocale();
    return (
      <button type="button" onClick={() => setLocale("en")}>
        to-en
      </button>
    );
  }

  it("đổi sang tiếng Anh thì nhãn panel đổi theo", async () => {
    mockReview();
    const user = userEvent.setup();
    renderWithProviders(
      <LocaleProvider>
        <Toggle />
        <AiReviewSection submission={ACCEPTED} />
      </LocaleProvider>,
    );

    await user.click(screen.getByRole("button", { name: "to-en" }));
    expect(await screen.findByText("All testcases passed. Get AI feedback on performance?")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Review code/ }));
    await screen.findByTestId("ai-review-result");

    expect(screen.getByText("Time")).toBeInTheDocument();
    expect(screen.getByText("Space")).toBeInTheDocument();
    expect(screen.getByText("Inefficiencies")).toBeInTheDocument();
    expect(screen.getByText("How to improve")).toBeInTheDocument();
    expect(screen.getByText(/Does not affect your grade/)).toBeInTheDocument();
    expect(screen.queryByText("Điểm chưa tối ưu")).toBeNull();
  });
});

/* ─── Đổi ngôn ngữ: cache kết quả theo từng ngôn ngữ ─────────────────────── */

/** Mock trả nội dung khác nhau theo `locale` trong body để phân biệt kết quả. */
function mockReviewByLocale() {
  const locales: string[] = [];
  server.use(
    http.post(URL, async ({ request }) => {
      const body = (await request.json()) as { locale?: string };
      const locale = body.locale ?? "vi";
      locales.push(locale);
      return HttpResponse.json({ ...PRIME_REVIEW, summary: `summary-${locale}` });
    }),
  );
  return locales;
}

function LocaleButtons() {
  const { setLocale } = useLocale();
  return (
    <div>
      <button type="button" onClick={() => setLocale("vi")}>
        set-vi
      </button>
      <button type="button" onClick={() => setLocale("en")}>
        set-en
      </button>
    </div>
  );
}

function renderWithLocaleToggle() {
  return renderWithProviders(
    <LocaleProvider>
      <LocaleButtons />
      <AiReviewSection submission={ACCEPTED} />
    </LocaleProvider>,
  );
}

describe("AiReviewSection — ngôn ngữ của prompt", () => {
  it("lần review đầu gửi locale đang xem (vi)", async () => {
    const locales = mockReviewByLocale();
    const user = userEvent.setup();
    renderWithLocaleToggle();

    await user.click(screen.getByRole("button", { name: /Review code/ }));

    await screen.findByTestId("ai-review-result");
    expect(locales).toEqual(["vi"]);
    expect(screen.getByText("summary-vi")).toBeInTheDocument();
  });

  it("đang ở EN thì review đầu gửi locale en", async () => {
    const locales = mockReviewByLocale();
    const user = userEvent.setup();
    renderWithLocaleToggle();

    await user.click(screen.getByRole("button", { name: "set-en" }));
    await user.click(screen.getByRole("button", { name: /Review code/ }));

    await screen.findByTestId("ai-review-result");
    expect(locales).toEqual(["en"]);
    expect(screen.getByText("summary-en")).toBeInTheDocument();
  });

  it("chưa bấm review thì đổi ngôn ngữ không gọi AI", async () => {
    const locales = mockReviewByLocale();
    const user = userEvent.setup();
    renderWithLocaleToggle();

    await user.click(screen.getByRole("button", { name: "set-en" }));
    await user.click(screen.getByRole("button", { name: "set-vi" }));

    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(locales).toEqual([]);
  });

  it("đổi ngôn ngữ sau khi review thì sinh lại bằng ngôn ngữ mới", async () => {
    const locales = mockReviewByLocale();
    const user = userEvent.setup();
    renderWithLocaleToggle();

    await user.click(screen.getByRole("button", { name: /Review code/ }));
    expect(await screen.findByText("summary-vi")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "set-en" }));

    expect(await screen.findByText("summary-en")).toBeInTheDocument();
    expect(locales).toEqual(["vi", "en"]);
  });

  it("quay lại ngôn ngữ đã có kết quả thì hiện cache, không gọi lại AI", async () => {
    const locales = mockReviewByLocale();
    const user = userEvent.setup();
    renderWithLocaleToggle();

    await user.click(screen.getByRole("button", { name: /Review code/ }));
    await screen.findByText("summary-vi");

    await user.click(screen.getByRole("button", { name: "set-en" }));
    await screen.findByText("summary-en");

    await user.click(screen.getByRole("button", { name: "set-vi" }));

    // Hiện ngay kết quả cũ, không có lượt gọi mới.
    expect(screen.getByText("summary-vi")).toBeInTheDocument();
    expect(locales).toEqual(["vi", "en"]);
  });

  it("chuyển ngôn ngữ liên tục chỉ gọi AI 1 lần cho mỗi ngôn ngữ", async () => {
    const locales = mockReviewByLocale();
    const user = userEvent.setup();
    renderWithLocaleToggle();

    await user.click(screen.getByRole("button", { name: /Review code/ }));
    await screen.findByText("summary-vi");

    const toEn = screen.getByRole("button", { name: "set-en" });
    const toVi = screen.getByRole("button", { name: "set-vi" });
    await user.click(toEn);
    await user.click(toVi);
    await user.click(toEn);
    await user.click(toVi);
    await user.click(toEn);

    expect(await screen.findByText("summary-en")).toBeInTheDocument();
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(locales).toEqual(["vi", "en"]);
  });

  it("đang chạy ở ngôn ngữ mới mà quay lại ngôn ngữ cũ thì hiện kết quả cũ ngay", async () => {
    const locales: string[] = [];
    let releaseEn: (() => void) | undefined;
    server.use(
      http.post(URL, async ({ request }) => {
        const body = (await request.json()) as { locale?: string };
        const locale = body.locale ?? "vi";
        locales.push(locale);
        if (locale === "en") {
          await new Promise<void>((resolve) => {
            releaseEn = resolve;
          });
        }
        return HttpResponse.json({ ...PRIME_REVIEW, summary: `summary-${locale}` });
      }),
    );
    const user = userEvent.setup();
    renderWithLocaleToggle();

    await user.click(screen.getByRole("button", { name: /Review code/ }));
    await screen.findByText("summary-vi");

    await user.click(screen.getByRole("button", { name: "set-en" }));
    // Đang chờ bản EN: panel hiện skeleton.
    expect(await screen.findByTestId("ai-review-loading")).toBeInTheDocument();

    // Quay lại VI: hiện ngay kết quả đã lưu, không phải chờ bản EN.
    await user.click(screen.getByRole("button", { name: "set-vi" }));
    expect(screen.getByText("summary-vi")).toBeInTheDocument();
    expect(screen.queryByTestId("ai-review-loading")).toBeNull();

    // Bản EN xong thì chuyển sang EN cũng hiện ngay.
    await act(async () => {
      releaseEn?.();
    });
    await user.click(screen.getByRole("button", { name: "set-en" }));
    expect(await screen.findByText("summary-en")).toBeInTheDocument();
    expect(locales).toEqual(["vi", "en"]);
  });

  it("lỗi được giữ theo ngôn ngữ: quay lại ngôn ngữ lỗi không tự gọi lại", async () => {
    const locales: string[] = [];
    server.use(
      http.post(URL, async ({ request }) => {
        const body = (await request.json()) as { locale?: string };
        const locale = body.locale ?? "vi";
        locales.push(locale);
        return locale === "en"
          ? HttpResponse.json({ error_code: "AI_BUSY", message: "bận" }, { status: 503 })
          : HttpResponse.json({ ...PRIME_REVIEW, summary: "summary-vi" });
      }),
    );
    const user = userEvent.setup();
    renderWithLocaleToggle();

    await user.click(screen.getByRole("button", { name: /Review code/ }));
    await screen.findByText("summary-vi");

    await user.click(screen.getByRole("button", { name: "set-en" }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "set-vi" }));
    expect(screen.getByText("summary-vi")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "set-en" }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(locales).toEqual(["vi", "en"]);
  });

  it("đóng panel rồi đổi ngôn ngữ thì không bật lại kết quả cũ", async () => {
    const locales = mockReviewByLocale();
    const user = userEvent.setup();
    renderWithLocaleToggle();

    await user.click(screen.getByRole("button", { name: /Review code/ }));
    await screen.findByText("summary-vi");

    await user.click(screen.getByRole("button", { name: "Đóng AI review" }));
    expect(screen.queryByTestId("ai-review-result")).toBeNull();

    await user.click(screen.getByRole("button", { name: "set-en" }));
    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(screen.queryByTestId("ai-review-result")).toBeNull();
    expect(locales).toEqual(["vi"]);
  });
});
