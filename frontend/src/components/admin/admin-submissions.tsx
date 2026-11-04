"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Download, FileCheck2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { getPendingSubmissions } from "@/lib/api/endpoints/dashboard";
import { downloadCsv } from "@/lib/helpers/download";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import { adminKeys, useAdminCourses } from "@/lib/hooks/use-admin";
import type { PendingFilter, PendingSubmission } from "@/lib/types/dashboard";
import { AdminHeading, AdminMetric, ADMIN_PRIMARY, ADMIN_SELECT } from "./admin-ui";

export function AdminSubmissionTable({ rows }: { rows: PendingSubmission[] }) {
  return <Table className="min-w-[740px]"><TableHeader><TableRow className="bg-[#352078] hover:bg-[#352078]">
    {["Sinh viên", "Lớp / Buổi học", "Trạng thái", "Bài tập", "Thao tác"].map((label) => <TableHead key={label} className="text-white">{label}</TableHead>)}
  </TableRow></TableHeader><TableBody>{rows.map((row) => <TableRow key={row.id}>
    <TableCell><p className="font-semibold">{row.student_name}</p><p className="text-xs text-muted-foreground">{row.student_code}</p></TableCell>
    <TableCell><Link className="font-medium text-indigo-700 dark:text-indigo-300" href={`/admin/courses/${encodeURIComponent(row.course_id)}`}>{row.course_code}</Link><p className="mt-1 text-xs text-muted-foreground">{row.session_label}</p></TableCell>
    <TableCell><span className={`inline-block rounded-md px-2 py-1 text-xs font-medium ${row.judge_kind === "graded" ? "bg-emerald-100 text-emerald-800" : row.judge_kind === "compile_error" ? "bg-rose-100 text-rose-800" : "bg-amber-100 text-amber-800"}`}>{row.judge_label}</span></TableCell>
    <TableCell className="max-w-xs"><p className="font-medium">{row.topic}</p><p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{row.judge_kind === "graded" ? "Bài nộp đã được chấp nhận." : row.issue}</p></TableCell>
    <TableCell><Button asChild size="sm" className={ADMIN_PRIMARY}><Link href={`/admin/submissions/${row.id}`}>Xem & đánh giá</Link></Button></TableCell>
  </TableRow>)}</TableBody></Table>;
}

export function AdminSubmissions() {
  const params = useSearchParams();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<PendingFilter>("all");
  const [course, setCourse] = useState(params.get("course") ?? "");
  const [page, setPage] = useState(1);
  const debounced = useDebouncedValue(search, 300);
  const courses = useAdminCourses();
  const lesson = params.get("lesson_id");
  const problem = params.get("problem_id");
  const query = useQuery({
    queryKey: [...adminKeys.submissions, "list", filter, debounced, course, lesson, problem],
    queryFn: () => getPendingSubmissions({
      filter, search: debounced.trim() || undefined, course: course || undefined, limit: 500, include_graded: true,
      lesson_id: lesson ? Number(lesson) : undefined, problem_id: problem ? Number(problem) : undefined,
    }),
  });
  const data = query.data;
  const rows = data?.items ?? [];
  const pages = Math.max(1, Math.ceil(rows.length / 20));
  const currentPage = Math.min(page, pages);
  const visible = rows.slice((currentPage - 1) * 20, currentPage * 20);

  return <div className="space-y-6">
    <AdminHeading title="Quản lý bài nộp" description="Theo dõi và đánh giá bài nộp của sinh viên trên toàn bộ lớp học phần."
      actions={<Button variant="outline" disabled={!rows.length} onClick={() => downloadCsv("bai-nop.csv", [["Mã bài nộp", "MSSV", "Họ tên", "Lớp", "Buổi", "Bài tập", "Trạng thái"], ...rows.map((row) => [row.id, row.student_code, row.student_name, row.course_code, row.session_label, row.topic, row.judge_label])])}><Download className="size-4" />Xuất kết quả đang lọc</Button>} />
    <div className="grid gap-4 sm:grid-cols-3">
      <AdminMetric label="Tổng bài nộp khớp tìm kiếm" value={data?.counts.all} icon={FileCheck2} />
      <AdminMetric label="Đã chấp nhận" value={data?.counts.graded} icon={FileCheck2} />
      <AdminMetric label="Lỗi biên dịch" value={data?.counts.error} icon={FileCheck2} />
    </div>
    <section className="overflow-hidden rounded-2xl border bg-card shadow-sm">
      <div className="space-y-4 p-4 sm:p-5">
        <div className="flex flex-wrap gap-3"><div className="relative w-full min-w-0 sm:min-w-64 sm:flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} className="w-full pl-9" placeholder="Tìm MSSV, tên sinh viên, lớp hoặc bài tập..." aria-label="Tìm bài nộp" /></div>
          <select className={`${ADMIN_SELECT} max-w-full`} aria-label="Lọc lớp học phần" value={course} onChange={(event) => { setCourse(event.target.value); setPage(1); }}><option value="">Tất cả lớp học phần</option>{courses.data?.map((item) => <option key={item.course_id} value={item.course_id}>{item.course_id} — {item.course_name}</option>)}</select>
        </div>
        <div className="flex flex-wrap gap-2" aria-label="Lọc trạng thái bài nộp">{[
          { value: "all", label: "Tất cả" }, { value: "graded", label: "Đã chấp nhận" }, { value: "error", label: "Lỗi biên dịch" },
        ].map((item) => <Button key={item.value} size="sm" variant={filter === item.value ? "secondary" : "ghost"} aria-pressed={filter === item.value} onClick={() => { setFilter(item.value as PendingFilter); setPage(1); }}>{item.label}</Button>)}</div>
        {(lesson || problem) && <p className="text-xs text-muted-foreground">Đang lọc theo {lesson && `buổi học #${lesson}`} {problem && `bài tập #${problem}`}. <Link href="/admin/submissions" className="text-indigo-700 underline dark:text-indigo-300">Bỏ bộ lọc buổi/bài</Link></p>}
      </div>
      {query.isPending ? <p aria-busy="true" className="p-10 text-center text-sm text-muted-foreground">Đang tải bài nộp...</p> : query.error ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : rows.length ? <AdminSubmissionTable rows={visible} /> : <EmptyState title="Chưa có bài nộp phù hợp" description="Thử đổi từ khóa hoặc bộ lọc." />}
      {data && <div className="flex flex-wrap items-center justify-between gap-3 border-t p-4 text-sm text-muted-foreground"><p>Hiển thị {visible.length} / {data.total} bài nộp.{data.total > rows.length && " Đang tải tối đa 500 bài; hãy thu hẹp bộ lọc."}</p>
        <div className="flex items-center gap-2"><Button variant="outline" size="sm" disabled={currentPage <= 1} onClick={() => setPage(currentPage - 1)}>Trước</Button><span>{currentPage} / {pages}</span><Button variant="outline" size="sm" disabled={currentPage >= pages} onClick={() => setPage(currentPage + 1)}>Sau</Button></div></div>}
    </section>
  </div>;
}
