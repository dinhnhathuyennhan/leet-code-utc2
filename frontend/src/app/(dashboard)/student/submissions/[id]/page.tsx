"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { AiReviewSection } from "@/components/student/ai-review-panel";
import { GradingResultPanel } from "@/components/student/grading-result-panel";
import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { ErrorState } from "@/components/shared/page-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useLocale } from "@/lib/i18n";
import { useMySubmissionDetail } from "@/lib/hooks/use-submissions";

/**
 * Trang chi tiết kết quả chấm một bài nộp của sinh viên.
 *
 * Hiển thị: mã nguồn đã nộp + kết quả chấm chi tiết theo từng test case.
 */
export default function StudentSubmissionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const submissionId = Array.isArray(id) ? id[0] : id;

  const query = useMySubmissionDetail(submissionId);
  const { t } = useLocale();

  useBreadcrumbLabel(
    query.data ? `${t("submission.resultNumbered")}${query.data.id}` : "submission.resultFallback",
  );

  if (query.isPending) {
    return (
      <div className="space-y-4" aria-busy="true">
        <Skeleton className="h-12 w-full rounded-xl" />
        <Skeleton className="h-56 w-full rounded-2xl" />
        <Skeleton className="h-72 w-full rounded-2xl" />
      </div>
    );
  }

  if (query.error || !query.data) {
    return (
      <ErrorState error={query.error} onRetry={() => void query.refetch()} />
    );
  }

  const submission = query.data;

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href="/student/history"
            className="inline-flex items-center gap-1 text-sm text-indigo-700 hover:underline"
          >
            <ArrowLeft className="size-4" /> {t("submission.backToHistory")}
          </Link>
          <h1 className="mt-2 text-2xl font-bold">
            {submission.problem_code ?? `${t("history.problemFallback")} ${submission.problem_id}`}: {submission.problem_title}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {submission.course_name} · {submission.session_label}
          </p>
        </div>
      </header>

      <GradingResultPanel submission={submission} />

      {/* ─── Mã nguồn đã nộp ───────────────────────────────────────────── */}
      <section className="overflow-hidden rounded-2xl border bg-slate-950 text-slate-100">
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-2.5 text-xs text-slate-300">
          <span className="font-mono">{t("submission.sourceTitle")} ({submission.language})</span>
        </div>
        <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-slate-200">
          <code>{submission.submitted_code}</code>
        </pre>
      </section>

      {/* Chỉ hiện khi bài nộp này pass hết testcase. */}
      <AiReviewSection key={submission.id} submission={submission} />
    </div>
  );
}
