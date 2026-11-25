"use client";

import { useState } from "react";
import { BookOpen, CalendarDays, GraduationCap, LayoutGrid, List, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CourseGrid } from "@/components/shared/course-grid";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { toCourseSummary } from "@/lib/api/transformers/course";
import { useAdminCourses } from "@/lib/hooks/use-admin";
import type { CourseView } from "@/lib/types/course";
import { AdminHeading, AdminLoading, AdminMetric, ADMIN_SELECT } from "./admin-ui";

export function AdminCourses() {
  const query = useAdminCourses();
  const [search, setSearch] = useState("");
  const [term, setTerm] = useState("");
  const [view, setView] = useState<CourseView>("grid");
  const records = query.data ?? [];
  const courses = records.map(toCourseSummary);
  const normalized = search.trim().toLowerCase();
  const visible = courses.filter((course, index) => (!term || records[index].term === term) && `${course.code} ${course.name} ${course.teacher_name}`.toLowerCase().includes(normalized));

  return <div className="space-y-6">
    <AdminHeading title="Lớp học phần" description="Xem toàn bộ lớp học phần, buổi học, sinh viên và bảng điểm. Lớp do giảng viên chủ lớp tạo và quản lý." />
    <div className="grid gap-4 sm:grid-cols-3">
      <AdminMetric label="Tổng lớp học phần" value={query.data?.length} icon={GraduationCap} />
      <AdminMetric label="Đang diễn ra" value={query.data ? courses.filter((course) => course.status === "ongoing").length : undefined} icon={CalendarDays} />
      <AdminMetric label="Buổi học" value={query.data?.reduce((sum, course) => sum + (course.sessions?.length ?? 0), 0)} icon={BookOpen} />
    </div>
    <section className="flex flex-wrap items-center gap-3 rounded-xl border bg-card p-4">
      <div className="relative w-full min-w-0 sm:min-w-64 sm:flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tìm mã lớp, tên lớp hoặc người tạo..." aria-label="Tìm lớp học phần" className="w-full pl-9" /></div>
      <select aria-label="Lọc theo học kỳ" className={`${ADMIN_SELECT} min-w-0 max-w-full flex-1 sm:flex-none`} value={term} onChange={(event) => setTerm(event.target.value)}><option value="">Tất cả học kỳ</option>{[...new Set(records.map((course) => course.term))].map((value) => <option key={value}>{value}</option>)}</select>
      <div className="flex gap-1" aria-label="Kiểu hiển thị">{(["grid", "list"] as const).map((item) => <Button key={item} variant={view === item ? "secondary" : "ghost"} size="icon" aria-label={item === "grid" ? "Dạng lưới" : "Dạng danh sách"} aria-pressed={view === item} onClick={() => setView(item)}>{item === "grid" ? <LayoutGrid className="size-4" /> : <List className="size-4" />}</Button>)}</div>
    </section>
    {query.isPending ? <AdminLoading /> : query.error ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : !visible.length ? <EmptyState icon={GraduationCap} title={records.length ? "Không tìm thấy lớp phù hợp" : "Chưa có lớp học phần"} description={records.length ? "Thử thay đổi từ khoá hoặc bộ lọc." : "Giảng viên chưa tạo lớp học phần nào."} /> : <CourseGrid view={view} courses={visible} hrefFor={(course) => `/admin/courses/${encodeURIComponent(course.code)}`} />}
  </div>;
}
