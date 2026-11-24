/**
 * Unit tests cho GradingResultPanel — phần hiển thị kết quả chấm bài cho sinh viên.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { GradingResultPanel } from "./grading-result-panel";
import type { StudentSubmissionDetail } from "@/lib/types/submission";

const baseSubmission: StudentSubmissionDetail = {
  id: 1,
  problem_id: 10,
  problem_code: "ARR_01",
  problem_title: "Tổng hai số",
  course_id: "CS101",
  course_name: "Lập trình cơ bản",
  lesson_id: 3,
  session_label: "Buổi 1: Nhập môn và biến",
  language: "python",
  submitted_code: "print(3)",
  status: "accepted",
  compile_output: null,
  feedback: null,
  passed_count: 2,
  total_testcases: 2,
  submitted_datetime: "2026-10-20T10:30:00+07:00",
  testcases: [
    { id: 1, input: "1 2", expected_output: "3", is_sample: true },
    { id: 2, input: "-5 5", expected_output: "0", is_sample: false },
  ],
};

function renderPanel(overrides: Partial<StudentSubmissionDetail> = {}) {
  return render(<GradingResultPanel submission={{ ...baseSubmission, ...overrides }} />);
}

describe("GradingResultPanel", () => {
  it("shows the accepted verdict and the score out of 10", () => {
    renderPanel();

    expect(screen.getByText("Đạt")).toBeInTheDocument();
    expect(screen.getByText("10.0")).toBeInTheDocument();
    expect(screen.getByText("/10")).toBeInTheDocument();
  });

  it("computes a partial score from passed/total testcases", () => {
    renderPanel({ status: "wrong_answer", passed_count: 1, total_testcases: 3 });

    expect(screen.getByText("Sai kết quả")).toBeInTheDocument();
    expect(screen.getByText("3.3")).toBeInTheDocument();
  });

  it("shows how many testcases passed", () => {
    renderPanel({ passed_count: 1, total_testcases: 3 });

    expect(screen.getByText(/Đạt 1\/3 test/)).toBeInTheDocument();
  });

  it("shows the real per-testcase verdict, not the first N as passed", () => {
    // Test #1 sai nhưng test #3 đúng: không được suy ra từ passed_count theo thứ tự
    renderPanel({
      status: "wrong_answer",
      passed_count: 1,
      total_testcases: 3,
      testcase_results: [
        { index: 1, is_sample: true, status: "wrong_answer", time: 0.1 },
        { index: 2, is_sample: false, status: "runtime_error", time: 0.1 },
        { index: 3, is_sample: false, status: "accepted", time: 0.1 },
      ],
    });

    const items = screen.getAllByText(/^Test #\d/).map((node) => node.closest("div")?.textContent ?? "");
    expect(items[0]).toContain("Sai kết quả");
    expect(items[1]).toContain("Lỗi khi chạy");
    expect(items[2]).toContain("Đúng");
  });

  it("labels skipped testcases and explains early stop", () => {
    renderPanel({
      status: "time_limit_exceeded",
      passed_count: 0,
      total_testcases: 2,
      testcase_results: [
        { index: 1, is_sample: true, status: "time_limit_exceeded", time: null },
        { index: 2, is_sample: false, status: "skipped", time: null },
      ],
    });

    expect(screen.getByText("Bỏ qua")).toBeInTheDocument();
    expect(screen.getByText(/dừng chấm sớm/)).toBeInTheDocument();
  });

  it("hides the per-testcase table for old submissions without results", () => {
    renderPanel({ testcase_results: [] });

    expect(screen.queryByText("Chi tiết từng test case")).not.toBeInTheDocument();
  });

  it("renders the compile error output when present", () => {
    renderPanel({
      status: "compile_error",
      passed_count: 0,
      compile_output: "Main.java:3: error: ';' expected",
    });

    expect(screen.getByText("Lỗi biên dịch")).toBeInTheDocument();
    expect(screen.getByText(/Main\.java:3: error/)).toBeInTheDocument();
  });

  it("renders the teacher feedback when present", () => {
    renderPanel({ feedback: "Bạn cần xử lý trường hợp âm." });

    expect(screen.getByText("Nhận xét của giảng viên")).toBeInTheDocument();
    expect(screen.getByText("Bạn cần xử lý trường hợp âm.")).toBeInTheDocument();
  });

  it("hides the score when there are no testcases", () => {
    renderPanel({ total_testcases: 0, passed_count: 0, testcases: [] });

    expect(screen.queryByText("/10")).toBeNull();
  });

  it("shows the submission time and language", () => {
    renderPanel();

    expect(screen.getByText(/Nộp lúc/)).toBeInTheDocument();
    expect(screen.getByText(/Ngôn ngữ python/)).toBeInTheDocument();
  });
});
