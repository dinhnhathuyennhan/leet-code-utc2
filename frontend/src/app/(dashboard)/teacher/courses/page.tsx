"use client";

import { CourseListView } from "@/components/shared/course-list-view";
import { useCourseList } from "@/lib/hooks/use-course-list";
import { useQueryClient } from "@tanstack/react-query";
import { CourseCreateDialog } from "@/components/teacher/course-create-dialog";
import { useAuth } from "@/context/auth-context";

export default function TeacherCoursesPage() {
  const { filters, query } = useCourseList();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const courses = query.data?.items.map((course) => ({
    ...course,
    teacher_name: user?.full_name || "Giảng viên UTC2",
  }));
  return (
    <CourseListView
      role="teacher"
      filters={filters}
      courses={courses}
      stats={query.data?.stats}
      isLoading={query.isPending}
      isFetching={query.isFetching}
      error={query.error}
      onRetry={() => void query.refetch()}
      hrefFor={(course) => `/teacher/courses/${course.code || course.id}`}
      actions={
        <CourseCreateDialog
          onCreated={() =>
            void queryClient.invalidateQueries({ queryKey: ["courses"] })
          }
        />
      }
    />
  );
}
