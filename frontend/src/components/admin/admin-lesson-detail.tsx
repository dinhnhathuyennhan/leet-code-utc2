"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, BookOpenCheck, CalendarDays, FileCheck2, Pencil, Plus, Users } from "lucide-react";
import { toast } from "sonner";
import { useBreadcrumbLabels } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { attachAdminProblems, getAdminLesson, getAdminProblems } from "@/lib/api/endpoints/admin-management";
import { formatDate } from "@/lib/helpers/datetime";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import { adminKeys, useAdminCourse } from "@/lib/hooks/use-admin";
import { AdminLessonForm } from "./admin-course-detail";
import { adminLevelLabel } from "./admin-problem-bank";
import { AdminDialog, AdminHeading, AdminLoading, AdminMetric, ADMIN_PRIMARY } from "./admin-ui";

export function AdminLessonDetail({ courseId, lessonId }: { courseId: string; lessonId: string }) {
  const query = useQuery({ queryKey: [...adminKeys.course(courseId), "lesson", lessonId], queryFn: () => getAdminLesson(courseId, lessonId) });
  const course = useAdminCourse(courseId);
  const [attaching, setAttaching] = useState(false);
  const [editing, setEditing] = useState(false);
  useBreadcrumbLabels(courseId, query.data?.title ?? `Buổi #${lessonId}`);
  if (query.isPending) return <AdminLoading />;
  if (query.error || !query.data) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  const data = query.data;
  const session = course.data?.sessions?.find((item) => String(item.id) === lessonId);
  const submissionLink = `/admin/submissions?${new URLSearchParams({ course: courseId, lesson_id: lessonId })}`;
  return <div className="space-y-6">
    <Link href={`/admin/courses/${encodeURIComponent(courseId)}`} className="inline-flex items-center gap-2 text-sm text-indigo-700 dark:text-indigo-300"><ArrowLeft className="size-4" />Quay lại lớp học phần</Link>
    <AdminHeading title={`Buổi ${data.order}: ${data.title}`} description={`${data.course_code} · ${data.course_name}`}
      actions={<><Button variant="outline" disabled={!session} onClick={() => setEditing(true)}><Pencil className="size-4" />Chỉnh sửa buổi</Button><Button className={ADMIN_PRIMARY} onClick={() => setAttaching(true)}><Plus className="size-4" />Thêm từ ngân hàng đề</Button></>} />
    <section className="flex flex-wrap items-center gap-4 rounded-xl border bg-card p-5 text-sm"><CalendarDays className="size-5 text-indigo-600" /><span>Mở: <strong>{formatDate(data.start_date)}</strong></span><span>Hạn nộp: <strong>{formatDate(data.end_date)}</strong></span><span className="text-muted-foreground">{data.deadline_notice}</span></section>
    <div className="grid gap-4 sm:grid-cols-3">
      <AdminMetric label="Sinh viên đã nộp" value={data.submitted_students === null ? undefined : `${data.submitted_students}/${data.total_students ?? "—"}`} icon={Users} />
      <AdminMetric label="Tỉ lệ nộp bài" value={data.stats ? `${data.stats.submission_rate}%` : undefined} icon={FileCheck2} />
      <AdminMetric label="Điểm trung bình" value={data.stats ? `${data.stats.avg_score}/10` : undefined} icon={BookOpenCheck} />
    </div>
    {course.error && <ErrorState error={course.error} onRetry={() => void course.refetch()} />}
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-lg font-semibold">Bài tập thực hành ({data.exercises.length})</h2><Button asChild variant="outline"><Link href={submissionLink}>Xem bài nộp buổi này</Link></Button></div>
      {!data.exercises.length ? <EmptyState title="Buổi học chưa có bài tập" description="Chọn bài từ ngân hàng đề để giao cho sinh viên." /> : data.exercises.map((problem) => <article key={problem.id} className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card p-5 shadow-sm">
        <div className="min-w-0 flex-1 space-y-2"><div className="flex flex-wrap items-center gap-2"><h3 className="font-semibold">{problem.order}. {problem.title}</h3><span className="rounded bg-indigo-50 px-2 py-1 text-xs text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">{adminLevelLabel(problem.level)}</span></div>
          <p className="line-clamp-2 text-sm text-muted-foreground">{problem.description}</p><p className="text-xs text-muted-foreground">{problem.time_limit_seconds}s · {problem.total_number_testcase} testcase · {problem.submitted_count ?? "—"} bài nộp</p></div>
        <div className="flex flex-wrap gap-2"><Button asChild variant="outline" size="sm"><Link href={`/admin/courses/${encodeURIComponent(courseId)}/sessions/${lessonId}/problems/${problem.id}`}>Nội dung & testcase</Link></Button>
          <Button asChild size="sm" className={ADMIN_PRIMARY}><Link href={`${submissionLink}&problem_id=${problem.id}`}>Xem bài nộp</Link></Button></div>
      </article>)}
    </section>
    {editing && course.data && session && <AdminLessonForm course={course.data} session={session} onClose={() => setEditing(false)} />}
    {attaching && <ProblemPicker courseId={courseId} lessonId={lessonId} existingIds={data.exercises.map((item) => item.id)} onClose={() => setAttaching(false)} />}
  </div>;
}

