"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Clock, FileCode2, FlaskConical, PlayCircle, Send, TriangleAlert } from "lucide-react";
import { toast } from "sonner";

import { AiReviewSection } from "@/components/student/ai-review-panel";
import { CheckAnswerPanel } from "@/components/student/check-answer-panel";
import { CodeEditor } from "@/components/student/code-editor";
import { GradingResultPanel } from "@/components/student/grading-result-panel";
import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { findLanguageOption } from "@/lib/helpers/languages";
import { formatDeadline } from "@/lib/helpers/datetime";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { useLocale } from "@/lib/i18n";
import {
  useCourseWithProblem,
  useProblemDetail,
  useRunCode,
  useSubmitAssignment,
  useSubmissionResult,
} from "@/lib/hooks/use-submissions";
import type { RunCodeResponse } from "@/lib/api/endpoints/submissions";
import type { StudentSubmissionDetail } from "@/lib/types/submission";

/**
 * Trang chi tiết bài tập của sinh viên.
 *
 * Luồng: đọc đề → soạn code → nộp bài → backend chấm nền → poll kết quả.
 * Vì chấm chạy nền nên sau khi nộp, trang tự poll `GET /submissions/{id}/result`
 * cho tới khi có trạng thái cuối rồi hiển thị kết quả.
 */
