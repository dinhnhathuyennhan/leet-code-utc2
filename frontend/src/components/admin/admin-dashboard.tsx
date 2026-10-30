"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, BookOpen, FileCheck2, GraduationCap, Upload, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CourseGrid } from "@/components/shared/course-grid";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { getPendingSubmissions } from "@/lib/api/endpoints/dashboard";
import { toCourseSummary } from "@/lib/api/transformers/course";
import { adminKeys, useAdminAccountCount, useAdminClasses, useAdminCourses, useAdminProfile } from "@/lib/hooks/use-admin";
import { AdminHeading, AdminMetric, ADMIN_PRIMARY } from "./admin-ui";
import { AdminSubmissionTable } from "./admin-submissions";

export function AdminDashboard() {
  const courses = useAdminCourses();
  const classes = useAdminClasses();
  const profile = useAdminProfile();
  const accounts = useAdminAccountCount();
  const students = useAdminAccountCount(3);
  const teachers = useAdminAccountCount(2);
  const pending = useQuery({
    queryKey: [...adminKeys.submissions, "overview"],
    queryFn: () => getPendingSubmissions({ filter: "all", limit: 6 }),
  });
  const summaries = (courses.data ?? []).map(toCourseSummary);
  const activeCourses = courses.data ? summaries.filter((course) => course.status === "ongoing").length : undefined;

  return <div className="space-y-6">
    <AdminHeading title="Tổng quan quản trị" description="Theo dõi tài khoản, lớp học và các bài nộp cần xử lý trong toàn hệ thống."
      actions={<Button asChild className={ADMIN_PRIMARY}><Link href="/admin/accounts/import"><Upload className="size-4" />Nhập sinh viên từ Excel</Link></Button>} />
    <section className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#352078] via-indigo-600 to-sky-400 p-6 text-white sm:p-8">
      <div aria-hidden className="pointer-events-none absolute inset-y-0 left-1/2 w-20 -skew-x-12 bg-white/10" />
      <div className="relative flex flex-wrap items-center justify-between gap-6">
        <div className="space-y-2"><p className="text-sm text-white/80">UTC2 JUDGE MASTER · ADMIN</p>
          <h2 className="text-2xl font-bold sm:text-3xl">Chào mừng, {profile.data?.full_name || "Quản trị viên"}</h2>
          <p className="max-w-xl text-sm leading-6 text-white/85">Quản lý hoạt động đào tạo và hỗ trợ giảng viên, sinh viên từ một không gian chung.</p></div>
        <Button asChild variant="secondary"><Link href="/admin/courses">Quản lý lớp học phần<ArrowRight className="size-4" /></Link></Button>
      </div>
    </section>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <AdminMetric label="Tài khoản" value={accounts.data} icon={Users} detail={students.data !== undefined && teachers.data !== undefined ? `${students.data} sinh viên · ${teachers.data} giảng viên` : "Tổng tài khoản được cấp trong hệ thống"} />
      <AdminMetric label="Lớp học phần" value={courses.data?.length} icon={GraduationCap} detail={activeCourses === undefined ? "Đang tải số liệu" : `${activeCourses} lớp đang diễn ra`} />
      <AdminMetric label="Lớp hành chính" value={classes.data?.length} icon={BookOpen} detail="Danh mục lớp sinh hoạt của sinh viên" />
      <AdminMetric label="Bài cần xử lý" value={pending.data?.total} icon={FileCheck2} detail="Bài chờ chấm hoặc có lỗi chấm" />
    </div>
    {(accounts.error || students.error || teachers.error) && <ErrorState error={accounts.error || students.error || teachers.error} onRetry={() => { void accounts.refetch(); void students.refetch(); void teachers.refetch(); }} />}
    <section className="min-w-0 space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="font-bold">Bài nộp cần xử lý</h2><Link className="text-sm font-medium text-indigo-700 dark:text-indigo-300" href="/admin/submissions">Xem tất cả →</Link></div>
        {pending.isPending ? <p className="py-10 text-center text-sm text-muted-foreground">Đang tải bài nộp...</p> : pending.error ? <ErrorState error={pending.error} onRetry={() => void pending.refetch()} /> : pending.data?.items.length ? <AdminSubmissionTable rows={pending.data.items} /> : <EmptyState title="Không có bài nộp cần xử lý" description="Bài chờ chấm hoặc chấm lỗi sẽ hiển thị tại đây." />}
    </section>
    {classes.error && <ErrorState error={classes.error} onRetry={() => void classes.refetch()} />}
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3"><h2 className="font-bold">Lớp học phần trong hệ thống</h2><Link className="text-sm text-indigo-700 dark:text-indigo-300" href="/admin/courses">Xem tất cả →</Link></div>
      {courses.error ? <ErrorState error={courses.error} onRetry={() => void courses.refetch()} /> : courses.isPending ? <p className="py-8 text-sm text-muted-foreground">Đang tải lớp học phần...</p> : summaries.length ? <CourseGrid view="grid" courses={summaries.slice(0, 4)} hrefFor={(course) => `/admin/courses/${encodeURIComponent(course.code)}`} /> : <EmptyState title="Chưa có lớp học phần" description="Tạo lớp học phần đầu tiên để bắt đầu." />}
    </section>
  </div>;
}
