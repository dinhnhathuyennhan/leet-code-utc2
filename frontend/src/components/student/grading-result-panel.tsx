"use client";

import { CheckCircle2, CircleSlash, Clock, Gauge, XCircle } from "lucide-react";

import { SubmissionStatusBadge } from "@/components/student/submission-status-badge";
import { scoreOutOfTen, submissionStatusMeta } from "@/lib/helpers/submission-status";
import { formatDate } from "@/lib/helpers/datetime";
import { useLocale } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { GradingResultView } from "@/lib/types/submission";

/**
 * Hiển thị kết quả chấm của một bài nộp.
 *
 * Gồm 3 phần:
 *  1. Tóm tắt: trạng thái, điểm thang 10, số testcase đạt, thời gian nộp.
 *  2. Output lỗi (biên dịch / runtime) nếu có.
 *  3. Bảng từng testcase: testcase đầu `passed_count` là đạt, phần còn lại sai.
 *
 * Chấp nhận cả bản rút gọn (`SubmissionResult`, dùng khi poll) lẫn bản đầy đủ
 * (`StudentSubmissionDetail`, dùng khi mở trang chi tiết bài nộp).
 */
export function GradingResultPanel({
  submission,
  className,
}: {
  submission: GradingResultView;
  className?: string;
}) {
  const meta = submissionStatusMeta(submission.status);
  const score = scoreOutOfTen(submission.passed_count, submission.total_testcases);
  const errorOutput = submission.compile_output?.trim();
  const { t } = useLocale();
  const testcases = submission.testcases ?? [];

  return (
    <div className={cn("space-y-4", className)}>
      {/* ─── Tóm tắt kết quả ───────────────────────────────────────────── */}
      <div
        className={cn(
          "rounded-2xl border p-5",
          meta.icon === "check"
            ? "border-emerald-200 bg-emerald-50/70 dark:border-emerald-500/30 dark:bg-emerald-500/10"
            : meta.icon === "x"
              ? "border-red-200 bg-red-50/70 dark:border-red-500/30 dark:bg-red-500/10"
              : "border-amber-200 bg-amber-50/70 dark:border-amber-500/30 dark:bg-amber-500/10",
        )}
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1.5">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t("result.heading")}
            </p>
            <SubmissionStatusBadge status={submission.status} />
            <p className="text-sm text-muted-foreground">
              {submission.problem_code ?? `${t("history.problemFallback")} ${submission.problem_id ?? ""}`}
              {submission.problem_title ? ` · ${submission.problem_title}` : ""}
            </p>
          </div>

          {score !== null && (
            <div className="text-right">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {t("result.score")}
              </p>
              <p className="text-3xl font-bold tabular-nums text-slate-900 dark:text-slate-100">
                {score.toFixed(1)}
                <span className="text-base font-medium text-muted-foreground">/10</span>
              </p>
            </div>
          )}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <CheckCircle2 className="size-3.5" />
            {t("result.passed")} {submission.passed_count}/{submission.total_testcases} {t("history.testSuffix")}
          </span>
          {submission.submitted_datetime && (
            <span className="inline-flex items-center gap-1.5">
              <Clock className="size-3.5" />
              {t("result.submittedAt")} {formatDate(submission.submitted_datetime)}
            </span>
          )}
          {submission.language && (
            <span className="inline-flex items-center gap-1.5">
              <Gauge className="size-3.5" />
              {t("result.language")} {submission.language}
            </span>
          )}
        </div>
      </div>

      {/* ─── Output lỗi ─────────────────────────────────────────────────── */}
      {errorOutput && (
        <div className="rounded-2xl border border-red-200 bg-slate-950 dark:border-red-500/30">
          <div className="flex items-center gap-2 border-b border-white/10 px-4 py-2.5 text-xs font-semibold text-slate-300">
            <CircleSlash className="size-3.5 text-red-400" />
            {t("result.errorTitle")}
          </div>
          <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap text-red-200">
            {errorOutput}
          </pre>
        </div>
      )}

      {/* ─── Nhận xét của giảng viên ────────────────────────────────────── */}
      {submission.feedback?.trim() && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50/60 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-300">
            {t("result.feedbackTitle")}
          </p>
          <p className="mt-1.5 whitespace-pre-wrap text-sm text-amber-900 dark:text-amber-200">
            {submission.feedback}
          </p>
        </div>
      )}

      {/* ─── Bảng chi tiết testcase ────────────────────────────────────── */}
      {testcases.length > 0 && (
        <div className="rounded-2xl border bg-card p-5">
          <h3 className="mb-3 text-sm font-bold text-slate-900 dark:text-slate-100">
            {t("result.testcaseDetails")}
          </h3>
          <div className="grid gap-2 sm:grid-cols-2">
            {testcases.map((testcase, index) => {
              // Backend chỉ trả về số testcase đạt (passed_count) theo thứ tự,
              // nên testcase đầu tiên trong danh sách là các testcase đã đạt.
              const passed = index < submission.passed_count;
              return (
                <div
                  key={testcase.id}
                  className={cn(
                    "flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-xs",
                    passed
                      ? "bg-emerald-50/60 dark:bg-emerald-500/10"
                      : "border-red-200 bg-red-50/60 dark:border-red-500/30 dark:bg-red-500/10",
                  )}
                >
                  <span className="font-medium">
                    Test #{index + 1}
                    {testcase.is_sample && (
                      <span className="ml-1.5 text-[10px] text-muted-foreground">({t("result.sample")})</span>
                    )}
                  </span>
                  <span
                    className={cn(
                      "flex items-center gap-1 font-semibold",
                      passed
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-red-600 dark:text-red-400",
                    )}
                  >
                    {passed ? (
                      <>
                        <CheckCircle2 className="size-3.5" /> {t("result.correct")}
                      </>
                    ) : (
                      <>
                        <XCircle className="size-3.5" /> {t("result.incorrect")}
                      </>
                    )}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
