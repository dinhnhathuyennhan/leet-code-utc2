import { useState } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

import { CodeEditor } from "./code-editor";

/**
 * Task 1B — FE đổi ngôn ngữ phải nạp lại mã mẫu của ngôn ngữ mới và cảnh báo
 * nếu người dùng đã tự sửa code (tránh nộp nhầm ngôn ngữ -> compile_error).
 */

const STARTER_CODES = {
  python: "def solve():\n    print('python')\n",
  cpp: "int main() { return 0; } // cpp\n",
  java: "class Main { /* java */ }\n",
};

/**
 * Harness: giữ `value` trong state để mô phỏng đúng cách component được dùng
 * thật (parent sở hữu code đang soạn).
 */
function Harness({
  starterCodes = STARTER_CODES,
  supportedLanguages,
  onLanguageChange,
}: {
  starterCodes?: Record<string, string>;
  supportedLanguages?: readonly string[];
  onLanguageChange?: (language: string) => void;
}) {
  const [language, setLanguage] = useState("python");
  const [value, setValue] = useState("");

  return (
    <CodeEditor
      value={value}
      onChange={setValue}
      language={language}
      onLanguageChange={(next) => {
        setLanguage(next);
        onLanguageChange?.(next);
      }}
      starterCodes={starterCodes}
      supportedLanguages={supportedLanguages}
    />
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

it("hiển thị đủ 5 tab ngôn ngữ được backend hỗ trợ", () => {
  render(<Harness />);

  expect(screen.getByRole("button", { name: /Python 3\.8/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /C\+\+ \(GCC 9\.2\)/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Java 13/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /C \(GCC 9\.2\)/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /JavaScript \(Node 12\)/ })).toBeInTheDocument();
});

it("chỉ hiện các ngôn ngữ được problem hỗ trợ (grading mode)", () => {
  render(<Harness supportedLanguages={["python", "java"]} />);

  expect(screen.getByRole("button", { name: /Java 13/ })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /C\+\+ \(GCC 9\.2\)/ })).not.toBeInTheDocument();
});

it("nạp mã mẫu của ngôn ngữ đang chọn vào ô soạn code", async () => {
  render(<Harness />);

  await waitFor(() => {
    expect(screen.getByLabelText("Mã nguồn bài nộp")).toHaveValue(STARTER_CODES.python);
  });
});

it("đổi ngôn ngữ thì nạp lại mã mẫu mới, không giữ code của ngôn ngữ cũ", async () => {
  const user = userEvent.setup();
  render(<Harness />);

  await waitFor(() => {
    expect(screen.getByLabelText("Mã nguồn bài nộp")).toHaveValue(STARTER_CODES.python);
  });

  await user.click(screen.getByRole("button", { name: /C\+\+ \(GCC 9\.2\)/ }));

  await waitFor(() => {
    expect(screen.getByLabelText("Mã nguồn bài nộp")).toHaveValue(STARTER_CODES.cpp);
  });
  expect(screen.getByLabelText("Mã nguồn bài nộp")).not.toHaveValue(STARTER_CODES.python);
});

it("hiện cảnh báo khi người dùng đã sửa code rồi mới đổi ngôn ngữ", async () => {
  const user = userEvent.setup();
  render(<Harness />);

  const textarea = screen.getByLabelText("Mã nguồn bài nộp");
  await user.clear(textarea);
  await user.type(textarea, "print('cua toi')");
  expect(textarea).toHaveValue("print('cua toi')");

  await user.click(screen.getByRole("button", { name: /Java 13/ }));

  expect(await screen.findByRole("status")).toHaveTextContent(/Đã đổi sang .*Java 13/);
});

it("không hiện cảnh báo nếu người dùng chưa sửa code", async () => {
  const user = userEvent.setup();
  render(<Harness />);

  await user.click(screen.getByRole("button", { name: /Java 13/ }));

  await waitFor(() => {
    expect(screen.getByLabelText("Mã nguồn bài nộp")).toHaveValue(STARTER_CODES.java);
  });
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
});
