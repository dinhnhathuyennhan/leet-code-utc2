"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { SearchX } from "lucide-react";

import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { CourseDetailSkeleton } from "@/components/teacher/course-detail-skeleton";
import { StudentCourseDetailTabs, type StudentCourseTab } from "@/components/student/course-detail-tabs";
import { StudentCourseHeaderCard } from "@/components/student/course-header-card";
import { StudentCourseInfoPanel } from "@/components/student/course-info-panel";
import { StudentRosterTable } from "@/components/student/student-roster-table";
import { ApiError } from "@/lib/api/error";
import { useCourse, useCourseStudents } from "@/lib/hooks/use-courses";

export default function StudentCourseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const courseId = typeof id === "string" ? id : Array.isArray(id) ? id[0] : undefined;

  const courseQuery = useCourse(courseId);
  const studentsQuery = useCourseStudents(courseId);
  const [tab, setTab] = useState<StudentCourseTab>("info");

  // Ưu tiên course_id từ URL làm nhãn dự phòng.
  // Khi data về, dùng `code` (alias của course_id từ BE) — vẫn là "CS101".
  useBreadcrumbLabel(courseQuery.data?.code ?? courseId);

  if (courseQuery.isPending) return <CourseDetailSkeleton />;

  if (courseQuery.error || !courseQuery.data) {
    // Gộp 403 + 404: cả hai đều hiện EmptyState (mô tả đã nói "không tồn tại hoặc bạn không có quyền xem").
    // Không hiện nút "Thử lại" với 403/404 vì retry không có tác dụng.
    if (
      courseQuery.error instanceof ApiError &&
      (courseQuery.error.status === 404 || courseQuery.error.status === 403)
    ) {
      return (
        <EmptyState
          icon={SearchX}
          title="Không tìm thấy lớp học phần"
          description="Lớp này không tồn tại hoặc bạn không có quyền xem."
        />
      );
    }
    return <ErrorState error={courseQuery.error} onRetry={() => void courseQuery.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <StudentCourseHeaderCard course={courseQuery.data} />
      <StudentCourseDetailTabs
        value={tab}
        onValueChange={setTab}
        info={<StudentCourseInfoPanel courseId={courseId ?? ""} />}
        roster={
          <StudentRosterTable
            students={studentsQuery.data}
            isLoading={studentsQuery.isPending}
            error={studentsQuery.error}
            onRetry={() => void studentsQuery.refetch()}
          />
        }
      />
    </div>
  );
}