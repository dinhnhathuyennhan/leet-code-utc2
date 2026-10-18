import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type {
  PendingSubmissionParams,
  PendingSubmissionsResponse,
  PlagiarismAlert,
  StudentOverview,
  TeacherOverview,
} from "@/lib/types/dashboard";
import {
  toCourseSummary,
  type CourseResponseRaw,
} from "@/lib/api/transformers/course";

// Dashboard endpoints are kept together so query hooks share one typed API contract.

export async function getTeacherOverview(): Promise<TeacherOverview> {
  try {
    const response = await axiosInstance.get<TeacherOverview>("/teacher/dashboard/overview");
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/**
 * GET /students/{student_id}/dashboard
 * Transform `courses[]` từ `CourseResponseRaw` → `CourseSummary`
 * (backend trả `course_id`, FE cần `id` + `name`).
 */
export async function getStudentOverview(studentId: string): Promise<StudentOverview> {
  try {
    const response = await axiosInstance.get<{ courses: CourseResponseRaw[] } & Omit<StudentOverview, "courses">>(
      `/students/${encodeURIComponent(studentId)}/dashboard`,
    );
    return {
      ...response.data,
      courses: response.data.courses.map(toCourseSummary),
    };
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
