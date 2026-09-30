"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import {
  getPendingSubmissions,
  getPlagiarismAlerts,
  getTeacherOverview,
} from "../api/endpoints/dashboard";
import type {
  PendingSubmissionParams,
  PendingSubmissionsResponse,
  PlagiarismAlert,
  TeacherOverview,
} from "@/lib/types/dashboard";

export const dashboardKeys = {
  overview: ["dashboard", "teacher", "overview"] as const,
  pending: (params: PendingSubmissionParams) => ["dashboard", "teacher", "pending", params] as const,
  plagiarism: ["dashboard", "teacher", "plagiarism"] as const,
};

export function useTeacherOverview() {
  return useQuery<TeacherOverview>({ queryKey: dashboardKeys.overview, queryFn: getTeacherOverview });
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
