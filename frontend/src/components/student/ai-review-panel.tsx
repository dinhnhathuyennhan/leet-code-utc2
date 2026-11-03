"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Info,
  Lightbulb,
  Loader2,
  RotateCcw,
  Sparkles,
  X,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AiReviewError } from "@/lib/api/endpoints/ai-review";
import { canReviewCode } from "@/lib/helpers/submission-status";
import { useAiReview } from "@/lib/hooks/use-ai-review";
import { useLocale, type Locale, type TranslationKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { AiReviewErrorCode, AiReviewResult } from "@/lib/types/ai-review";

/** Sau bao lâu thì báo "lần đầu có thể mất 1–2 phút" (model đang được nạp). */
export const AI_REVIEW_WARMUP_HINT_MS = 15_000;

/** Lỗi không thể khắc phục bằng cách bấm lại: ẩn nút "Thử lại". */
const NON_RETRYABLE: ReadonlySet<AiReviewErrorCode> = new Set([
  "SUBMISSION_NOT_ACCEPTED",
  "CODE_TOO_LONG",
  "NOT_FOUND",
]);

function errorCodeOf(error: unknown): AiReviewErrorCode {
  return error instanceof AiReviewError ? error.code : "UNKNOWN";
}

export interface AiReviewSubmission {
  id: number;
  status: string;
  passed_count: number;
  total_testcases: number;
}

/**
 * Nút "Review code" + panel kết quả AI review cho một bài nộp.
 *
 * - Không render gì nếu bài nộp chưa pass toàn bộ testcase.
 * - Chỉ gọi AI khi sinh viên bấm nút (không tự gọi khi mount, không tự retry).
 * - Parent nên đặt `key={submission.id}` để nộp bài mới thì kết quả cũ bị xoá.
 */
export function AiReviewSection({
  submission,
  className,
}: {
  submission: AiReviewSubmission | null | undefined;
  className?: string;
}) {
  if (!submission || !canReviewCode(submission)) return null;
  return <AiReviewSectionInner submissionId={submission.id} className={className} />;
}

function AiReviewSectionInner({ submissionId, className }: { submissionId: number; className?: string }) {
  const { t, locale } = useLocale();

  // Một mutation cho MỖI ngôn ngữ: React Query giữ state riêng theo mutationKey,
  // nên kết quả (và cả lượt đang chạy) của "vi" vẫn còn khi người dùng xem "en".
  // Nhờ vậy đổi qua đổi lại không phải chờ Ollama sinh lại.
  const viReview = useAiReview(submissionId, "vi");
  const enReview = useAiReview(submissionId, "en");
  const review = locale === "en" ? enReview : viReview;

  const [showWarmup, setShowWarmup] = useState(false);

  // Đã bấm "Review code" lần nào chưa — chỉ khi đã bấm mới tự review lại theo
  // ngôn ngữ mới. Dùng ref vì chỉ cần nhớ, không cần render lại.
  const startedRef = useRef(false);
  // Ngôn ngữ của lượt review gần nhất đã kích hoạt, để không gọi trùng.
  const requestedRef = useRef<Locale | null>(null);

  // `mutate` ổn định tham chiếu giữa các render (React Query đảm bảo), nên
  // tách ra để effect dưới không chạy lại chỉ vì object mutation đổi identity.
  const { mutate: mutateVi, reset: resetVi, isIdle: viIdle } = viReview;
  const { mutate: mutateEn, reset: resetEn, isIdle: enIdle } = enReview;

  const runReview = useCallback(
    (target: Locale) => {
      startedRef.current = true;
      requestedRef.current = target;
      (target === "en" ? mutateEn : mutateVi)();
    },
    [mutateEn, mutateVi],
  );

  // Đổi VI <-> EN sau khi đã review: sinh lại bằng ngôn ngữ mới.
  // - Ngôn ngữ đích đã có kết quả (hoặc đang chạy) thì KHÔNG gọi lại, chỉ hiện
  //   phần đã lưu — đây là lý do bấm chuyển liên tục không phải đợi.
  // - Lỗi cũng được giữ nguyên, không tự thử lại (mỗi lượt tốn GPU).
  useEffect(() => {
    if (!startedRef.current) return;
    if (requestedRef.current === locale) return;

    const targetIdle = locale === "en" ? enIdle : viIdle;
    requestedRef.current = locale;
    if (targetIdle) {
      (locale === "en" ? mutateEn : mutateVi)();
    }
  }, [locale, enIdle, viIdle, mutateEn, mutateVi]);

  // Đóng panel: xoá kết quả của CẢ HAI ngôn ngữ, nếu không thì chuyển ngôn ngữ
  // sẽ làm panel bật lại kết quả vừa đóng.
  const close = useCallback(() => {
    startedRef.current = false;
    requestedRef.current = null;
    resetVi();
    resetEn();
  }, [resetVi, resetEn]);

  // Bật dòng nhắc "đang khởi động" nếu chờ quá lâu; tắt khi request kết thúc.
  useEffect(() => {
    if (!review.isPending) return;
    const timer = window.setTimeout(() => setShowWarmup(true), AI_REVIEW_WARMUP_HINT_MS);
    return () => {
      window.clearTimeout(timer);
      setShowWarmup(false);
    };
  }, [review.isPending]);

  const start = () => {
    if (review.isPending) return;
    runReview(locale);
  };

  const isIdle = review.isIdle;

  return (
    <section
      className={cn("space-y-3", className)}
      aria-label={t("aiReview.title")}
      data-testid="ai-review-section"
    >
      {/* ─── Lời mời + nút ──────────────────────────────────────────── */}
      {(isIdle || review.isPending) && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-indigo-200 bg-indigo-50/60 px-5 py-4 dark:border-indigo-500/30 dark:bg-indigo-500/10">
          <p className="flex items-center gap-2 text-sm text-indigo-900 dark:text-indigo-200">
            <Sparkles className="size-4 shrink-0 text-indigo-600 dark:text-indigo-300" aria-hidden />
            {t("aiReview.prompt")}
          </p>
          <Button
            type="button"
            onClick={start}
            disabled={review.isPending}
            aria-busy={review.isPending}
            className="bg-[#352078] font-semibold text-white hover:bg-[#2b1a63]"
          >
            {review.isPending ? (
              <Loader2 className="size-4 animate-spin" aria-hidden />
            ) : (
              <Sparkles className="size-4" aria-hidden />
            )}
            {review.isPending ? t("aiReview.running") : t("aiReview.button")}
          </Button>
        </div>
      )}

      {/* ─── Vùng kết quả: aria-live để trình đọc màn hình báo khi xong ── */}
      <div aria-live="polite" aria-busy={review.isPending}>
        {review.isPending && <ReviewSkeleton showWarmup={showWarmup} />}

        {review.isError && (
          <ReviewErrorCard
            code={errorCodeOf(review.error)}
            onRetry={start}
          />
        )}

        {review.isSuccess && (
          <ReviewResultCard
            result={review.data}
            onClose={close}
            onReviewAgain={start}
          />
        )}
      </div>
    </section>
  );
}

