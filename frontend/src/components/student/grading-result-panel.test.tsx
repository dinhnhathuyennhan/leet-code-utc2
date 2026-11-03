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

  it("marks passed testcases as correct and the rest as wrong", () => {
    renderPanel({
      passed_count: 1,
      total_testcases: 3,
      testcases: [
        { id: 1, input: "1 2", expected_output: "3", is_sample: true },
        { id: 2, input: "-5 5", expected_output: "0", is_sample: false },
        { id: 3, input: "1 1", expected_output: "2", is_sample: false },
      ],
    });

    expect(screen.getAllByText("Đúng")).toHaveLength(1);
    expect(screen.getAllByText("Sai")).toHaveLength(2);
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
