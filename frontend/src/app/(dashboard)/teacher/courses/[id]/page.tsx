"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { SearchX } from "lucide-react";

import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { CourseDetailSkeleton } from "@/components/teacher/course-detail-skeleton";
import { CourseDetailTabs, type CourseTab } from "@/components/teacher/course-detail-tabs";
import { ApiError } from "@/lib/api/error";
import { formatUpdatedAt } from "@/lib/helpers/format";
import { useCourse, useCourseEnrollments } from "@/lib/hooks/use-courses";
import { CourseHeaderCard } from "@/components/teacher/course-header-card";
import { CourseStudentsTable } from "@/components/teacher/course-students-table";
import { CourseGradesTable } from "@/components/teacher/course-grades-table";
import { SessionEditorDialog } from "@/components/teacher/session-editor-dialog";
import { SessionList } from "@/components/teacher/session-list";

export default function TeacherCourseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: course, isPending, error, refetch } = useCourse(id);
  const enrollments = useCourseEnrollments(course?.code);
  const [tab, setTab] = useState<CourseTab>("sessions");
  const [editorOpen, setEditorOpen] = useState(false);

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
      <CourseHeaderCard course={course} onCreateSession={() => setEditorOpen(true)} />
      <CourseDetailTabs
        value={tab}
        onValueChange={setTab}
        updatedAtLabel={formatUpdatedAt(course.updated_at)}
        sessions={
          <SessionList sessions={course.sessions} studentCount={course.student_count} courseId={course.code || id} onViewResults={() => setTab("grades")} />
        }
        students={enrollments.isPending ? <CourseDetailSkeleton /> : enrollments.error ? <ErrorState error={enrollments.error} onRetry={() => void enrollments.refetch()} /> : <CourseStudentsTable students={enrollments.data ?? []} courseId={course.code} onChanged={() => void enrollments.refetch()} />}
        grades={<CourseGradesTable sessions={course.sessions.map((session) => ({ id: session.id, order: session.order, title: session.title, status: session.status, problems: session.problems.map((problem) => ({ id: problem.id, code: problem.report ?? problem.title, title: problem.title })) }))} rows={course.grades ?? (enrollments.data ?? []).map((student) => ({ student_id: student.student_id, full_name: student.full_name, class_id: student.class_id ?? null, problem_scores: [], overall_score: null, session_scores: {} }))} />}
      />
      <SessionEditorDialog key={`${editorOpen}-new`} course={course} session={null} open={editorOpen} onOpenChange={setEditorOpen} onSaved={() => void refetch()} />
    </div>
  );
}