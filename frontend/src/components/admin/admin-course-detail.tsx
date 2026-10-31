"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CalendarDays, Download, Pencil, Plus, Search, Users } from "lucide-react";
import { toast } from "sonner";
import { useBreadcrumbLabels } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { CourseDetailTabs, type CourseTab } from "@/components/teacher/course-detail-tabs";
import { CourseGradesTable } from "@/components/teacher/course-grades-table";
import { CourseHeaderCard } from "@/components/teacher/course-header-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { addAdminClassEnrollment, addAdminEnrollment, deleteAdminEnrollment, getAdminEnrollments, saveAdminLesson } from "@/lib/api/endpoints/admin-management";
import { toCourseDetail } from "@/lib/api/transformers/course";
import { formatDeadline, toDateInput } from "@/lib/helpers/datetime";
import { downloadCsv } from "@/lib/helpers/download";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { adminKeys, useAdminClasses, useAdminCourse } from "@/lib/hooks/use-admin";
import type { AdminCourse } from "@/lib/types/admin";
import type { CourseSession } from "@/lib/types/course";
import { AdminConfirm, AdminDialog, AdminLoading, ADMIN_PRIMARY, ADMIN_SELECT } from "./admin-ui";
import { AdminCourseForm } from "./admin-courses";

export function AdminCourseDetail({ id }: { id: string }) {
  const query = useAdminCourse(id);
  const [tab, setTab] = useState<CourseTab>("sessions");
  const [courseEditor, setCourseEditor] = useState(false);
  const [lessonEditor, setLessonEditor] = useState<CourseSession | "new" | null>(null);
  useBreadcrumbLabels(query.data?.course_id ?? id, null);
  if (query.isPending) return <AdminLoading />;
  if (query.error || !query.data) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  const course = query.data;
  const detail = toCourseDetail(course);
  return <div className="space-y-6">
    <Link href="/admin/courses" className="inline-flex items-center gap-2 text-sm text-indigo-700 dark:text-indigo-300"><ArrowLeft className="size-4" />Lớp học phần</Link>
    <CourseHeaderCard course={detail} onCreateSession={() => setLessonEditor("new")} onEditCourse={() => setCourseEditor(true)} />
    <p className="text-sm text-muted-foreground">Người tạo: <strong>{course.created_by}</strong> · Học kỳ: {course.term}</p>
    <CourseDetailTabs value={tab} onValueChange={setTab}
      sessions={<div className="space-y-4">
        {!course.sessions?.length ? <EmptyState title="Chưa có buổi học" description="Tạo buổi học để bắt đầu giao bài tập." /> : [...course.sessions].sort((a, b) => a.order - b.order).map((session) =>
          <article key={session.id} className="rounded-xl border p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-2"><div className="flex flex-wrap items-center gap-2"><h2 className="text-lg font-semibold">Buổi {session.order}: {session.title}</h2>
                <span className="rounded-md bg-indigo-50 px-2 py-1 text-xs text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">{session.status === "open" ? "Đang mở" : session.status === "closed" ? "Đã đóng" : "Sắp mở"}</span></div>
                <p className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground"><CalendarDays className="size-4" />Hạn nộp: {formatDeadline(session.deadline)} · {session.problems.length} bài tập</p>
              </div>
              <div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => setLessonEditor(session)}><Pencil className="size-4" />Chỉnh sửa</Button>
                <Button asChild size="sm" className={ADMIN_PRIMARY}><Link href={`/admin/courses/${encodeURIComponent(id)}/sessions/${session.id}`}>Quản lý buổi học</Link></Button></div>
            </div>
            {!!session.problems.length && <div className="mt-4 flex flex-wrap gap-2">{session.problems.map((problem) => <Link className="rounded-lg bg-muted px-3 py-2 text-xs hover:bg-indigo-50 dark:hover:bg-indigo-500/20" key={problem.id} href={`/admin/courses/${encodeURIComponent(id)}/sessions/${session.id}/problems/${problem.id}`}>{problem.report || `#${problem.id}`} · {problem.title}</Link>)}</div>}
          </article>)}
      </div>}
      students={<AdminCourseRoster id={id} />}
      grades={<CourseGradesTable onUpdated={() => void query.refetch()} rows={detail.grades ?? []} sessions={detail.sessions.map((session) => ({
        id: session.id, order: session.order, title: session.title, status: session.status,
        problems: session.problems.map((problem) => ({ id: problem.id, code: problem.report ?? `#${problem.id}`, title: problem.title })),
      }))} />}
    />
    {courseEditor && <AdminCourseForm course={course} onClose={() => setCourseEditor(false)} />}
    {lessonEditor && <AdminLessonForm course={course} session={lessonEditor === "new" ? undefined : lessonEditor} onClose={() => setLessonEditor(null)} />}
  </div>;
}

