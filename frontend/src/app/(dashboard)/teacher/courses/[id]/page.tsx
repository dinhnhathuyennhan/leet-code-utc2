"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { CalendarPlus, SearchX } from "lucide-react";

import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { CourseDetailSkeleton } from "@/components/teacher/course-detail-skeleton";
import { CourseDetailTabs, type CourseTab } from "@/components/teacher/course-detail-tabs";
import { ApiError } from "@/lib/api/error";
import { useCourse } from "@/lib/hooks/use-courses";
import { CourseHeaderCard } from "@/components/teacher/course-header-card";

export default function TeacherCourseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: course, isPending, error, refetch } = useCourse(id);
  const [tab, setTab] = useState<CourseTab>("sessions");

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
      <CourseHeaderCard course={course} />
      <CourseDetailTabs
        value={tab}
        onValueChange={setTab}
        sessions={<EmptyState icon={CalendarPlus} title="Chưa có buổi học nào" description="Tính năng buổi học sẽ đến ở Phase 2." />}
        students={<EmptyState icon={CalendarPlus} title="Danh sách sinh viên" description="Tính năng sẽ đến ở Phase 1." />}
      />
    </div>
  );
}