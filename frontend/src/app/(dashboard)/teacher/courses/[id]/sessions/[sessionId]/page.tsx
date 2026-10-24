"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Calendar, Pencil, Users } from "lucide-react";

import { useBreadcrumbLabels } from "@/components/shared/breadcrumb-context";
import { ErrorState, ForbiddenState } from "@/components/shared/page-state";
import { ApiError } from "@/lib/api/error";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { getSessionDetail } from "@/lib/api/endpoints/courses";
import type { SessionDetailData } from "@/lib/types/course";
import { SessionEditPage } from "@/components/teacher/session-edit-page";
import { formatDate } from "@/lib/helpers/format";
import { getSessionStatus } from "@/lib/helpers/session-status";
import { SessionStatusBadge } from "@/components/teacher/session-status-badge";
import { SessionStats } from "@/components/teacher/session-stats";
import { SessionDeadlineAlert } from "@/components/teacher/session-deadline-alert";
import { SessionActions } from "@/components/teacher/session-actions";
import { ExerciseList } from "@/components/teacher/exercise-list";

function PageSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-32 w-full rounded-2xl" />
      <div className="grid gap-5 md:grid-cols-3">
        {[0, 1, 2].map((i) => <Skeleton key={i} className="h-28 rounded-2xl" />)}
      </div>
      <Skeleton className="h-64 w-full rounded-2xl" />
    </div>
  );
}

export default function TeacherSessionDetailPage() {
  const { id: courseId, sessionId } = useParams<{ id: string; sessionId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const isEdit = searchParams.get("mode") === "edit";

  const [data, setData] = useState<SessionDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  useBreadcrumbLabels(courseId, data?.title ?? "Buổi học", isEdit ? "Soạn bài tập" : null);

  useEffect(() => {
    let cancelled = false;
    getSessionDetail(courseId, sessionId)
      .then((res) => !cancelled && setData(res))
      .catch((e) => !cancelled && setError(e))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [courseId, sessionId]);

  const status = useMemo(() => (data ? getSessionStatus(data.start_date, data.end_date) : null), [data]);

  if (loading) return <PageSkeleton />;
  if (error || !data || !status) {
    if (error instanceof ApiError && error.status === 403) return <ForbiddenState />;
    return <ErrorState error={error} />;
  }
  if (isEdit) {
    return <SessionEditPage
      courseId={courseId}
      sessionId={sessionId}
      data={data}
      onSaved={async () => {
        const refreshed = await getSessionDetail(courseId, sessionId);
        setData(refreshed);
      }}
    />;
  }

  const base = `/teacher/courses/${courseId}/sessions/${sessionId}`;
  const submissionsHref = `/teacher/submissions?course=${encodeURIComponent(data.course_code)}&lesson_id=${sessionId}`;

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-start justify-between gap-6 rounded-2xl border bg-card p-6 shadow-xs">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-3xl">{data.title}</h1>
            <SessionStatusBadge status={status} />
          </div>
          <div className="flex flex-wrap items-center gap-6 text-[15px] text-muted-foreground">
            <span className="flex items-center gap-2">
              <Calendar className="size-4 text-slate-500" />
              Mở - đóng: <strong>{formatDate(data.start_date)} → {formatDate(data.end_date)}</strong>
            </span>
            <span className="flex items-center gap-2">
              <Users className="size-4 text-slate-500" />
              Sĩ số nộp: <strong>{data.submitted_students}/{data.total_students} SV</strong>
            </span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-3">
            <Button onClick={() => router.push(`${base}?mode=edit`)} className="h-10 gap-1.5 bg-[#2f226b] font-semibold text-white hover:bg-[#251b56]">
              <Pencil className="size-4" /> Soạn buổi & bài tập
            </Button>
            <SessionActions courseId={courseId} sessionId={sessionId} exerciseCount={data.exercises.length} />
          </div>
          {status === "open" && data.deadline_notice && (
            <p className="text-sm font-semibold text-red-600 dark:text-red-400">{data.deadline_notice}</p>
          )}
        </div>
      </section>

      <SessionStats stats={data.stats} total_students={data.total_students} submitted_students={data.submitted_students} />
      <SessionDeadlineAlert alert={data.alert} status={status} listHref={submissionsHref} />
      <ExerciseList
        exercises={data.exercises}
        courseId={courseId}
        sessionId={sessionId}
        courseCode={data.course_code}
        editHref={`${base}?mode=edit`}
      />
    </div>
  );
}
