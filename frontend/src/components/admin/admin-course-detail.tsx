"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CalendarDays, Download, Search, Users } from "lucide-react";
import { toast } from "sonner";
import { useBreadcrumbLabels } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { CourseDetailTabs, type CourseTab } from "@/components/teacher/course-detail-tabs";
import { CourseGradesTable } from "@/components/teacher/course-grades-table";
import { CourseHeaderCard } from "@/components/teacher/course-header-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getAdminEnrollments } from "@/lib/api/endpoints/admin-management";
import { toCourseDetail } from "@/lib/api/transformers/course";
import { deleteCourse } from "@/lib/api/endpoints/courses";
import { formatDeadline } from "@/lib/helpers/datetime";
import { downloadCsv } from "@/lib/helpers/download";
import { adminKeys, useAdminCourse } from "@/lib/hooks/use-admin";
import { AdminLoading, ADMIN_PRIMARY } from "./admin-ui";

/** Admin chỉ xem lớp học phần: buổi học, sinh viên, bảng điểm. Việc vận hành lớp do giảng viên chủ lớp làm; Admin chỉ còn quyền xoá lớp. */
export function AdminCourseDetail({ id }: { id: string }) {
  const query = useAdminCourse(id);
  const [tab, setTab] = useState<CourseTab>("sessions");
  const router = useRouter();
  const client = useQueryClient();
  useBreadcrumbLabels(query.data?.course_id ?? id, null);
  if (query.isPending) return <AdminLoading />;
  if (query.error || !query.data) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  const course = query.data;
  const detail = toCourseDetail(course);
  return <div className="space-y-6">
    <Link href="/admin/courses" className="inline-flex items-center gap-2 text-sm text-indigo-700 dark:text-indigo-300"><ArrowLeft className="size-4" />Lớp học phần</Link>
    <CourseHeaderCard course={detail} onDeleteCourse={async () => { await deleteCourse(course.course_id); await client.invalidateQueries({ queryKey: adminKeys.all }); toast.success("Đã xoá lớp học phần."); router.push("/admin/courses"); }} />
    <p className="text-sm text-muted-foreground">Người tạo: <strong>{course.teacher_name || course.created_by}</strong> · Học kỳ: {course.term} · Lớp học do giảng viên chủ lớp quản lý, Admin chỉ xem.</p>
    <CourseDetailTabs value={tab} onValueChange={setTab}
      sessions={<div className="space-y-4">
        {!course.sessions?.length ? <EmptyState title="Chưa có buổi học" description="Giảng viên chủ lớp chưa tạo buổi học nào." /> : [...course.sessions].sort((a, b) => a.order - b.order).map((session) =>
          <article key={session.id} className="rounded-xl border p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-2"><div className="flex flex-wrap items-center gap-2"><h2 className="text-lg font-semibold">Buổi {session.order}: {session.title}</h2>
                <span className="rounded-md bg-indigo-50 px-2 py-1 text-xs text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">{session.status === "open" ? "Đang mở" : session.status === "closed" ? "Đã đóng" : "Sắp mở"}</span></div>
                <p className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground"><CalendarDays className="size-4" />Hạn nộp: {formatDeadline(session.deadline)} · {session.problems.length} bài tập</p>
              </div>
              <Button asChild size="sm" className={`${ADMIN_PRIMARY} shrink-0`}><Link href={`/admin/courses/${encodeURIComponent(id)}/sessions/${session.id}`}>Xem buổi học</Link></Button>
            </div>
            {!!session.problems.length && <div className="mt-4 flex flex-wrap gap-2">{session.problems.map((problem) => <Link className="rounded-lg bg-muted px-3 py-2 text-xs hover:bg-indigo-50 dark:hover:bg-indigo-500/20" key={problem.id} href={`/admin/courses/${encodeURIComponent(id)}/sessions/${session.id}/problems/${problem.id}`}>{problem.report || `#${problem.id}`} · {problem.title}</Link>)}</div>}
          </article>)}
      </div>}
      students={<AdminCourseRoster id={id} />}
      grades={<CourseGradesTable readOnly courseId={id} rows={detail.grades ?? []} sessions={detail.sessions.map((session) => ({
        id: session.id, order: session.order, title: session.title, status: session.status,
        problems: session.problems.map((problem) => ({ id: problem.id, code: problem.report ?? `#${problem.id}`, title: problem.title })),
      }))} />}
    />
  </div>;
}

function AdminCourseRoster({ id }: { id: string }) {
  const query = useQuery({ queryKey: [...adminKeys.course(id), "enrollments"], queryFn: () => getAdminEnrollments(id) });
  const [search, setSearch] = useState("");
  const rows = (query.data ?? []).filter((student) => `${student.student_code ?? ""} ${student.full_name} ${student.email}`.toLowerCase().includes(search.trim().toLowerCase()));
  return <div className="space-y-4">
    <div className="flex flex-wrap gap-3">
      <div className="relative w-full min-w-0 sm:min-w-64 sm:flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tìm MSSV, tên hoặc email sinh viên..." aria-label="Tìm sinh viên trong lớp học phần" className="pl-9" /></div>
      <Button variant="outline" disabled={!rows.length} onClick={() => downloadCsv(`sinh-vien-${id}.csv`, [["MSSV", "Họ tên", "Email"], ...rows.map((student) => [student.student_code ?? "", student.full_name, student.email])])}><Download className="size-4" />Xuất danh sách</Button>
    </div>
    {query.isPending ? <p className="p-8 text-center text-sm text-muted-foreground">Đang tải danh sách...</p> : query.error ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : !rows.length ? <EmptyState icon={Users} title="Chưa có sinh viên phù hợp" /> :
      <div className="overflow-x-auto rounded-lg border"><Table className="min-w-[600px] w-full"><TableHeader><TableRow><TableHead className="whitespace-nowrap">MSSV</TableHead><TableHead className="whitespace-nowrap">Họ tên</TableHead><TableHead>Email</TableHead></TableRow></TableHeader><TableBody>{rows.map((student) =>
        <TableRow key={student.student_id}><TableCell className="whitespace-nowrap font-medium">{student.student_code || "—"}</TableCell><TableCell className="whitespace-nowrap">{student.full_name}</TableCell><TableCell className="break-all">{student.email}</TableCell></TableRow>)}</TableBody></Table></div>}
  </div>;
}
