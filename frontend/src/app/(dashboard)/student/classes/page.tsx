"use client";

import { CourseListView } from "@/components/shared/course-list-view";
import { useCourseList } from "@/lib/hooks/use-course-list";

// Sinh viên: trang chủ = danh sách lớp học phần. Page chỉ nối hook với component (mục 3.1).
export default function StudentHomePage() {
  const { filters, query } = useCourseList();

  return (
    <CourseListView
      role="student"
      filters={filters}
      courses={query.data?.items}
      stats={query.data?.stats}
      isLoading={query.isPending}
      isFetching={query.isFetching}
      error={query.error}
      onRetry={() => void query.refetch()}
      hrefFor={(course) => `/courses/${course.id}`} // TODO: trang chi tiết lớp của sinh viên chưa có thiết kế
    />
  );
}
