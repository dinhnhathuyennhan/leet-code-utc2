"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import {
  getCourseById,
  getCourses,
  getCourseStudents,
} from "@/lib/api/endpoints/courses";
import type { CourseListParams } from "@/lib/types/course";

export const courseKeys = {
  all: ["courses"] as const,
  list: (params: CourseListParams) => [...courseKeys.all, "list", params] as const,
  detail: (id: number | string) => [...courseKeys.all, "detail", id] as const,
  students: (id: string) => [...courseKeys.all, "students", id] as const,
};

/**
 * keepPreviousData giúp đổi bộ lọc (khi BE có) không nhấp nháy skeleton.
 * Hiện tại BE chưa nhận filter → các tham số sẽ bị FastAPI bỏ qua; vẫn gọi để
 * khi BE bổ sung chỉ cần bật filter ngược, không phải sửa consumer.
 */
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

export function useCourseStudents(id: string | undefined) {
  return useQuery({
    queryKey: courseKeys.students(id ?? ""),
    queryFn: () => getCourseStudents(id as string),
    enabled: Boolean(id),
  });
}