export function AdminLessonForm({ course, session, onClose }: { course: AdminCourse; session?: CourseSession; onClose: () => void }) {
  const client = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState(session?.title ?? "");
  const [start, setStart] = useState(toDateInput(session?.opens_at || course.start_date));
  const [end, setEnd] = useState(toDateInput(session?.deadline || course.end_date));
  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    if (!title.trim() || !start || !end || start > end) { toast.error("Vui lòng nhập tên buổi và ngày bắt đầu/kết thúc hợp lệ."); return; }
    setBusy(true);
    try {
      await saveAdminLesson(course.course_id, { lesson_name: title.trim(), start_date: start, end_date: end, problem_ids: [] }, session?.id);
      await client.invalidateQueries({ queryKey: adminKeys.all });
      toast.success(session ? "Đã cập nhật buổi học." : "Đã tạo buổi học."); onClose();
    } catch (error) { toast.error(getErrorMessage(error)); } finally { setBusy(false); }
  }
  return <AdminDialog open title={session ? "Chỉnh sửa buổi học" : "Tạo buổi học"} description={`${course.course_id} · ${course.course_name}`} busy={busy} onClose={onClose}>
    <form onSubmit={(event) => void save(event)} className="space-y-4">
      <label className="block space-y-2 text-sm font-medium">Tên buổi học<Input value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={255} disabled={busy} /></label>
      <div className="grid gap-4 sm:grid-cols-2"><label className="space-y-2 text-sm font-medium">Ngày mở<Input type="date" value={start} onChange={(event) => setStart(event.target.value)} required disabled={busy} /></label>
        <label className="space-y-2 text-sm font-medium">Hạn nộp<Input type="date" value={end} min={start} onChange={(event) => setEnd(event.target.value)} required disabled={busy} /></label></div>
      <p className="text-xs text-muted-foreground">Buổi học mở lúc 00:00 ngày bắt đầu và đóng vào cuối ngày hạn nộp, theo giờ Việt Nam. Gắn bài tập tại trang quản lý buổi học.</p>
      <div className="flex justify-end gap-2"><Button type="button" variant="outline" disabled={busy} onClick={onClose}>Hủy</Button><Button type="submit" className={ADMIN_PRIMARY} disabled={busy}>{busy ? "Đang lưu..." : "Lưu buổi học"}</Button></div>
    </form>
  </AdminDialog>;
}

