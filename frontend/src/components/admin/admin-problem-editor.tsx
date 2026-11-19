"use client";

import { useState } from "react";
import { Plus, Save, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/lib/helpers/error-message";
import type { AdminProblem, AdminProblemPayload } from "@/lib/types/admin";
import { ADMIN_PRIMARY, ADMIN_SELECT } from "./admin-ui";

const FUNCTION_LANGUAGES = ["python", "c", "cpp", "javascript"] as const;
const STDIO_LANGUAGES = ["python", "c", "cpp", "java", "javascript"] as const;
function dateTimeInput(value: string) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Ho_Chi_Minh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date(value));
  const p = Object.fromEntries(parts.map((item) => [item.type, item.value]));
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}`;
}
const withVietnamOffset = (value: string) =>
  `${value.length === 16 ? `${value}:00` : value}+07:00`;
const encodeJson = (value: unknown) => JSON.stringify(value, null, 2) ?? "null";
const draftTests = (problem?: AdminProblem) => {
  const functionMode = problem?.function_name != null;
  return (
    problem?.testcases.map((test) => ({
      input: functionMode ? encodeJson(test.input) : String(test.input ?? ""),
      expected: functionMode
        ? encodeJson(test.expected_output)
        : String(test.expected_output ?? ""),
      sample: test.is_sample,
    })) ?? [{ input: "[]", expected: "null", sample: true }]
  );
};

export function AdminProblemEditor({
  problem,
  onSave,
  onBusyChange,
  uploadTestcases,
  hideTestcases = false,
}: {
  problem?: AdminProblem;
  onSave: (data: AdminProblemPayload) => Promise<unknown>;
  onBusyChange?: (busy: boolean) => void;
  uploadTestcases?: (file: File) => Promise<AdminProblem>;
  hideTestcases?: boolean;
}) {
  const [title, setTitle] = useState(problem?.title ?? "");
  const [report, setReport] = useState(problem?.code ?? "");
  const [functionName, setFunctionName] = useState(
    problem?.function_name ?? "",
  );
  const [functionMode, setFunctionMode] = useState(
    problem ? problem.function_name !== null : true,
  );
  const [description, setDescription] = useState(problem?.description ?? "");
  const [constraints, setConstraints] = useState(problem?.constraints ?? "");
  const [level, setLevel] = useState<AdminProblemPayload["level"]>(
    (problem?.level as AdminProblemPayload["level"]) ?? "easy",
  );
  const [timeLimit, setTimeLimit] = useState(problem?.time_limit_seconds ?? 1);
  const [start, setStart] = useState(
    problem ? dateTimeInput(problem.start_datetime) : "",
  );
  const [end, setEnd] = useState(
    problem ? dateTimeInput(problem.end_datetime) : "",
  );
  const [hint, setHint] = useState(problem?.hint ?? "");
  const [complexity, setComplexity] = useState(problem?.complexity ?? "");
  const [codes, setCodes] = useState<Record<string, string>>({
    python: problem?.starter_code ?? "",
    c: "",
    cpp: "",
    java: "",
    javascript: "",
    ...problem?.starter_codes,
  });
  const [language, setLanguage] = useState<string>("python");
  const [tests, setTests] = useState(() => draftTests(problem));
  const [busy, setBusy] = useState(false);
  const languages = functionMode ? FUNCTION_LANGUAGES : STDIO_LANGUAGES;

  function markBusy(next: boolean) {
    setBusy(next);
    onBusyChange?.(next);
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    if (
      !title.trim() ||
      (functionMode && !/^[A-Za-z_][A-Za-z0-9_]*$/.test(functionName.trim()))
    ) {
      toast.error(
        "Nhập tên bài và tên hàm hợp lệ (chữ ASCII, số, dấu gạch dưới).",
      );
      return;
    }
    if (!start || !end || start >= end) {
      toast.error("Thời gian mở đề phải trước hạn nộp.");
      return;
    }
    const missing = functionMode
      ? (["python", "javascript"] as const).filter(
          (item) => !codes[item]?.trim(),
        )
      : [];
    if (missing.length) {
      toast.error(
        `Bài chấm theo hàm bắt buộc có mã khởi tạo: ${missing.map((item) => item.toUpperCase()).join(", ")}.`,
      );
      return;
    }
    let testcases: AdminProblemPayload["testcases"];
    try {
      testcases = tests.map((test, index) => {
        if (!functionMode) {
          return {
            input: test.input,
            expected_output: test.expected,
            is_sample: test.sample,
          };
        }
        const input: unknown = JSON.parse(test.input);
        if (!Array.isArray(input))
          throw new Error(
            `Input test #${index + 1} phải là mảng JSON các đối số.`,
          );
        return {
          input,
          expected_output: JSON.parse(test.expected) as unknown,
          is_sample: test.sample,
        };
      });
    } catch (error) {
      toast.error(
        error instanceof SyntaxError
          ? "Input/output testcase phải là JSON hợp lệ."
          : getErrorMessage(error),
      );
      return;
    }
    const sampleCount = testcases.filter((test) => test.is_sample).length;
    const hiddenCount = testcases.length - sampleCount;
    if (testcases.length < 10) {
      toast.error("Cần ít nhất 10 testcase tổng cộng.");
      return;
    }
    if (testcases.length > 50) {
      toast.error("Chỉ được có tối đa 50 testcase.");
      return;
    }
    if (sampleCount < 3) {
      toast.error("Cần ít nhất 3 testcase mẫu.");
      return;
    }
    if (hiddenCount < 5) {
      toast.error("Cần ít nhất 5 hidden testcase.");
      return;
    }
    markBusy(true);
    try {
      await onSave({
        title: title.trim(),
        report: report.trim() || null,
        ...(problem ? {} : { function_name: functionMode ? functionName.trim() : null }),
        description: description.trim(),
        constraints: constraints.trim(),
        level,
        time_limit_seconds: timeLimit,
        start_datetime: withVietnamOffset(start),
        end_datetime: withVietnamOffset(end),
        starter_codes: Object.fromEntries(
          languages
            .filter((item) => codes[item]?.trim())
            .map((item) => [item, codes[item]]),
        ),
        hint: hint.trim() || null,
        complexity: complexity.trim() || null,
        testcases,
      });
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      markBusy(false);
    }
  }
  async function upload(file: File) {
    if (!uploadTestcases || busy) return;
    if (!/\.(json|zip)$/i.test(file.name) || file.size > 5 * 1024 * 1024) {
      toast.error("Chọn file JSON/ZIP không vượt quá 5 MB.");
      return;
    }
    markBusy(true);
    try {
      const result = await uploadTestcases(file);
      if (result.testcases.length > 50) {
        toast.error(
          "File có quá 50 testcase. Hãy giảm số lượng trước khi tải lên.",
        );
        return;
      }
      setTests(draftTests(result));
      toast.success(`Đã nhập ${result.testcases.length} testcase.`);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      markBusy(false);
    }
  }
  return (
    <form onSubmit={(event) => void submit(event)} className="space-y-6">
      <fieldset disabled={busy} className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-2 text-sm font-medium">
            Tên bài tập
            <Input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              maxLength={255}
              required
            />
          </label>
          <label className="space-y-2 text-sm font-medium">
            Mã bài (tùy chọn)
            <Input
              value={report}
              onChange={(event) => setReport(event.target.value)}
              maxLength={255}
            />
          </label>
          {!hideTestcases && (
            <label className="space-y-2 text-sm font-medium">
              Kiểu chấm
              <select
                value={functionMode ? "function" : "stdio"}
                disabled={!!problem}
                onChange={(event) => {
                  const nextFunctionMode = event.target.value === "function";
                  if (
                    nextFunctionMode !== functionMode &&
                    !window.confirm(
                      "Đổi kiểu chấm sẽ xóa input/output hiện tại của các testcase. Tiếp tục?",
                    )
                  )
                    return;
                  setFunctionMode(nextFunctionMode);
                  if (nextFunctionMode && !functionName.trim())
                    setFunctionName("solve");
                  setTests((current) =>
                    current.map((test) => ({
                      ...test,
                      input: nextFunctionMode ? "[]" : "",
                      expected: nextFunctionMode ? "null" : "",
                    })),
                  );
                  setLanguage("python");
                }}
                className={`${ADMIN_SELECT} w-full`}
              >
                <option value="function">Gọi function_name</option>
                <option value="stdio">stdin / stdout</option>
              </select>
            </label>
          )}
          {functionMode && (
            <label className="space-y-2 text-sm font-medium">
              Tên hàm cần chấm
              <Input
                value={functionName}
                onChange={(event) => setFunctionName(event.target.value)}
                placeholder="solve"
                maxLength={100}
                required
                disabled={!!problem}
              />
              {problem && (
                <span className="block text-xs font-normal text-muted-foreground">
                  Không thể đổi tên hàm sau khi tạo bài.
                </span>
              )}
            </label>
          )}
          <label className="space-y-2 text-sm font-medium">
            Mức độ
            <select
              value={level}
              onChange={(event) => setLevel(event.target.value as typeof level)}
              className={`${ADMIN_SELECT} w-full`}
            >
              <option value="easy">Dễ</option>
              <option value="medium">Trung bình</option>
              <option value="hard">Khó</option>
            </select>
          </label>
          <label className="space-y-2 text-sm font-medium">
            Giới hạn thời gian (giây)
            <Input
              type="number"
              min={1}
              step={1}
              value={timeLimit}
              onChange={(event) => setTimeLimit(Number(event.target.value))}
              required
            />
          </label>
          <label className="space-y-2 text-sm font-medium">
            Mở đề (giờ Việt Nam)
            <Input
              type="datetime-local"
              step={1}
              value={start}
              onChange={(event) => setStart(event.target.value)}
              required
            />
          </label>
          <label className="space-y-2 text-sm font-medium">
            Hạn nộp (giờ Việt Nam)
            <Input
              type="datetime-local"
              step={1}
              value={end}
              min={start}
              onChange={(event) => setEnd(event.target.value)}
              required
            />
          </label>
        </div>
        <label className="block space-y-2 text-sm font-medium">
          Nội dung đề bài
          <Textarea
            rows={5}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            required
          />
        </label>
        <label className="block space-y-2 text-sm font-medium">
          Ràng buộc
          <Textarea
            rows={3}
            value={constraints}
            onChange={(event) => setConstraints(event.target.value)}
            required
          />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-2 text-sm font-medium">
            Gợi ý
            <Textarea
              value={hint}
              onChange={(event) => setHint(event.target.value)}
            />
          </label>
          <label className="space-y-2 text-sm font-medium">
            Độ phức tạp
            <Input
              value={complexity}
              onChange={(event) => setComplexity(event.target.value)}
              placeholder="O(n)"
            />
          </label>
        </div>
        <section className="space-y-3 rounded-xl border p-4">
          <h2 className="font-semibold">Mã nguồn khởi tạo</h2>
          <p className="text-xs text-muted-foreground">
            {functionMode
              ? "Bắt buộc Python và JavaScript (*). C/C++ tùy chọn, chỉ nhận khi dựng được harness; bài sẽ chỉ hỗ trợ các ngôn ngữ có mã khởi tạo hợp lệ. Java dùng stdin/stdout."
              : "Stdin/stdout hỗ trợ Python, C, C++, Java và JavaScript. Mã khởi tạo không bắt buộc."}
          </p>
          <div className="flex flex-wrap gap-2">
            {languages.map((item) => (
              <Button
                key={item}
                type="button"
                variant={language === item ? "secondary" : "outline"}
                size="sm"
                aria-pressed={language === item}
                onClick={() => setLanguage(item)}
              >
                {item.toUpperCase()}
                {functionMode && (item === "python" || item === "javascript")
                  ? " *"
                  : ""}
                {codes[item]?.trim() ? " ✓" : ""}
              </Button>
            ))}
          </div>
          <Textarea
            aria-label={`Mã khởi tạo ${language}`}
            rows={9}
            value={codes[language] ?? ""}
            onChange={(event) =>
              setCodes({ ...codes, [language]: event.target.value })
            }
            className="bg-slate-950 font-mono text-xs text-slate-100"
          />
        </section>
        {!hideTestcases && (
          <section className="space-y-4 rounded-xl border p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-semibold">Testcase ({tests.length})</h2>
              <div className="flex gap-2">
                {uploadTestcases && (
                  <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-xs">
                    <Upload className="size-4" />
                    Nhập JSON/ZIP
                    <input
                      type="file"
                      accept=".json,.zip"
                      disabled={busy}
                      className="hidden"
                      onChange={(event) => {
                        const file = event.target.files?.[0];
                        event.target.value = "";
                        if (file) void upload(file);
                      }}
                    />
                  </label>
                )}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={tests.length >= 50}
                  onClick={() =>
                    setTests([
                      ...tests,
                      { input: "[]", expected: "null", sample: false },
                    ])
                  }
                >
                  <Plus className="size-4" />
                  Thêm test
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              {functionMode
                ? "Input là mảng JSON đối số; output là giá trị JSON. "
                : "Input là chuỗi stdin; output là chuỗi stdout. "}
              Cần 10–50 testcase tổng cộng, ít nhất 3 mẫu và 5 hidden.
            </p>
            <p
              className={`text-xs font-medium ${tests.length >= 10 && tests.length <= 50 && tests.filter((test) => test.sample).length >= 3 && tests.filter((test) => !test.sample).length >= 5 ? "text-green-700" : "text-amber-700"}`}
            >
              {tests.length}/10–50 tổng cộng ·{" "}
              {tests.filter((test) => test.sample).length}/3 mẫu tối thiểu ·{" "}
              {tests.filter((test) => !test.sample).length}/5 hidden tối thiểu
            </p>
            {tests.map((test, index) => (
              <div key={index} className="space-y-3 rounded-lg bg-muted/50 p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">Test #{index + 1}</span>
                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-2 text-xs">
                      <input
                        type="checkbox"
                        checked={test.sample}
                        onChange={(event) =>
                          setTests(
                            tests.map((item, i) =>
                              i === index
                                ? { ...item, sample: event.target.checked }
                                : item,
                            ),
                          )
                        }
                      />
                      Test mẫu
                    </label>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      disabled={tests.length <= 10}
                      onClick={() =>
                        setTests(tests.filter((_, i) => i !== index))
                      }
                      aria-label={`Xóa test ${index + 1}`}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="space-y-1 text-xs font-medium">
                    {functionMode ? "Input JSON (đối số hàm)" : "stdin"}
                    <Textarea
                      rows={3}
                      value={test.input}
                      onChange={(event) =>
                        setTests(
                          tests.map((item, i) =>
                            i === index
                              ? { ...item, input: event.target.value }
                              : item,
                          ),
                        )
                      }
                      className="font-mono text-xs"
                    />
                  </label>
                  <label className="space-y-1 text-xs font-medium">
                    {functionMode ? "Output JSON" : "stdout"}
                    <Textarea
                      rows={3}
                      value={test.expected}
                      onChange={(event) =>
                        setTests(
                          tests.map((item, i) =>
                            i === index
                              ? { ...item, expected: event.target.value }
                              : item,
                          ),
                        )
                      }
                      className="font-mono text-xs"
                    />
                  </label>
                </div>
              </div>
            ))}
          </section>
        )}
      </fieldset>
      <div className="flex justify-end">
        <Button type="submit" disabled={busy} className={ADMIN_PRIMARY}>
          <Save className="size-4" />
          {busy
            ? "Đang xử lý..."
            : problem
              ? "Lưu bài tập"
              : "Tạo bài tập nguồn"}
        </Button>
      </div>
    </form>
  );
}
