"use client";

import { CourseListView } from "@/components/shared/course-list-view";
import { useCourseList } from "@/lib/hooks/use-course-list";

export default function TeacherCoursesPage() {
  const { filters, query } = useCourseList();

  return (
    <CourseListView
      role="teacher"
      filters={filters}
      courses={query.data?.items}
      stats={query.data?.stats}
      isLoading={query.isPending}
      isFetching={query.isFetching}
      error={query.error}
      onRetry={() => void query.refetch()}
      hrefFor={(course) => `/teacher/courses/${course.id}`}
    />
  );
}