function AdminCourseRoster({ id }: { id: string }) {
  const client = useQueryClient();
  const query = useQuery({ queryKey: [...adminKeys.course(id), "enrollments"], queryFn: () => getAdminEnrollments(id) });
  const [search, setSearch] = useState("");
  const [adding, setAdding] = useState(false);
  const rows = (query.data ?? []).filter((student) => `${student.student_id} ${student.full_name} ${student.email}`.toLowerCase().includes(search.trim().toLowerCase()));
  async function remove(studentId: string) {
    await deleteAdminEnrollment(id, studentId);
    await client.invalidateQueries({ queryKey: adminKeys.all });
    toast.success("Đã xóa sinh viên khỏi lớp học phần.");
  }
  return <div className="space-y-4">
    <div className="flex flex-wrap gap-3">
      <div className="relative w-full min-w-0 sm:min-w-64 sm:flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tìm mã, tên hoặc email sinh viên..." aria-label="Tìm sinh viên trong lớp học phần" className="pl-9" /></div>
      <Button variant="outline" disabled={!rows.length} onClick={() => downloadCsv(`sinh-vien-${id}.csv`, [["MSSV", "Họ tên", "Email"], ...rows.map((student) => [student.student_id, student.full_name, student.email])])}><Download className="size-4" />Xuất danh sách</Button>
      <Button className={ADMIN_PRIMARY} onClick={() => setAdding(true)}><Plus className="size-4" />Thêm sinh viên</Button>
    </div>
    {query.isPending ? <p className="p-8 text-center text-sm text-muted-foreground">Đang tải danh sách...</p> : query.error ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : !rows.length ? <EmptyState icon={Users} title="Chưa có sinh viên phù hợp" /> :
      <Table className="min-w-[640px]"><TableHeader><TableRow><TableHead>MSSV</TableHead><TableHead>Họ tên</TableHead><TableHead>Email</TableHead><TableHead>Thao tác</TableHead></TableRow></TableHeader><TableBody>{rows.map((student) =>
        <TableRow key={student.student_id}><TableCell className="font-medium">{student.student_id}</TableCell><TableCell>{student.full_name}</TableCell><TableCell>{student.email}</TableCell><TableCell>
          <AdminConfirm label="Xóa khỏi lớp" title="Xóa sinh viên khỏi lớp học phần?" description={`${student.full_name} (${student.student_id}) sẽ được gỡ khỏi lớp ${id}. Tài khoản sinh viên vẫn được giữ lại.`} onConfirm={() => remove(student.student_id)} />
        </TableCell></TableRow>)}</TableBody></Table>}
    {adding && <EnrollmentForm id={id} onClose={() => setAdding(false)} />}
  </div>;
}

function EnrollmentForm({ id, onClose }: { id: string; onClose: () => void }) {
  const client = useQueryClient();
  const classes = useAdminClasses();
  const [mode, setMode] = useState("student");
  const [studentId, setStudentId] = useState("");
  const [classId, setClassId] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    try {
      if (mode === "class") {
        const result = await addAdminClassEnrollment(id, classId);
        toast.success(`Đã thêm ${result.added_count} sinh viên, bỏ qua ${result.skipped_count} sinh viên đã có trong lớp.`);
      } else { await addAdminEnrollment(id, studentId.trim()); toast.success("Đã thêm sinh viên vào lớp học phần."); }
      await client.invalidateQueries({ queryKey: adminKeys.all }); onClose();
    } catch (error) { toast.error(getErrorMessage(error)); } finally { setBusy(false); }
  }
  return <AdminDialog open title="Thêm sinh viên vào lớp học phần" description="Thêm một sinh viên hoặc toàn bộ sinh viên của một lớp hành chính." onClose={onClose} busy={busy}>
    <form onSubmit={(event) => void submit(event)} className="space-y-4">
      <div className="flex gap-2"><Button type="button" variant={mode === "student" ? "secondary" : "outline"} disabled={busy} onClick={() => setMode("student")}>Theo MSSV</Button><Button type="button" variant={mode === "class" ? "secondary" : "outline"} disabled={busy} onClick={() => setMode("class")}>Theo lớp hành chính</Button></div>
      {mode === "student" ? <label className="block space-y-2 text-sm font-medium">MSSV<Input value={studentId} onChange={(event) => setStudentId(event.target.value)} required disabled={busy} /></label> : <>
        <label className="block space-y-2 text-sm font-medium">Lớp hành chính<select className={`${ADMIN_SELECT} w-full`} value={classId} onChange={(event) => setClassId(event.target.value)} required disabled={busy || classes.isPending}><option value="">Chọn lớp</option>{classes.data?.map((item) => <option key={item.class_id} value={item.class_id}>{item.class_id} · {item.student_count} sinh viên</option>)}</select></label>
        {classes.error && <ErrorState error={classes.error} onRetry={() => void classes.refetch()} />}
      </>}
      <div className="flex justify-end gap-2"><Button type="button" variant="outline" disabled={busy} onClick={onClose}>Hủy</Button><Button type="submit" disabled={busy || (mode === "student" ? !studentId.trim() : !classId)} className={ADMIN_PRIMARY}>{busy ? "Đang thêm..." : "Thêm vào lớp"}</Button></div>
    </form>
  </AdminDialog>;
}
