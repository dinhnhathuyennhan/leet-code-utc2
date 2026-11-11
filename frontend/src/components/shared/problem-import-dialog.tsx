"use client";

import { useRef, useState } from "react";
import { Download, FileUp, LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  importProblems,
  previewProblemImport,
  type ProblemImportPreviewResponse,
  type ProblemImportResponse,
} from "@/lib/api/endpoints/problems";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { ApiError } from "@/lib/api/error";

const MAX_FILE_BYTES = 25 * 1024 * 1024;
const TEMPLATE = {
  problems: [
    {
      title: "Sum Two Numbers",
      report: "EXAMPLE-001",
      function_name: "sumTwoNumbers",
      description: "Write a function that returns the sum of two integers.",
      constraints: "-1000 <= a, b <= 1000",
      level: "easy",
      time_limit_seconds: 2,
      starter_codes: {
        python:
          "class Solution:\n    def sumTwoNumbers(self, a: int, b: int) -> int:\n        pass",
        c: "int sumTwoNumbers(int a, int b) { return a + b; }",
        cpp: "class Solution { public: int sumTwoNumbers(int a, int b) { return a + b; } };",
        javascript: "function sumTwoNumbers(a, b) { return a + b; }",
      },
      start_datetime: "2026-01-01T00:00:00+07:00",
      end_datetime: "2099-12-31T23:59:00+07:00",
      hint: null,
      complexity: "O(1)",
      testcases: [
        { input: [2, 3], expected_output: 5, is_sample: true },
        { input: [-1, 5], expected_output: 4, is_sample: true },
        { input: [0, 0], expected_output: 0, is_sample: true },
        { input: [1000, -1000], expected_output: 0, is_sample: false },
        { input: [999, 1], expected_output: 1000, is_sample: false },
        { input: [-1000, -1000], expected_output: -2000, is_sample: false },
        { input: [123, -23], expected_output: 100, is_sample: false },
        { input: [42, 58], expected_output: 100, is_sample: false },
        { input: [500, 500], expected_output: 1000, is_sample: false },
        { input: [-999, 999], expected_output: 0, is_sample: false },
      ],
    },
    {
      title: "Sum Two Numbers (stdin/stdout)",
      report: "EXAMPLE-STDIO-001",
      function_name: null,
      description:
        "Read two integers from stdin and print their sum to stdout.",
      constraints: "-1000 <= a, b <= 1000",
      level: "easy",
      time_limit_seconds: 2,
      starter_codes: {
        python: "a, b = map(int, input().split())\nprint(a + b)",
        c: '#include <stdio.h>\nint main(void) { int a, b; if (scanf("%d %d", &a, &b) != 2) return 0; printf("%d\\n", a + b); return 0; }',
        cpp: "#include <iostream>\nint main() { int a, b; std::cin >> a >> b; std::cout << a + b << '\\n'; }",
        java: "import java.util.Scanner;\nclass Main { public static void main(String[] args) { Scanner s = new Scanner(System.in); System.out.println(s.nextInt() + s.nextInt()); } }",
        javascript:
          "const fs = require('fs');\nconst [a, b] = fs.readFileSync(0, 'utf8').trim().split(/\\s+/).map(Number);\nconsole.log(a + b);",
      },
      start_datetime: "2026-01-01T00:00:00+07:00",
      end_datetime: "2099-12-31T23:59:00+07:00",
      hint: null,
      complexity: "O(1)",
      testcases: [
        { input: "2 3\n", expected_output: "5\n", is_sample: true },
        { input: "-1 5\n", expected_output: "4\n", is_sample: true },
        { input: "0 0\n", expected_output: "0\n", is_sample: true },
        { input: "1000 -1000\n", expected_output: "0\n", is_sample: false },
        { input: "999 1\n", expected_output: "1000\n", is_sample: false },
        {
          input: "-1000 -1000\n",
          expected_output: "-2000\n",
          is_sample: false,
        },
        { input: "123 -23\n", expected_output: "100\n", is_sample: false },
        { input: "42 58\n", expected_output: "100\n", is_sample: false },
        { input: "500 500\n", expected_output: "1000\n", is_sample: false },
        { input: "-999 999\n", expected_output: "0\n", is_sample: false },
      ],
    },
  ],
};

