import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type {
  PendingSubmissionParams,
  PendingSubmissionsResponse,
  PlagiarismAlert,
  TeacherOverview,
} from "@/lib/dashboard";

// Dashboard endpoints are kept together so query hooks share one typed API contract.

export async function getTeacherOverview(): Promise<TeacherOverview> {
  try {
    const response = await axiosInstance.get<TeacherOverview>("/teacher/dashboard/overview");
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getPendingSubmissions(params: PendingSubmissionParams): Promise<PendingSubmissionsResponse> {
  try {
    const response = await axiosInstance.get<PendingSubmissionsResponse>("/teacher/submissions/pending", { params });
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getPlagiarismAlerts(): Promise<PlagiarismAlert[]> {
  try {
    const response = await axiosInstance.get<PlagiarismAlert[]>("/teacher/plagiarism/alerts");
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}
