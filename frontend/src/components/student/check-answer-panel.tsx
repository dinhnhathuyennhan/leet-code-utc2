"use client";

import { CheckCircle2, CircleSlash, XCircle } from "lucide-react";

import { useLocale } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { RunCodeResponse } from "@/lib/api/endpoints/submissions";

/**
 * Kết quả của nút "Kiểm tra đáp án".
 *
 * Gọi `POST .../run` — chạy code với testcase MẪU của bài, không tạo bài nộp
 * và không ảnh hưởng điểm. Hiển thị từng testcase: input, output mong đợi,
 * output thực tế và lỗi runtime nếu có.
 */
export function CheckAnswerPanel({
  result,
  className,
}: {
  result: RunCodeResponse;
  className?: string;
}) {
  const { t } = useLocale();
  const passedCount = result.cases.filter((item) => item.status === "accepted").length;
  const allPassed = passedCount === result.cases.length;
  const compileError = result.compile_output?.trim();

  return (
    <div className={cn("space-y-4", className)} data-testid="check-answer-panel">
      {/* ─── Tóm tắt ────────────────────────────────────────────────────── */}
      <div
        className={cn(
          "rounded-2xl border p-5",
          compileError
            ? "border-red-200 bg-red-50/70 dark:border-red-500/30 dark:bg-red-500/10"
            : allPassed
              ? "border-emerald-200 bg-emerald-50/70 dark:border-emerald-500/30 dark:bg-emerald-500/10"
              : "border-amber-200 bg-amber-50/70 dark:border-amber-500/30 dark:bg-amber-500/10",
        )}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t("student.assignment.checkTitle")}
            </p>
            <p className="text-sm text-muted-foreground">{t("student.assignment.checkDesc")}</p>
          </div>
          <p className="text-lg font-bold tabular-nums text-slate-900 dark:text-slate-100">
            {passedCount}/{result.cases.length}{" "}
            <span className="text-sm font-medium text-muted-foreground">
              {t("student.assignment.checkPassed")}
            </span>
          </p>
        </div>
      </div>

      {/* ─── Output lỗi biên dịch ───────────────────────────────────────── */}
      {compileError && (
        <div className="rounded-2xl border border-red-200 bg-slate-950 dark:border-red-500/30">
          <div className="flex items-center gap-2 border-b border-white/10 px-4 py-2.5 text-xs font-semibold text-slate-300">
            <CircleSlash className="size-3.5 text-red-400" />
            {t("result.errorTitle")}
          </div>
          <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap text-red-200">
            {compileError}
          </pre>
        </div>
      )}

      {/* ─── Chi tiết từng testcase ────────────────────────────────────── */}
      <div className="space-y-3">
        {result.cases.map((item) => {
          const passed = item.status === "accepted";
          return (
            <details
              key={item.index}
              className={cn(
                "rounded-2xl border bg-card p-4",
                !passed && "border-red-200 dark:border-red-500/30",
              )}
              data-testid={`check-answer-case-${item.index}`}
            >
              <summary className="flex cursor-pointer items-center justify-between gap-3 text-sm font-medium">
                <span className="inline-flex items-center gap-2">
                  {passed ? (
                    <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <XCircle className="size-4 text-red-600 dark:text-red-400" />
                  )}
                  Test #{item.index + 1}
                </span>
                <span className="text-xs text-muted-foreground">
                  {passed ? t("result.correct") : item.status}
                  {item.time != null ? ` · ${item.time}s` : ""}
                </span>
              </summary>

              <div className="mt-3 grid gap-3 text-xs sm:grid-cols-3">
                <div>
                  <p className="mb-1 font-semibold text-muted-foreground">{t("student.assignment.sampleInput")}</p>
                  <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-muted p-3 font-mono">
                    {formatValue(item.input)}
                  </pre>
                </div>
                <div>
                  <p className="mb-1 font-semibold text-muted-foreground">{t("student.assignment.sampleOutput")}</p>
                  <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-muted p-3 font-mono">
                    {formatValue(item.expected_output)}
                  </pre>
                </div>
                <div>
                  <p className="mb-1 font-semibold text-muted-foreground">{t("student.assignment.actualOutput")}</p>
                  <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-muted p-3 font-mono">
                    {formatValue(item.actual_output)}
                  </pre>
                </div>
              </div>

              {item.stderr && (
                <pre className="mt-3 overflow-auto whitespace-pre-wrap rounded bg-red-50 p-3 font-mono text-xs text-red-700 dark:bg-red-500/10 dark:text-red-300">
                  {item.stderr}
                </pre>
              )}
            </details>
          );
        })}
      </div>
    </div>
  );
}

/** Testcase value có thể là chuỗi, số hoặc object — hiển thị cho dễ đọc. */
function formatValue(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}
