"use client";

import { CourseListView } from "@/components/shared/course-list-view";
import { useCourseList } from "@/lib/hooks/use-course-list";

// Sinh viên: trang chủ = danh sách lớp đang học.
// Page chỉ nối hook với component (mục 3.1).
export default function StudentHomePage() {
  const { filters, query } = useCourseList();

  return (
    <CourseListView
      role="student"
      filters={filters}
      courses={query.data?.items}
      isLoading={query.isPending}
      isFetching={query.isFetching}
      error={query.error}
      onRetry={() => void query.refetch()}
      hrefFor={(course) => `/student/classes/${course.id}`}
    />
  );
}