"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { getCourseById, getCourses } from "@/lib/api/endpoints/courses";
import type { CourseListParams } from "@/lib/types/course";

export const courseKeys = {
  all: ["courses"] as const,
  list: (params: CourseListParams) => [...courseKeys.all, "list", params] as const,
  detail: (id: number | string) => [...courseKeys.all, "detail", id] as const,
};

/** keepPreviousData: đổi bộ lọc không làm lưới nhấp nháy về trạng thái loading. */
export function useCourses(params: CourseListParams) {
  return useQuery({
    queryKey: courseKeys.list(params),
    queryFn: () => getCourses(params),
    placeholderData: keepPreviousData,
  });
}

export function useCourse(id: number | string | undefined) {
  return useQuery({
    queryKey: courseKeys.detail(id ?? ""),
    queryFn: () => getCourseById(id as number | string),
    enabled: id !== undefined && id !== "",
  });
}
