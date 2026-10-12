"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import {
  getCourseById,
  getCourses,
  getCourseStudents,
  getStudentCourses,
  getStudentEnrollments,
  type StudentEnrollmentItem,
} from "@/lib/api/endpoints/courses";
import type { CourseListParams, CourseSummary } from "@/lib/types/course";

export const courseKeys = {
  all: ["courses"] as const,
  list: (params: CourseListParams) => [...courseKeys.all, "list", params] as const,
  detail: (id: number | string) => [...courseKeys.all, "detail", id] as const,
  students: (id: string) => [...courseKeys.all, "students", id] as const,
  studentCourses: (id: string) =>
    [...courseKeys.all, "student-courses", id] as const,
  studentEnrollments: (id: string) =>
    [...courseKeys.all, "student-enrollments", id] as const,
};

/**
 * `keepPreviousData` giúp đổi filter (term/search) không nhấp nháy skeleton.
 *
 * Từ Lỗi 4: BE `GET /courses` đã nhận query param `term` (LIKE %term%)
 * và `search` (LIKE %search% trên course_id/course_name).
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

/** Hook cho Lỗi 7 — lấy danh sách lớp của 1 sinh viên. */
export function useStudentCourses(studentId: string | undefined) {
  return useQuery<CourseSummary[]>({
    queryKey: courseKeys.studentCourses(studentId ?? ""),
    queryFn: () => getStudentCourses(studentId as string),
    enabled: Boolean(studentId),
  });
}

/** Hook cho Lỗi 8 — lấy danh sách enrollment (kèm info lớp) của 1 sinh viên. */
export function useStudentEnrollments(studentId: string | undefined) {
  return useQuery<StudentEnrollmentItem[]>({
    queryKey: courseKeys.studentEnrollments(studentId ?? ""),
    queryFn: () => getStudentEnrollments(studentId as string),
    enabled: Boolean(studentId),
  });
}
