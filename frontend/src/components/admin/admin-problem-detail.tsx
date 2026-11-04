"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { useBreadcrumbLabels } from "@/components/shared/breadcrumb-context";
import { ErrorState } from "@/components/shared/page-state";
import { Button } from "@/components/ui/button";
import { getAdminProblem, updateAdminProblem, uploadAdminTestcases } from "@/lib/api/endpoints/admin-management";
import { adminKeys } from "@/lib/hooks/use-admin";
import { AdminProblemEditor } from "./admin-problem-editor";
import { AdminHeading, AdminLoading } from "./admin-ui";

export function AdminProblemDetail({ courseId, lessonId, problemId }: { courseId: string; lessonId: string; problemId: string }) {
  const client = useQueryClient();
  const key = [...adminKeys.course(courseId), "lesson", lessonId, "problem", problemId];
  const query = useQuery({ queryKey: key, queryFn: () => getAdminProblem(courseId, lessonId, problemId) });
  useBreadcrumbLabels(courseId, `Buổi #${lessonId}`, query.data?.title ?? "Nội dung bài tập");
  if (query.isPending) return <AdminLoading />;
  if (query.error || !query.data) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  return <div className="space-y-6">
    <Link href={`/admin/courses/${encodeURIComponent(courseId)}/sessions/${lessonId}`} className="inline-flex items-center gap-2 text-sm text-indigo-700 dark:text-indigo-300"><ArrowLeft className="size-4" />Quay lại buổi học</Link>
    <AdminHeading title={query.data.title} description={`Bài tập #${problemId} · ${courseId}`}
      actions={<Button asChild variant="outline"><Link href={`/admin/submissions?${new URLSearchParams({ course: courseId, lesson_id: lessonId, problem_id: problemId })}`}>Xem bài nộp</Link></Button>} />
    <section className="rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
      <AdminProblemEditor key={query.dataUpdatedAt} problem={query.data}
        uploadTestcases={(file) => uploadAdminTestcases(courseId, lessonId, problemId, file)}
        onSave={async (payload) => {
          await updateAdminProblem(courseId, lessonId, problemId, payload);
          await client.invalidateQueries({ queryKey: adminKeys.all });
          toast.success("Đã lưu bài tập và testcase.");
        }} />
    </section>
  </div>;
}