export default function StudentAssignmentDetailPage() {
  const { id, assignmentId } = useParams<{ id: string; assignmentId: string }>();
  const courseId = Array.isArray(id) ? id[0] : id;
  const problemId = Number(assignmentId);

  const courseQuery = useCourseWithProblem(courseId, assignmentId);
  const lessonId = courseQuery.data?.session?.id;
  const problemQuery = useProblemDetail({ course: courseId, lessonId, problemId });

  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  /** Id bài vừa nộp — dùng để poll kết quả chấm nền. */
  const [submittedId, setSubmittedId] = useState<number | null>(null);
  /** Bài đã nạp mã mẫu — dùng để nạp lại code khi đổi bài (tránh setState trong effect). */
  const [loadedProblemId, setLoadedProblemId] = useState<number | null>(null);
  /** Kết quả lần chạy "Kiểm tra đáp án" gần nhất (null = chưa chạy). */
  const [checkResult, setCheckResult] = useState<RunCodeResponse | null>(null);

  const submitMutation = useSubmitAssignment(courseId, lessonId, problemId);
  const runMutation = useRunCode(courseId, lessonId, problemId);
  const resultQuery = useSubmissionResult(submittedId ?? undefined);
  const { t } = useLocale();

  useBreadcrumbLabel(problemQuery.data?.title ?? "nav.assignments");

  // Nạp mã mẫu khi bài tập tải xong. Điều chỉnh state trong lúc render là cách
  // React khuyến nghị thay cho setState trong effect (tránh render dây chuyền).
  const starterCode = problemQuery.data?.starter_code;
  if (starterCode && loadedProblemId !== problemQuery.data?.id) {
    setLoadedProblemId(problemQuery.data?.id ?? null);
    setCode(starterCode);
  }

  const sample = useMemo(
    () => (problemQuery.data?.testcases ?? []).filter((testcase) => testcase.is_sample),
    [problemQuery.data?.testcases],
  );

  // Backend chấm nền nên sau khi nộp vẫn đang ở pending/processing.
  const isGrading =
    submitMutation.isPending ||
    (submittedId !== null &&
      (resultQuery.data?.status === "pending" || resultQuery.data?.status === "processing"));

  function handleSubmit() {
    if (!code.trim()) {
      toast.error(t("student.assignment.emptySource"));
      return;
    }
    submitMutation.mutate(
      { code, language },
      {
        onSuccess: (data) => {
          setSubmittedId(data.submission_id);
          toast.success(t("student.assignment.toastSubmitted"));
        },
        onError: (error) => {
          toast.error(getErrorMessage(error));
        },
      },
    );
  }

  /**
   * "Kiểm tra đáp án": chạy code với testcase MẪU (`POST .../run`).
   * Không tạo bài nộp và không ảnh hưởng điểm — chỉ để sinh viên tự soát.
   */
  function handleCheckAnswer() {
    if (!code.trim()) {
      toast.error(t("student.assignment.emptySource"));
      return;
    }
    runMutation.mutate(
      { code, language },
      {
        onSuccess: (data) => {
          setCheckResult(data);
        },
        onError: (error) => {
          setCheckResult(null);
          toast.error(getErrorMessage(error));
        },
      },
    );
  }

  if (courseQuery.isPending) return <AssignmentSkeleton />;

  if (courseQuery.error) {
    return <ErrorState error={courseQuery.error} onRetry={() => void courseQuery.refetch()} />;
  }

  // Không tìm thấy buổi học chứa bài này -> báo rõ ràng thay vì treo ở skeleton
  // (problemQuery bị disable khi thiếu lessonId nên isPending sẽ không bao giờ hết).
  if (!courseQuery.data?.session) {
    return (
      <EmptyState
        icon={TriangleAlert}
        title={t("student.assignment.notFound")}
        description={t("student.assignment.notFoundDesc")}
      />
    );
  }

  if (problemQuery.isPending) return <AssignmentSkeleton />;

  if (problemQuery.error) {
    return <ErrorState error={problemQuery.error} onRetry={() => void problemQuery.refetch()} />;
  }

  const course = courseQuery.data?.course;
  const problem = problemQuery.data;
  const session = courseQuery.data?.session;

  if (!course || !problem) {
    return (
      <EmptyState
        icon={TriangleAlert}
        title={t("student.assignment.notFound")}
        description={t("student.assignment.notFoundDesc2")}
      />
    );
  }

  const languageLabel = findLanguageOption(language)?.label ?? language;

  return (
    <div className="space-y-5">
      {/* ─── Header ────────────────────────────────────────────────────── */}
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href={`/student/classes/${encodeURIComponent(courseId)}`}
            className="inline-flex items-center gap-1 text-sm text-indigo-700 hover:underline"
          >
            <ArrowLeft className="size-4" /> {t("student.assignment.backToClass")}
          </Link>
          <h1 className="mt-2 text-2xl font-bold">
            {problem.code ?? `${t("history.problemFallback")} ${problem.id}`}: {problem.title}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">{course.name}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <Badge className="bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300">
            {languageLabel}
          </Badge>
          <span className="inline-flex items-center gap-1">
            <Clock className="size-4" />
            {t("student.assignment.due")} {session?.deadline ? formatDeadline(session.deadline) : "—"}
          </span>
        </div>
      </header>

      {/* ─── Stats ─────────────────────────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-4">
        <Stat
          icon={<Clock />}
          label={t("student.assignment.stat.runtime")}
          value={`${problem.time_limit_seconds}s`}
        />
        <Stat
          icon={<FlaskConical />}
          label={t("student.assignment.stat.testcases")}
          value={String(problem.total_number_testcase)}
        />
        <Stat icon={<FileCode2 />} label={t("student.assignment.stat.level")} value={problem.level} />
        <Stat icon={<FileCode2 />} label={t("student.assignment.stat.language")} value={languageLabel} />
      </div>

      {/* ─── Đề bài + Editor ───────────────────────────────────────────── */}
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(380px,1fr)]">
        <article className="space-y-5 rounded-2xl border bg-card p-6">
          <Section title={t("student.assignment.section.statement")}>
            <p className="whitespace-pre-wrap text-sm leading-7">{problem.description}</p>
          </Section>

          <Section title={t("student.assignment.section.constraints")}>
            <pre className="whitespace-pre-wrap rounded-lg bg-indigo-50 p-4 text-sm dark:bg-indigo-500/10">
              {problem.constraints || "—"}
            </pre>
          </Section>

          {problem.hint && (
            <Section title={t("student.assignment.section.hint")}>
              <p className="whitespace-pre-wrap text-sm">{problem.hint}</p>
            </Section>
          )}

          <Section title={t("student.assignment.section.samples")}>
            {sample.length ? (
              <div className="space-y-3">
                {sample.map((testcase, index) => (
                  <div key={testcase.id} className="rounded-lg border bg-indigo-50/60 p-3 text-sm dark:bg-indigo-500/10">
                    <strong>Test #{index + 1}</strong>
                    <pre className="mt-2 whitespace-pre-wrap">
                      {t("student.assignment.sampleInput")}: {String(testcase.input)}
                      {"\n"}
                      {t("student.assignment.sampleOutput")}: {String(testcase.expected_output)}
                    </pre>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{t("student.assignment.noSamples")}</p>
            )}
          </Section>
        </article>

        <div className="space-y-3">
          <CodeEditor
            value={code}
            onChange={setCode}
            starterCodes={problem.starter_codes}
            fallbackCode={problem.starter_code}
            language={language}
            onLanguageChange={setLanguage}
            supportedLanguages={problem.supported_languages}
            functionName={problem.function_name}
            disabled={isGrading}
          />

          <div className="flex flex-wrap items-center justify-end gap-3">
            {isGrading && (
              <p className="text-xs text-muted-foreground">
                {t("student.assignment.gradingWait")}
              </p>
            )}
            {/* "Kiểm tra đáp án": chạy testcase mẫu, không tạo bài nộp. */}
            <Button
              size="lg"
              variant="outline"
              onClick={handleCheckAnswer}
              disabled={isGrading || runMutation.isPending}
              className="font-semibold"
            >
              <PlayCircle className="size-4" />
              {runMutation.isPending
                ? t("student.assignment.checking")
                : t("student.assignment.checkAnswer")}
            </Button>
            <Button
              size="lg"
              onClick={handleSubmit}
              disabled={isGrading}
              className="bg-[#352078] font-semibold text-white hover:bg-[#2b1a63]"
            >
              <Send className="size-4" />
              {submitMutation.isPending ? t("student.assignment.submitting") : t("student.assignment.submit")}
            </Button>
          </div>
        </div>
      </div>

      {/* ─── Kết quả kiểm tra đáp án (chạy testcase mẫu) ───────────────── */}
      {checkResult && (
        <section className="space-y-3">
          <CheckAnswerPanel result={checkResult} />
        </section>
      )}

      {/* ─── Kết quả chấm ──────────────────────────────────────────────── */}
      {submittedId !== null && resultQuery.data && (
        <section className="space-y-3">
          <h2 className="text-lg font-bold text-[#2f226b]">{t("student.assignment.resultTitle")}</h2>
          <GradingResultPanel
            submission={resultQuery.data as unknown as StudentSubmissionDetail}
          />
          {/* Chỉ hiện khi lần nộp này pass hết testcase. `key` theo id bài nộp
              để nộp lại thì review của lần trước bị xoá. */}
          <AiReviewSection
            key={submittedId}
            submission={{ ...resultQuery.data, id: submittedId }}
          />
        </section>
      )}
    </div>
  );
}

/* ─── Helpers ─────────────────────────────────────────────────────────────── */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2">
      <h2 className="font-bold text-[#2f226b]">{title}</h2>
      {children}
    </section>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="flex items-center gap-2 text-indigo-700">
        {icon}
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <strong className="mt-2 block">{value}</strong>
    </div>
  );
}

function AssignmentSkeleton() {
  return (
    <div className="space-y-5">
      <Skeleton className="h-16 w-full rounded-xl" />
      <div className="grid gap-4 sm:grid-cols-4">
        {[1, 2, 3, 4].map((item) => (
          <Skeleton key={item} className="h-24 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-[600px] w-full rounded-2xl" />
    </div>
  );
}
