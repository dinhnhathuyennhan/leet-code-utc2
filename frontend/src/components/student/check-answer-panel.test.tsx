/**
 * Unit tests cho CheckAnswerPanel — kết quả của nút "Kiểm tra đáp án".
 *
 * "Kiểm tra đáp án" gọi `POST .../run`: chạy code với testcase MẪU, không tạo
 * bài nộp và không ảnh hưởng điểm. Panel hiển thị số testcase đạt và chi tiết
 * từng testcase (input, output mong đợi, output thực tế, lỗi runtime).
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { CheckAnswerPanel } from "./check-answer-panel";
import type { RunCodeResponse } from "@/lib/api/endpoints/submissions";

const baseResult: RunCodeResponse = {
  status: "accepted",
  compile_output: null,
  cases: [
    {
      index: 0,
      status: "accepted",
      input: "1 2",
      expected_output: "3",
      actual_output: "3",
      stderr: null,
      time: 0.01,
    },
    {
      index: 1,
      status: "wrong_answer",
      input: "-5 5",
      expected_output: "0",
      actual_output: "-1",
      stderr: null,
      time: 0.02,
    },
  ],
};

function renderPanel(overrides: Partial<RunCodeResponse> = {}) {
  return render(<CheckAnswerPanel result={{ ...baseResult, ...overrides }} />);
}

describe("CheckAnswerPanel", () => {
  it("shows how many sample test cases passed out of the total", () => {
    renderPanel();

    expect(screen.getByText("1/2")).toBeInTheDocument();
    expect(screen.getByText("testcase mẫu đạt")).toBeInTheDocument();
  });

  it("explains that checking does not create a submission", () => {
    renderPanel();

    expect(
      screen.getByText(
        "Chạy code với các testcase mẫu của bài. Thao tác này không tạo bài nộp và không ảnh hưởng điểm.",
      ),
    ).toBeInTheDocument();
  });

  it("marks each test case as correct or incorrect", () => {
    renderPanel();

    expect(screen.getByText("Test #1")).toBeInTheDocument();
    expect(screen.getByText("Test #2")).toBeInTheDocument();
    // Nhãn nằm chung thẻ với thời gian chạy nên dùng regex.
    expect(screen.getByText(/Đúng/)).toBeInTheDocument();
    expect(screen.getByText(/wrong_answer/)).toBeInTheDocument();
  });

  it("shows the expected and the actual output of a test case", () => {
    renderPanel();

    // "3" xuất hiện 2 lần (expected + actual của test #1) nên dùng getAllByText.
    expect(screen.getAllByText("3")).toHaveLength(2);
    expect(screen.getByText("-1")).toBeInTheDocument();
  });

  it("shows the compile error when the code does not compile", () => {
    renderPanel({ status: "compile_error", compile_output: "SyntaxError: invalid syntax" });

    expect(screen.getByText("SyntaxError: invalid syntax")).toBeInTheDocument();
  });

  it("shows the runtime error of a failing test case", () => {
    renderPanel({
      cases: [
        {
          index: 0,
          status: "runtime_error",
          input: "1 2",
          expected_output: "3",
          actual_output: null,
          stderr: "ZeroDivisionError: division by zero",
          time: null,
        },
      ],
    });

    expect(screen.getByText("ZeroDivisionError: division by zero")).toBeInTheDocument();
  });
});