function downloadTemplate() {
  const blob = new Blob([JSON.stringify(TEMPLATE, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "problem-import-template.json";
  link.click();
  URL.revokeObjectURL(url);
}

export function ProblemImportDialog({
  open,
  onClose,
  onImported,
  onImportOutcomeUncertain,
}: {
  open: boolean;
  onClose: () => void;
  onImported: (result: ProblemImportResponse) => void;
  onImportOutcomeUncertain: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<ProblemImportPreviewResponse | null>(
    null,
  );

  function close() {
    if (busy) return;
    setFile(null);
    setError("");
    setPreview(null);
    if (inputRef.current) inputRef.current.value = "";
    onClose();
  }

  async function previewFile() {
    if (!file || busy) return;
    if (!file.name.toLowerCase().endsWith(".json")) {
      setError("Chọn file có định dạng .json.");
      return;
    }
    if (file.size > MAX_FILE_BYTES) {
      setError("File import không được vượt quá 25 MB.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      setPreview(await previewProblemImport(file));
    } catch (requestError) {
      setError(
        requestError instanceof ApiError && requestError.isNetworkError
          ? "Máy chủ chưa phản hồi kịp khi kiểm tra file. Chưa có bài nào được import; bạn có thể kiểm tra lại."
          : getErrorMessage(requestError),
      );
    } finally {
      setBusy(false);
    }
  }

  async function submit() {
    if (!file || !preview?.valid || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await importProblems(file);
      onImported(result);
      setFile(null);
      setPreview(null);
      if (inputRef.current) inputRef.current.value = "";
      onClose();
    } catch (requestError) {
      const outcomeMayBeUnknown =
        requestError instanceof ApiError &&
        (requestError.isNetworkError || requestError.status >= 500);
      if (outcomeMayBeUnknown) {
        setFile(null);
        setError("");
        setPreview(null);
        if (inputRef.current) inputRef.current.value = "";
        onClose();
        onImportOutcomeUncertain();
        return;
      }
      setError(getErrorMessage(requestError));
      setPreview(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) close();
      }}
    >
      <DialogContent showCloseButton={!busy} className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Import problem từ JSON</DialogTitle>
          <DialogDescription>
            File phải theo cấu trúc problem của hệ thống. Toàn bộ file sẽ được
            kiểm tra trước khi tạo bài.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="rounded-lg bg-muted/60 p-3 text-sm">
            <p className="font-medium">Cấu trúc file</p>
            <p className="mt-1 text-muted-foreground">
              Một problem, mảng problem hoặc object có field{" "}
              <code>problems</code>. Có thể chấm theo <code>function_name</code>{" "}
              với input mảng/output JSON, hoặc stdin/stdout với input và output
              chuỗi (bỏ hoặc đặt <code>function_name: null</code>). Mỗi bài cần{" "}
              <strong>10–50 testcase</strong>, gồm ít nhất{" "}
              <strong>3 sample</strong> và <strong>5 hidden</strong>. Bài có{" "}
              <code>function_name</code> bắt buộc starter <code>python</code> và{" "}
              <code>javascript</code>; <code>c</code>/<code>cpp</code> tùy chọn
              (không dựng được harness sẽ bị bỏ). Bài stdin/stdout không bắt
              buộc starter. File mẫu có ví dụ cho cả hai kiểu.
            </p>
            <Button
              type="button"
              variant="link"
              className="mt-2 h-auto p-0"
              onClick={downloadTemplate}
            >
              <Download className="size-4" /> Tải file mẫu
            </Button>
          </div>
          <label className="block space-y-2 text-sm font-medium">
            Chọn file JSON
            <input
              ref={inputRef}
              type="file"
              accept=".json,application/json"
              disabled={busy}
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setError("");
                setPreview(null);
              }}
              className="block w-full rounded-lg border bg-background p-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-muted file:px-3 file:py-1.5"
            />
          </label>
          {file && (
            <p className="text-xs text-muted-foreground">
              {file.name} · {(file.size / (1024 * 1024)).toFixed(2)} MB
            </p>
          )}
          {preview && (
            <section
              className={`space-y-2 rounded-lg border p-3 text-sm ${preview.valid ? "border-green-300 bg-green-50 text-green-900" : "border-amber-300 bg-amber-50 text-amber-950"}`}
            >
              <p className="font-semibold">
                {preview.valid ? "Kiểm tra hợp lệ" : "File cần chỉnh sửa"}
              </p>
              <p>
                {preview.ready_problem_count}/{preview.problem_count} problem
                hợp lệ · {preview.testcase_count} testcase ·{" "}
                {preview.sample_testcase_count} mẫu ·{" "}
                {preview.hidden_testcase_count} hidden
              </p>
              {!!preview.issues.length && (
                <ul className="max-h-40 list-disc space-y-1 overflow-y-auto pl-5">
                  {preview.issues.map((item, index) => (
                    <li key={`${item.index ?? "file"}-${index}`}>
                      {item.message}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}
          {error && (
            <p
              role="alert"
              className="rounded-lg bg-red-50 p-3 text-sm text-red-700"
            >
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={busy}
              onClick={close}
            >
              Hủy
            </Button>
            {!preview?.valid ? (
              <Button
                type="button"
                disabled={!file || busy}
                onClick={() => void previewFile()}
              >
                {busy ? (
                  <LoaderCircle className="size-4 animate-spin" />
                ) : (
                  <FileUp className="size-4" />
                )}
                {busy ? "Đang kiểm tra..." : "Kiểm tra file"}
              </Button>
            ) : (
              <Button
                type="button"
                disabled={busy}
                onClick={() => void submit()}
              >
                {busy ? (
                  <LoaderCircle className="size-4 animate-spin" />
                ) : (
                  <FileUp className="size-4" />
                )}
                {busy
                  ? "Đang import..."
                  : `Import ${preview.problem_count} problem`}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
