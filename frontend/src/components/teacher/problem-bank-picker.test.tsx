/**
 * Component test cho bộ chọn bài khi tạo/sửa buổi học: gửi đúng bộ lọc lên
 * `GET /problems`, tải thêm trang kế tiếp, chọn/bỏ chọn bài, khoá bài không chọn được.
 */
import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { ProblemBankPicker } from "./problem-bank-picker";
import { server } from "@/test/mocks/server";
import { renderWithProviders } from "@/test/utils/render";
import type { ProblemListItem } from "@/lib/api/endpoints/problems";

const PROBLEMS_URL = "http://localhost:8000/problems";

function item(id: number, overrides: Partial<ProblemListItem> = {}): ProblemListItem {
  return { id, code: `BT-${id}`, title: `Bank ${id}`, level: "easy", lesson_id: null, total_number_testcase: 10, grading_mode: "harness", ...overrides };
}

function mockProblems(requests: URLSearchParams[], courseItems: ProblemListItem[] = [item(50, { title: "Course Sum", code: "C-01", lesson_id: 1 })]) {
  server.use(
    http.get(PROBLEMS_URL, ({ request }) => {
      const params = new URL(request.url).searchParams;
      requests.push(params);
      const page = Number(params.get("page"));
      if (params.get("course_id")) {
        return HttpResponse.json({ items: courseItems, total: courseItems.length, page, page_size: 20 });
      }
      const items = page === 1 ? [item(2), item(1)] : [item(3, { title: "Bank page two", grading_mode: "stdin_stdout", level: "hard" })];
      return HttpResponse.json({ items, total: 3, page, page_size: 2 });
    }),
  );
}

async function choose(label: string, option: string) {
  await userEvent.click(screen.getByRole("combobox", { name: label }));
  await userEvent.click(await screen.findByRole("option", { name: new RegExp(option) }));
}

describe("ProblemBankPicker", () => {
  it("requests bank problems with testcases and loads the next page", async () => {
    const requests: URLSearchParams[] = [];
    mockProblems(requests);
    renderWithProviders(
      <ProblemBankPicker courseId="CS101" enabled selected={[]} onToggle={vi.fn()} deadlineLabel="2026-12-01" lessonLabel={(id) => (id === 1 ? "Buổi 1" : undefined)} />,
    );

    expect(await screen.findByText("Bank 2")).toBeInTheDocument();
    expect(screen.getByText("Course Sum")).toBeInTheDocument();
    expect(screen.getByText("Buổi 1")).toBeInTheDocument();

    const bankRequest = requests.find((params) => params.get("bank_only") === "true");
    expect(bankRequest?.get("has_testcases")).toBe("true");
    expect(bankRequest?.get("page")).toBe("1");

    await userEvent.click(screen.getByRole("button", { name: "Xem thêm" }));
    expect(await screen.findByText("Bank page two")).toBeInTheDocument();
    expect(screen.getByText("stdin/stdout", { selector: "span.rounded" })).toBeInTheDocument();
    expect(requests.some((params) => params.get("bank_only") === "true" && params.get("page") === "2")).toBe(true);
    expect(screen.queryByRole("button", { name: "Xem thêm" })).not.toBeInTheDocument();
  });

  it("sends search, level and grading mode filters to the API", async () => {
    const requests: URLSearchParams[] = [];
    mockProblems(requests);
    renderWithProviders(<ProblemBankPicker courseId="CS101" enabled selected={[]} onToggle={vi.fn()} />);
    await screen.findByText("Bank 2");

    await userEvent.type(screen.getByLabelText("Tìm bài tập"), "BT-1");
    await choose("Lọc mức độ", "Khó");
    await choose("Lọc cách chấm", "stdin/stdout");

    await waitFor(() => {
      const last = requests.filter((params) => params.get("bank_only") === "true").at(-1);
      expect(last?.get("q")).toBe("BT-1");
      expect(last?.get("level")).toBe("hard");
      expect(last?.get("grading_mode")).toBe("stdin_stdout");
    });
    const courseRequest = requests.filter((params) => params.get("course_id") === "CS101").at(-1);
    expect(courseRequest?.get("q")).toBe("BT-1");
  });

  it("toggles a problem and shows selected chips that can be removed", async () => {
    const requests: URLSearchParams[] = [];
    mockProblems(requests);
    const onToggle = vi.fn();
    renderWithProviders(
      <ProblemBankPicker courseId="CS101" enabled selected={[{ id: 99, title: "Đã chọn trước", code: null }]} onToggle={onToggle} />,
    );

    await userEvent.click(await screen.findByText("Bank 2"));
    expect(onToggle).toHaveBeenCalledWith({ id: 2, title: "Bank 2", code: "BT-2" });

    await userEvent.click(screen.getByRole("button", { name: "Bỏ chọn Đã chọn trước" }));
    expect(onToggle).toHaveBeenCalledWith({ id: 99, title: "Đã chọn trước", code: null });
  });

  it("disables problems without testcases or rejected by disabledReason", async () => {
    const requests: URLSearchParams[] = [];
    mockProblems(requests, [
      item(60, { title: "No tests", lesson_id: 1, total_number_testcase: 0 }),
      item(61, { title: "Current lesson", lesson_id: 7 }),
    ]);
    const onToggle = vi.fn();
    renderWithProviders(
      <ProblemBankPicker
        courseId="CS101"
        enabled
        selected={[]}
        onToggle={onToggle}
        disabledReason={(problem) => (problem.lesson_id === 7 ? "Đang dùng trong buổi này" : null)}
      />,
    );

    expect(await screen.findByText("Chưa có testcase", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("Đang dùng trong buổi này", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("No tests").closest("button")).toBeDisabled();
    expect(screen.getByText("Current lesson").closest("button")).toBeDisabled();
    expect(screen.getByText("Bank 2").closest("button")).toBeEnabled();
  });
});
