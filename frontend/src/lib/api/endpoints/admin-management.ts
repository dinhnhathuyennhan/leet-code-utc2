import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type { AxiosRequestConfig } from "axios";
import type { AccountResponse } from "@/lib/api/types";
import type {
  AdminClass, AdminCourse, AdminEnrollment, AdminLesson,
  AdminAIConnection, AdminAIReview, AdminPreviewResult, AdminProblem, AdminProblemList, AdminProblemPayload, AdminTestcasePayload, JudgeResult,
} from "@/lib/types/admin";

const segment = encodeURIComponent;
export const adminCourseUrl = (id: string) => `/courses/${segment(id)}`;
export const adminLessonUrl = (id: string, lessonId: string | number) => `${adminCourseUrl(id)}/lessons/${segment(String(lessonId))}`;
export const adminProblemUrl = (id: string, lessonId: string | number, problemId: string | number) => `${adminLessonUrl(id, lessonId)}/problems/${segment(String(problemId))}`;

async function request<T>(config: AxiosRequestConfig): Promise<T> {
  try {
    return (await axiosInstance.request<T>(config)).data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export const getAdminCourses = () => request<AdminCourse[]>({ url: "/courses" });
export const getAdminCourse = (id: string) => request<AdminCourse>({ url: adminCourseUrl(id) });
export const getAdminProfile = () => request<AccountResponse>({ url: "/users/me" });

export const getAdminClasses = () => request<AdminClass[]>({ url: "/classes" });
export const createAdminClass = (data: Pick<AdminClass, "type" | "course_number" | "department">) =>
  request<AdminClass>({ method: "POST", url: "/classes", data });
export const deleteAdminClass = (id: string) => request<void>({ method: "DELETE", url: `/classes/${segment(id)}` });

export const getAdminEnrollments = (id: string) => request<AdminEnrollment[]>({ url: `${adminCourseUrl(id)}/enrollments` });

export const getAdminLesson = (id: string, lessonId: string) => request<AdminLesson>({ url: adminLessonUrl(id, lessonId) });

export const getAdminProblems = (params: { q?: string; level?: string; grading_mode?: "harness" | "stdin_stdout"; page?: number; page_size?: number } = {}) =>
  request<AdminProblemList>({ url: "/problems", params });
export const createAdminProblem = (data: AdminProblemPayload) => request<AdminProblem>({ method: "POST", url: "/problems", data });
export const getAdminBankProblem = (problemId: number) => request<AdminProblem>({ url: `/problems/${problemId}` });
export const updateAdminBankProblem = (problemId: number, data: Partial<AdminProblemPayload>) => request<AdminProblem>({ method: "PATCH", url: `/problems/${problemId}`, data });
export const deleteAdminBankProblem = (problemId: number) => request<void>({ method: "DELETE", url: `/problems/${problemId}` });
export const addAdminTestcase = (problemId: number, data: AdminTestcasePayload) =>
  request<AdminProblem>({ method: "POST", url: `/problems/${problemId}/testcases`, data });
export const updateAdminTestcase = (problemId: number, testcaseId: number, data: AdminTestcasePayload) =>
  request<AdminProblem>({ method: "PUT", url: `/problems/${problemId}/testcases/${testcaseId}`, data });
export const deleteAdminTestcase = (problemId: number, testcaseId: number) =>
  request<void>({ method: "DELETE", url: `/problems/${problemId}/testcases/${testcaseId}` });
export const previewAdminProblem = (problemId: number, data: {
  language: string; code: string;
}) =>
  request<AdminPreviewResult>({ method: "POST", url: `/problems/${problemId}/run-preview`, data, timeout: 320000 });
export const reviewAdminPreview = (problemId: number, data: { language: string; code: string; preview_token: string }) =>
  request<AdminAIReview>({ method: "POST", url: `/ai/problems/${problemId}/review-preview`, data, timeout: 190000 });
export const testAdminAIConnection = () =>
  request<AdminAIConnection>({ url: "/ai/test-connection", timeout: 15000 });
export const getAdminProblem = (id: string, lessonId: string, problemId: string) =>
  request<AdminProblem>({ url: adminProblemUrl(id, lessonId, problemId) });

export const testAdminJudge = () => request<JudgeResult>({ method: "POST", url: "/judge0/test", timeout: 60000 });
export const runAdminJudge = (data: { source_code: string; language_id: number; stdin: string }) =>
  request<JudgeResult>({ method: "POST", url: "/judge0/run", data, timeout: 60000 });