function ProblemPicker({ courseId, lessonId, existingIds, onClose }: { courseId: string; lessonId: string; existingIds: number[]; onClose: () => void }) {
  const client = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const debounced = useDebouncedValue(search, 300);
  const query = useQuery({
    queryKey: [...adminKeys.problems, "picker", debounced, page],
    queryFn: () => getAdminProblems({ q: debounced.trim() || undefined, page, page_size: 20 }),
  });
  async function attach() {
    if (busy || !selected.length) return;
    setBusy(true);
    try {
      await attachAdminProblems(courseId, lessonId, selected);
      await client.invalidateQueries({ queryKey: adminKeys.all });
      toast.success("Đã gắn bài tập vào buổi học."); onClose();
    } catch (error) { toast.error(getErrorMessage(error)); } finally { setBusy(false); }
  }
  return <AdminDialog open title="Thêm bài tập từ ngân hàng đề" description="Các bài được chọn sẽ được sao chép vào buổi học. Bài nguồn và bài nộp cũ được giữ nguyên." onClose={onClose} busy={busy}>
    <Input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Tìm tên bài tập..." aria-label="Tìm bài để gắn vào buổi học" disabled={busy} />
    {query.isPending ? <p>Đang tải bài tập...</p> : query.error ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : !query.data?.items.length ? <EmptyState title="Không tìm thấy bài tập" /> :
      <div className="max-h-80 space-y-2 overflow-auto">{query.data.items.map((problem) => <label key={problem.id} className="flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm">
        <input type="checkbox" className="mt-1" checked={selected.includes(problem.id)} disabled={busy || existingIds.includes(problem.id)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, problem.id] : current.filter((id) => id !== problem.id))} />
        <span><strong>{problem.title}</strong><span className="mt-1 block text-xs text-muted-foreground">#{problem.id} · {adminLevelLabel(problem.level)} · {problem.total_number_testcase} testcase · {existingIds.includes(problem.id) ? "Đã có trong buổi" : problem.lesson_id === null ? "Đề nguồn" : "Sao chép từ buổi khác"}</span></span>
      </label>)}</div>}
    {query.data && <div className="flex justify-between gap-2"><Button variant="outline" disabled={page === 1 || busy} onClick={() => setPage(page - 1)}>Trước</Button><span className="self-center text-xs text-muted-foreground">Trang {page} · {query.data.total} bài tập</span><Button variant="outline" disabled={busy || page * 20 >= query.data.total} onClick={() => setPage(page + 1)}>Sau</Button></div>}
    <div className="flex items-center justify-between gap-3"><Link className="text-sm text-indigo-700 dark:text-indigo-300" href="/admin/problem-bank">Tạo bài tập nguồn mới →</Link><Button className={ADMIN_PRIMARY} disabled={busy || !selected.length} onClick={() => void attach()}>{busy ? "Đang thêm..." : `Thêm ${selected.length} bài tập`}</Button></div>
  </AdminDialog>;
}
