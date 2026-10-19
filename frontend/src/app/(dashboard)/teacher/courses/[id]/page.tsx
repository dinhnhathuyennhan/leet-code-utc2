"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { SearchX } from "lucide-react";

import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
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
  const { data: course, dataUpdatedAt, isPending, error, refetch } = useCourse(id);
  const enrollments = useCourseEnrollments(course?.code);
  const [tab, setTab] = useState<CourseTab>("sessions");
  const [editorOpen, setEditorOpen] = useState(false);
  const [courseEditorOpen, setCourseEditorOpen] = useState(false);

  useBreadcrumbLabel(course?.code); // breadcrumb: Lớp học phần / <code>

  if (isPending) return <CourseDetailSkeleton />;

  if (error || !course) {
    if (error instanceof ApiError && error.status === 404) {
      return <EmptyState icon={SearchX} title="Không tìm thấy lớp học phần" description="Lớp này không tồn tại hoặc bạn không có quyền xem." />;
    }
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }

  return (
    <div className="space-y-6">
      <CourseHeaderCard course={{ ...course, updated_at: course.updated_at || (dataUpdatedAt ? new Date(dataUpdatedAt).toISOString() : null) }} onCreateSession={() => setEditorOpen(true)} onEditCourse={() => setCourseEditorOpen(true)} />
      <CourseDetailTabs
        value={tab}
        onValueChange={setTab}
        sessions={
          <SessionList sessions={course.sessions} studentCount={course.student_count} courseId={course.code || id} />
        }
        students={enrollments.isPending ? <CourseDetailSkeleton /> : enrollments.error ? <ErrorState error={enrollments.error} onRetry={() => void enrollments.refetch()} /> : <CourseStudentsTable students={enrollments.data ?? []} courseId={course.code} onChanged={() => void enrollments.refetch()} />}
        grades={<CourseGradesTable onUpdated={() => void refetch()} sessions={course.sessions.map((session) => ({ id: session.id, order: session.order, title: session.title, status: session.status, problems: session.problems.map((problem) => ({ id: problem.id, code: problem.report ?? problem.title, title: problem.title })) }))} rows={course.grades ?? []} />}
      />
      <SessionEditorDialog key={`${editorOpen}-new`} course={course} session={null} open={editorOpen} onOpenChange={setEditorOpen} onSaved={() => void refetch()} />
      <CourseEditDialog key={`${courseEditorOpen}-${dataUpdatedAt}`} course={course} open={courseEditorOpen} onOpenChange={setCourseEditorOpen} onSaved={() => void refetch()} />
    </div>
  );
}
