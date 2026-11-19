"use client";

import { CourseListView } from "@/components/shared/course-list-view";
import { useAuth } from "@/context/auth-context";
import { useCourseList } from "@/lib/hooks/use-course-list";
import { useStudentOverview } from "@/lib/hooks/use-dashboard";

// Sinh viên: trang chủ = danh sách lớp đang học.
// Page chỉ nối hook với component (mục 3.1).
export default function StudentHomePage() {
  const { filters, query, courses } = useCourseList();
  const auth = useAuth();
  const overview = useStudentOverview(auth.status === "authenticated" ? auth.user.user_id : "");

  // "Hạn tuần này" lấy từ backend (số bài sắp hết hạn mà SV chưa làm đạt) để khớp
  // với Dashboard; số tự đếm ở FE chỉ đếm buổi học nên dễ lệch.
  const stats = query.data?.stats && overview.data
    ? { ...query.data.stats, due_this_week: overview.data.due_this_week }
    : undefined;

  return (
    <CourseListView
      role="student"
      filters={filters}
      courses={courses}
      stats={stats}
      isLoading={query.isPending}
      isFetching={query.isFetching}
      error={query.error}
      onRetry={() => void query.refetch()}
      // encodeURIComponent: mã lớp có thể chứa ký tự đặc biệt (#, ?, /, %, space) — không encode sẽ bị browser cắt tại # (anchor) → 404.
      hrefFor={(course) => `/student/classes/${encodeURIComponent(course.id)}`}
    />
  );
}
