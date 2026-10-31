"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { BookOpen, CalendarDays, GraduationCap, LayoutGrid, List, Plus, Search } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CourseGrid } from "@/components/shared/course-grid";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { saveAdminCourse } from "@/lib/api/endpoints/admin-management";
import { toCourseSummary } from "@/lib/api/transformers/course";
import { COURSE_COVERS } from "@/lib/constants/course-covers";
import { fromDateInput, toDateInput } from "@/lib/helpers/datetime";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { adminKeys, useAdminCourses } from "@/lib/hooks/use-admin";
import type { AdminCourse } from "@/lib/types/admin";
import type { CourseView } from "@/lib/types/course";
import { AdminDialog, AdminHeading, AdminLoading, AdminMetric, ADMIN_PRIMARY, ADMIN_SELECT } from "./admin-ui";

export function AdminCourseForm({ course, onClose }: { course?: AdminCourse; onClose: () => void }) {
  const client = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    course_id: course?.course_id ?? "", course_name: course?.course_name ?? "", term: course?.term ?? "",
    start_date: course ? toDateInput(course.start_date) : "", end_date: course ? toDateInput(course.end_date) : "",
    avt_link: course?.avt_link ?? COURSE_COVERS.java,
  });
  function set(key: keyof typeof form, value: string) { setForm((current) => ({ ...current, [key]: value })); }
  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    if (!form.course_id.trim() || !form.course_name.trim() || !form.term.trim()) { toast.error("Vui lòng nhập mã lớp, tên lớp và học kỳ."); return; }
    if (!form.start_date || !form.end_date || form.start_date > form.end_date) { toast.error("Ngày kết thúc phải từ ngày bắt đầu trở đi."); return; }
    setBusy(true);
    try {
      await saveAdminCourse({
        course_id: form.course_id.trim(), course_name: form.course_name.trim(), term: form.term.trim(), avt_link: form.avt_link,
        start_date: fromDateInput(form.start_date), end_date: fromDateInput(form.end_date, "23:59:59"),
      }, course?.course_id);
      void client.invalidateQueries({ queryKey: adminKeys.all });
      toast.success(course ? "Đã cập nhật lớp học phần." : "Đã tạo lớp học phần.");
      onClose();
    } catch (error) { toast.error(getErrorMessage(error)); } finally { setBusy(false); }
  }
  return <AdminDialog open title={course ? "Chỉnh sửa lớp học phần" : "Tạo lớp học phần"} description="Thông tin lớp được lưu trực tiếp vào hệ thống." onClose={onClose} busy={busy}>
    <form onSubmit={(event) => void save(event)} className="space-y-5">
      <fieldset disabled={busy} className="grid gap-4 sm:grid-cols-2">
        <label className="space-y-2 text-sm font-medium">Mã lớp<Input value={form.course_id} onChange={(event) => set("course_id", event.target.value)} disabled={Boolean(course)} required maxLength={50} /></label>
        <label className="space-y-2 text-sm font-medium">Tên lớp học phần<Input value={form.course_name} onChange={(event) => set("course_name", event.target.value)} required maxLength={255} /></label>
        <label className="space-y-2 text-sm font-medium">Học kỳ / năm học<Input value={form.term} placeholder="HK1 2026-2027" onChange={(event) => set("term", event.target.value)} required maxLength={255} /></label>
        <label className="space-y-2 text-sm font-medium">Ảnh bìa<select className={`${ADMIN_SELECT} w-full`} value={form.avt_link} onChange={(event) => set("avt_link", event.target.value)}>
          {!Object.values(COURSE_COVERS).includes(form.avt_link) && <option value={form.avt_link}>Ảnh hiện tại</option>}
          {Object.entries(COURSE_COVERS).map(([language, path]) => <option key={language} value={path}>{language.toUpperCase()}</option>)}
        </select></label>
        <label className="space-y-2 text-sm font-medium">Ngày bắt đầu<Input type="date" value={form.start_date} onChange={(event) => set("start_date", event.target.value)} required /></label>
        <label className="space-y-2 text-sm font-medium">Ngày kết thúc<Input type="date" value={form.end_date} min={form.start_date} onChange={(event) => set("end_date", event.target.value)} required /></label>
      </fieldset>
      {course && <p className="text-xs text-muted-foreground">Người tạo: {course.created_by}. Mã lớp và người tạo được giữ theo dữ liệu gốc.</p>}
      <div className="flex justify-end gap-2"><Button type="button" variant="outline" disabled={busy} onClick={onClose}>Hủy</Button><Button type="submit" disabled={busy} className={ADMIN_PRIMARY}>{busy ? "Đang lưu..." : "Lưu lớp học phần"}</Button></div>
    </form>
  </AdminDialog>;
}

export function AdminCourses() {
  const query = useAdminCourses();
  const [search, setSearch] = useState("");
  const [term, setTerm] = useState("");
  const [view, setView] = useState<CourseView>("grid");
  const [creating, setCreating] = useState(false);
  const records = query.data ?? [];
  const courses = records.map(toCourseSummary);
  const normalized = search.trim().toLowerCase();
  const visible = courses.filter((course, index) => (!term || records[index].term === term) && `${course.code} ${course.name} ${course.teacher_name}`.toLowerCase().includes(normalized));

  return <div className="space-y-6">
    <AdminHeading title="Lớp học phần" description="Quản lý toàn bộ lớp học phần, buổi học, sinh viên và bảng điểm."
      actions={<Button className={ADMIN_PRIMARY} onClick={() => setCreating(true)}><Plus className="size-4" />Tạo lớp học phần</Button>} />
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
    {query.isPending ? <AdminLoading /> : query.error ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : !visible.length ? <EmptyState icon={GraduationCap} title={records.length ? "Không tìm thấy lớp phù hợp" : "Chưa có lớp học phần"} description="Tạo lớp mới hoặc thay đổi bộ lọc." /> : <CourseGrid view={view} courses={visible} hrefFor={(course) => `/admin/courses/${encodeURIComponent(course.code)}`} />}
    {creating && <AdminCourseForm onClose={() => setCreating(false)} />}
  </div>;
}
