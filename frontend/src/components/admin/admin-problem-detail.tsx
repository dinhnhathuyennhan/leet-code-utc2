"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { useBreadcrumbLabels } from "@/components/shared/breadcrumb-context";
import { ErrorState } from "@/components/shared/page-state";
import { getAdminProblem } from "@/lib/api/endpoints/admin-management";
import { adminKeys } from "@/lib/hooks/use-admin";
import { AdminProblemPreview } from "./admin-problem-preview";
import { AdminHeading, AdminLoading } from "./admin-ui";

/** Admin chỉ xem bài tập trong buổi học; sửa bài và testcase do giảng viên chủ lớp làm. */
export function AdminProblemDetail({ courseId, lessonId, problemId }: { courseId: string; lessonId: string; problemId: string }) {
  const key = [...adminKeys.course(courseId), "lesson", lessonId, "problem", problemId];
  const query = useQuery({ queryKey: key, queryFn: () => getAdminProblem(courseId, lessonId, problemId) });
  useBreadcrumbLabels(courseId, `Buổi #${lessonId}`, query.data?.title ?? "Nội dung bài tập");
  if (query.isPending) return <AdminLoading />;
  if (query.error || !query.data) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  return <div className="space-y-6">
    <Link href={`/admin/courses/${encodeURIComponent(courseId)}/sessions/${lessonId}`} className="inline-flex items-center gap-2 text-sm text-indigo-700 dark:text-indigo-300"><ArrowLeft className="size-4" />Quay lại buổi học</Link>
    <AdminHeading title={query.data.title} description={`Bài tập #${problemId} · ${courseId} · Chỉ xem, bài tập trong buổi học do giảng viên chủ lớp quản lý.`} />
    <section className="rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
      <AdminProblemPreview key={query.dataUpdatedAt} problem={query.data} />
    </section>
  </div>;
}
