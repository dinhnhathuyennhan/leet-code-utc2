"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { getClassStudents, getClasses, getCourseById, getCourseEnrollments, getCourseTerms, getCourses, searchStudents } from "@/lib/api/endpoints/courses";
import type { CourseListParams } from "@/lib/types/course";

export const courseKeys = {
  all: ["courses"] as const,
  list: (params: CourseListParams) => [...courseKeys.all, "list", params] as const,
  terms: () => [...courseKeys.all, "terms"] as const,
  detail: (id: number | string) => [...courseKeys.all, "detail", id] as const,
  enrollments: (id: string) => [...courseKeys.all, "enrollments", id] as const,
  classes: () => [...courseKeys.all, "classes"] as const,
  classStudents: (id: string) => [...courseKeys.all, "class-students", id] as const,
  studentSearch: (email: string) => [...courseKeys.all, "student-search", email] as const,
};

/** keepPreviousData: đổi bộ lọc không làm lưới nhấp nháy về trạng thái loading. */
export function useCourses(params: CourseListParams) {
  return useQuery({
    queryKey: courseKeys.list(params),
    queryFn: () => getCourses(params),
    placeholderData: keepPreviousData,
  });
}

export function useCourseTerms() {
  return useQuery({ queryKey: courseKeys.terms(), queryFn: getCourseTerms });
}

export function useClasses(enabled = true) {
  return useQuery({ queryKey: courseKeys.classes(), queryFn: getClasses, enabled });
}

export function useClassStudents(classId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: courseKeys.classStudents(classId ?? ""),
    queryFn: () => getClassStudents(classId as string),
    enabled: enabled && Boolean(classId),
  });
}

export function useStudentSearch(email: string, enabled = true) {
  return useQuery({
    queryKey: courseKeys.studentSearch(email),
    queryFn: () => searchStudents({ email }),
    enabled: enabled && email.trim().length >= 2,
  });
}

export function useCourseEnrollments(courseId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: courseKeys.enrollments(courseId ?? ""),
    queryFn: () => getCourseEnrollments(courseId as string),
    enabled: enabled && Boolean(courseId),
  });
}

export function useCourse(id: number | string | undefined) {
  return useQuery({
    queryKey: courseKeys.detail(id ?? ""),
    queryFn: () => getCourseById(id as number | string),
    enabled: id !== undefined && id !== "",
  });
}
