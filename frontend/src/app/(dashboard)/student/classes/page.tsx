"use client";

import { CourseListView } from "@/components/shared/course-list-view";
import { useCourseList } from "@/lib/hooks/use-course-list";

// Sinh viên: trang chủ = danh sách lớp đang học.
// Page chỉ nối hook với component (mục 3.1).
export default function StudentHomePage() {
  const { filters, query, courses } = useCourseList();

  return (
    <CourseListView
      role="student"
      filters={filters}
      courses={courses}
      stats={query.data?.stats}
      isLoading={query.isPending}
      isFetching={query.isFetching}
      error={query.error}
      onRetry={() => void query.refetch()}
      // encodeURIComponent: mã lớp có thể chứa ký tự đặc biệt (#, ?, /, %, space) — không encode sẽ bị browser cắt tại # (anchor) → 404.
      hrefFor={(course) => `/student/classes/${encodeURIComponent(course.id)}`}
    />
  );
}