/* ─── Đang chạy ─────────────────────────────────────────────────────────── */

function ReviewSkeleton({ showWarmup }: { showWarmup: boolean }) {
  const { t } = useLocale();
  return (
    <div className="space-y-3 rounded-2xl border border-indigo-200 bg-card p-5 dark:border-indigo-500/30" data-testid="ai-review-loading">
      <p className="text-sm text-muted-foreground">{t("aiReview.runningDesc")}</p>
      {showWarmup && (
        <p className="text-xs font-medium text-amber-700 dark:text-amber-300">{t("aiReview.warmup")}</p>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        <Skeleton className="h-16 rounded-xl" />
        <Skeleton className="h-16 rounded-xl" />
      </div>
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  );
}

/* ─── Lỗi ───────────────────────────────────────────────────────────────── */

function ReviewErrorCard({ code, onRetry }: { code: AiReviewErrorCode; onRetry: () => void }) {
  const { t } = useLocale();
  const canRetry = !NON_RETRYABLE.has(code);
  return (
    <div
      role="alert"
      className="flex flex-wrap items-start justify-between gap-3 rounded-2xl border border-red-200 bg-red-50/70 p-5 dark:border-red-500/30 dark:bg-red-500/10"
    >
      <div className="flex items-start gap-2">
        <XCircle className="mt-0.5 size-4 shrink-0 text-red-600 dark:text-red-400" aria-hidden />
        <div>
          <p className="text-sm font-semibold text-red-800 dark:text-red-200">{t("aiReview.errorTitle")}</p>
          <p className="mt-0.5 text-sm text-red-700 dark:text-red-300">
            {t(`aiReview.error.${code}` as TranslationKey)}
          </p>
        </div>
      </div>
      {canRetry && (
        <Button type="button" variant="outline" onClick={onRetry}>
          <RotateCcw className="size-4" aria-hidden />
          {t("aiReview.retry")}
        </Button>
      )}
    </div>
  );
}

/* ─── Kết quả ───────────────────────────────────────────────────────────── */

function ComplexityCard({
  label,
  current,
  expected,
  showExpected,
  testId,
}: {
  label: string;
  current: string;
  expected: string;
  showExpected: boolean;
  testId: string;
}) {
  return (
    <div className="rounded-xl border bg-indigo-50/50 p-4 dark:bg-indigo-500/10" data-testid={testId}>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1.5 flex flex-wrap items-center gap-2 font-mono text-lg font-bold text-slate-900 dark:text-slate-100">
        <span>{current}</span>
        {showExpected && (
          <>
            <ArrowRight className="size-4 text-emerald-600 dark:text-emerald-400" aria-label="→" />
            <span className="text-emerald-700 dark:text-emerald-300">{expected}</span>
          </>
        )}
      </p>
    </div>
  );
}

/** So sánh độ phức tạp bỏ qua khoảng trắng/hoa thường ("O(N)" == "O(n)"). */
function sameComplexity(a: string, b: string): boolean {
  const normalize = (value: string) => value.replace(/\s+/g, "").toLowerCase();
  return normalize(a) === normalize(b);
}

export function ReviewResultCard({
  result,
  onClose,
  onReviewAgain,
}: {
  result: AiReviewResult;
  onClose: () => void;
  onReviewAgain: () => void;
}) {
  const { t } = useLocale();
  const { optimization } = result;
  const optimizable = optimization.is_optimizable;
  const issues = result.issues.map((issue) => issue.trim()).filter(Boolean);

  return (
    <article className="space-y-4 rounded-2xl border border-indigo-200 bg-card p-5 dark:border-indigo-500/30" data-testid="ai-review-result">
      <header className="flex items-start justify-between gap-3">
        <h3 className="flex items-center gap-2 text-base font-bold text-[#2f226b] dark:text-indigo-200">
          <Sparkles className="size-4" aria-hidden />
          {t("aiReview.title")}
        </h3>
        <Button type="button" variant="ghost" size="icon-sm" onClick={onClose} aria-label={t("aiReview.close")}>
          <X className="size-4" aria-hidden />
        </Button>
      </header>

      {result.summary.trim() && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t("aiReview.summary")}</p>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-6">{result.summary}</p>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <ComplexityCard
          testId="ai-review-time"
          label={t("aiReview.time")}
          current={result.time_complexity}
          expected={optimization.expected_time_complexity}
          showExpected={optimizable && !sameComplexity(result.time_complexity, optimization.expected_time_complexity)}
        />
        <ComplexityCard
          testId="ai-review-space"
          label={t("aiReview.space")}
          current={result.space_complexity}
          expected={optimization.expected_space_complexity}
          showExpected={optimizable && !sameComplexity(result.space_complexity, optimization.expected_space_complexity)}
        />
      </div>

      {result.complexity_explanation.trim() && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t("aiReview.explanation")}</p>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-700 dark:text-slate-300">
            {result.complexity_explanation}
          </p>
        </div>
      )}

      <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-4 dark:border-amber-500/30 dark:bg-amber-500/10">
        <p className="flex items-center gap-2 text-sm font-semibold text-amber-900 dark:text-amber-200">
          <AlertTriangle className="size-4" aria-hidden />
          {t("aiReview.issues")}
          {issues.length > 0 && <span className="tabular-nums">({issues.length})</span>}
        </p>
        {issues.length > 0 ? (
          <ul className="mt-2 list-disc space-y-1 pl-6 text-sm text-amber-900 dark:text-amber-100">
            {issues.map((issue, index) => (
              <li key={index} className="whitespace-pre-wrap">{issue}</li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 flex items-center gap-1.5 text-sm text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 className="size-4" aria-hidden />
            {t("aiReview.noIssues")}
          </p>
        )}
      </div>

      {optimizable ? (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50/60 p-4 dark:border-indigo-500/30 dark:bg-indigo-500/10">
          <p className="flex items-center gap-2 text-sm font-semibold text-indigo-900 dark:text-indigo-200">
            <Lightbulb className="size-4" aria-hidden />
            {t("aiReview.optimization")}
          </p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-indigo-950 dark:text-indigo-100">
            {optimization.suggestion}
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-4 dark:border-emerald-500/30 dark:bg-emerald-500/10">
          <p className="flex items-center gap-2 text-sm font-semibold text-emerald-800 dark:text-emerald-200">
            <CheckCircle2 className="size-4" aria-hidden />
            {t("aiReview.alreadyOptimal")}
          </p>
          {optimization.suggestion.trim() && (
            <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-emerald-900 dark:text-emerald-100">
              {optimization.suggestion}
            </p>
          )}
        </div>
      )}

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t pt-3">
        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Info className="size-3.5 shrink-0" aria-hidden />
          {t("aiReview.disclaimer")}
        </p>
        <Button type="button" variant="outline" size="sm" onClick={onReviewAgain}>
          <RotateCcw className="size-3.5" aria-hidden />
          {t("aiReview.reviewAgain")}
        </Button>
      </footer>
    </article>
  );
}
