import { ApiError } from "@/lib/api/error";
import { getCourses } from "@/lib/api/endpoints/courses";
import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type { PendingFilter, PendingSubmissionParams, PendingSubmissionsResponse, PlagiarismAlert, StudentOverview, SubmissionDetail, TeacherOverview } from "@/lib/types/dashboard";
import type { UserResponse } from "@/lib/api/types";

export async function getTeacherOverview(): Promise<TeacherOverview> {
  const [courses, pending, user] = await Promise.all([
    getCourses(),
    getPendingSubmissions({ filter: "all", limit: 1 }),
    getCurrentUser(),
  ]);
  return {
    teacher_name: user.full_name,
    term_label: courses.items[0] ? `Học kỳ ${courses.items[0].semester} (${courses.items[0].academic_year})` : "",
    stats: { active_courses: courses.items.filter((course) => course.status === "ongoing").length, pending_grading: pending.total, plagiarism_cases: pending.counts.similarity },
    recent_courses: courses.items
      .filter((course) => course.status === "ongoing")
      .sort((a, b) => new Date(b.start_date ?? 0).getTime() - new Date(a.start_date ?? 0).getTime())
      .slice(0, 4)
      .map((course) => ({ ...course, teacher_name: user.full_name })),
  };
}

export async function getCurrentUser(): Promise<UserResponse> {
  try {
    const response = await axiosInstance.get<UserResponse>("/users/me");
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getPendingSubmissions(params: PendingSubmissionParams): Promise<PendingSubmissionsResponse> {
  try {
    const response = await axiosInstance.get<PendingSubmissionsResponse>("/submissions/pending", {
      params: { filter: params.filter, search: params.search, limit: params.limit, course: params.course, lesson_id: params.lesson_id, problem_id: params.problem_id },
    });
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getSubmissionDetail(id: string | number): Promise<SubmissionDetail> {
  try {
    const response = await axiosInstance.get<SubmissionDetail>(`/submissions/${id}`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function updateSubmission(id: string | number, data: { feedback?: string | null; status?: string; manual_score?: number }): Promise<SubmissionDetail> {
  try {
    const response = await axiosInstance.patch<SubmissionDetail>(`/submissions/${id}`, data);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getPlagiarismAlerts(): Promise<PlagiarismAlert[]> {
  throw new ApiError({ status: 501, detail: "API cảnh báo đạo văn chưa được backend cung cấp." });
}

export const EMPTY_PENDING_COUNTS: Record<PendingFilter, number> = { all: 0, graded: 0, late_appeal: 0, similarity: 0, error: 0 };
export async function getStudentOverview(studentId: string): Promise<StudentOverview> {
  try {
    const response = await axiosInstance.get<StudentOverview>(
      `/students/${encodeURIComponent(studentId)}/dashboard`,
    );
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

