"use client";

import { useState } from "react";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { ErrorState, ForbiddenState, NotFoundState } from "@/components/shared/page-state";
import { CourseDetailSkeleton } from "@/components/teacher/course-detail-skeleton";
import { CourseDetailTabs, type CourseTab } from "@/components/teacher/course-detail-tabs";
import { ApiError } from "@/lib/api/error";
import { useCourse, useCourseEnrollments } from "@/lib/hooks/use-courses";
import { CourseHeaderCard } from "@/components/teacher/course-header-card";
import { CourseStudentsTable } from "@/components/teacher/course-students-table";
import { CourseGradesTable } from "@/components/teacher/course-grades-table";
import { SessionEditorDialog } from "@/components/teacher/session-editor-dialog";
import { CourseEditDialog } from "@/components/teacher/course-edit-dialog";
import { SessionList } from "@/components/teacher/session-list";

export default function TeacherCourseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialTab = searchParams.get("tab");
  const { data: course, dataUpdatedAt, isPending, error, refetch } = useCourse(id);
  const [tab, setTab] = useState<CourseTab>(initialTab === "students" || initialTab === "grades" ? initialTab : "sessions");
  const enrollments = useCourseEnrollments(course?.code, tab === "students");
  const [editorOpen, setEditorOpen] = useState(false);
  const [courseEditorOpen, setCourseEditorOpen] = useState(false);

  useBreadcrumbLabel(course?.code); // breadcrumb: Lớp học phần / <code>

  if (isPending) return <CourseDetailSkeleton />;

  if (error || !course) {
    if (error instanceof ApiError && error.status === 404) {
      return <NotFoundState description="Lớp học phần không tồn tại hoặc đã được thay đổi." />;
    }
    if (error instanceof ApiError && error.status === 403) return <ForbiddenState />;
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }

  return (
    <div className="space-y-6">
      <CourseHeaderCard course={{ ...course, updated_at: course.updated_at || (dataUpdatedAt ? new Date(dataUpdatedAt).toISOString() : null) }} onCreateSession={() => setEditorOpen(true)} onEditCourse={() => setCourseEditorOpen(true)} />
      <CourseDetailTabs
        value={tab}
        onValueChange={(next) => { setTab(next); router.replace(`${pathname}?tab=${next}`, { scroll: false }); }}
        sessions={
          <SessionList key={course.sessions.map((session) => `${session.id}:${session.order}`).join(",")} sessions={course.sessions} studentCount={course.student_count} courseId={course.code || id} onChanged={() => void refetch()} />
        }
        students={enrollments.isPending ? <CourseDetailSkeleton /> : enrollments.error ? <ErrorState error={enrollments.error} onRetry={() => void enrollments.refetch()} /> : <CourseStudentsTable students={enrollments.data ?? []} courseId={course.code} onChanged={() => void enrollments.refetch()} />}
        grades={<CourseGradesTable onUpdated={() => void refetch()} sessions={course.sessions.map((session) => ({ id: session.id, order: session.order, title: session.title, status: session.status, problems: session.problems.map((problem) => ({ id: problem.id, code: problem.report ?? problem.title, title: problem.title })) }))} rows={course.grades ?? []} />}
      />
      <SessionEditorDialog key={`${editorOpen}-new`} course={course} session={null} open={editorOpen} onOpenChange={setEditorOpen} onSaved={() => void refetch()} />
      <CourseEditDialog key={`${courseEditorOpen}-${dataUpdatedAt}`} course={course} open={courseEditorOpen} onOpenChange={setCourseEditorOpen} onSaved={() => void refetch()} />
    </div>
  );
}
