"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import {
  getPendingSubmissions,
  getPlagiarismAlerts,
  getStudentOverview,
  getTeacherOverview,
} from "../api/endpoints/dashboard";
import type {
  PendingSubmissionParams,
  PendingSubmissionsResponse,
  PlagiarismAlert,
  StudentOverview,
  TeacherOverview,
} from "@/lib/types/dashboard";

export const dashboardKeys = {
  overview: ["dashboard", "teacher", "overview"] as const,
  student: (studentId: string) => ["dashboard", "student", studentId] as const,
  pending: (params: PendingSubmissionParams) => ["dashboard", "teacher", "pending", params] as const,
  plagiarism: ["dashboard", "teacher", "plagiarism"] as const,
};

export function useTeacherOverview() {
  return useQuery<TeacherOverview>({ queryKey: dashboardKeys.overview, queryFn: getTeacherOverview });
}

export function useStudentOverview(studentId: string | undefined) {
  return useQuery<StudentOverview>({
    queryKey: dashboardKeys.student(studentId ?? ""),
    queryFn: () => getStudentOverview(studentId as string),
    enabled: Boolean(studentId),
  });
}

export function usePendingSubmissions(params: PendingSubmissionParams) {
  return useQuery<PendingSubmissionsResponse>({
    queryKey: dashboardKeys.pending(params),
    queryFn: () => getPendingSubmissions(params),
    placeholderData: keepPreviousData,
  });
}

export function usePlagiarismAlerts() {
  return useQuery<PlagiarismAlert[]>({ queryKey: dashboardKeys.plagiarism, queryFn: getPlagiarismAlerts });
}
