"use client";

import { CourseListView } from "@/components/shared/course-list-view";
import { useCourseList } from "@/lib/hooks/use-course-list";
import { useQueryClient } from "@tanstack/react-query";
import { CourseCreateDialog } from "@/components/teacher/course-create-dialog";

export default function TeacherCoursesPage() {
  const { filters, query } = useCourseList();
  const queryClient = useQueryClient();

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
      hrefFor={(course) => `/teacher/courses/${course.code || course.id}`}
      actions={<CourseCreateDialog onCreated={() => void queryClient.invalidateQueries({ queryKey: ["courses"] })} />}
    />
  );
}
