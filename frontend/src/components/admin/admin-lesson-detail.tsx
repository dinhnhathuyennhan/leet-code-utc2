"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, BookOpenCheck, CalendarDays, FileCheck2, Users } from "lucide-react";
import { useBreadcrumbLabels } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { Button } from "@/components/ui/button";
import { getAdminLesson } from "@/lib/api/endpoints/admin-management";
import { formatDate } from "@/lib/helpers/datetime";
import { adminKeys } from "@/lib/hooks/use-admin";
import { adminLevelLabel } from "./admin-problem-bank";
import { AdminHeading, AdminLoading, AdminMetric } from "./admin-ui";

/** Admin chỉ xem buổi học; tạo/sửa buổi và gắn bài tập do giảng viên chủ lớp làm. */
export function AdminLessonDetail({ courseId, lessonId }: { courseId: string; lessonId: string }) {
  const query = useQuery({ queryKey: [...adminKeys.course(courseId), "lesson", lessonId], queryFn: () => getAdminLesson(courseId, lessonId) });
  useBreadcrumbLabels(courseId, query.data?.title ?? `Buổi #${lessonId}`);
  if (query.isPending) return <AdminLoading />;
  if (query.error || !query.data) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  const data = query.data;
  return <div className="space-y-6">
    <Link href={`/admin/courses/${encodeURIComponent(courseId)}`} className="inline-flex items-center gap-2 text-sm text-indigo-700 dark:text-indigo-300"><ArrowLeft className="size-4" />Quay lại lớp học phần</Link>
    <AdminHeading title={`Buổi ${data.order}: ${data.title}`} description={`${data.course_code} · ${data.course_name}`} />
    <section className="flex flex-wrap items-center gap-4 rounded-xl border bg-card p-5 text-sm"><CalendarDays className="size-5 text-indigo-600" /><span>Mở: <strong>{formatDate(data.start_date)}</strong></span><span>Hạn nộp: <strong>{formatDate(data.end_date)}</strong></span><span className="text-muted-foreground">{data.deadline_notice}</span></section>
    <div className="grid gap-4 sm:grid-cols-3">
      <AdminMetric label="Sinh viên đã nộp" value={data.submitted_students === null ? undefined : `${data.submitted_students}/${data.total_students ?? "—"}`} icon={Users} />
      <AdminMetric label="Tỉ lệ nộp bài" value={data.stats ? `${data.stats.submission_rate}%` : undefined} icon={FileCheck2} />
      <AdminMetric label="Điểm trung bình" value={data.stats ? `${data.stats.avg_score}/10` : undefined} icon={BookOpenCheck} />
    </div>
    <section className="space-y-4">
      <h2 className="text-lg font-semibold">Bài tập thực hành ({data.exercises.length})</h2>
      {!data.exercises.length ? <EmptyState title="Buổi học chưa có bài tập" description="Giảng viên chủ lớp chưa giao bài tập cho buổi học này." /> : data.exercises.map((problem) => <article key={problem.id} className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card p-5 shadow-sm">
        <div className="min-w-0 flex-1 space-y-2"><div className="flex flex-wrap items-center gap-2"><h3 className="font-semibold">{problem.order}. {problem.title}</h3><span className="rounded bg-indigo-50 px-2 py-1 text-xs text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">{adminLevelLabel(problem.level)}</span></div>
          <p className="line-clamp-2 text-sm text-muted-foreground">{problem.description}</p><p className="text-xs text-muted-foreground">{problem.time_limit_seconds}s · {problem.total_number_testcase} testcase · {problem.submitted_count ?? "—"} bài nộp</p></div>
        <Button asChild variant="outline" size="sm"><Link href={`/admin/courses/${encodeURIComponent(courseId)}/sessions/${lessonId}/problems/${problem.id}`}>Xem nội dung & testcase</Link></Button>
      </article>)}
    </section>
  </div>;
}
