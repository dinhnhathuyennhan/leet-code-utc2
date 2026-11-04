import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type { AxiosRequestConfig } from "axios";
import type { AccountResponse } from "@/lib/api/types";
import type {
  AdminClass, AdminCourse, AdminEnrollment, AdminLesson, AdminLessonPayload,
  AdminAIConnection, AdminAIReview, AdminPreviewResult, AdminProblem, AdminProblemList, AdminProblemPayload, AdminSubmissionDetail, AdminTestcasePayload, JudgeResult,
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
export const saveAdminCourse = (data: {
  course_name: string; term: string; start_date: string; end_date: string; avt_link?: string | null; course_id?: string;
}, id?: string) => request<AdminCourse>({ method: id ? "PATCH" : "POST", url: id ? adminCourseUrl(id) : "/courses", data });

export const getAdminClasses = () => request<AdminClass[]>({ url: "/classes" });
export const createAdminClass = (data: Pick<AdminClass, "type" | "course_number" | "department">) =>
  request<AdminClass>({ method: "POST", url: "/classes", data });
export const deleteAdminClass = (id: string) => request<void>({ method: "DELETE", url: `/classes/${segment(id)}` });

export const getAdminEnrollments = (id: string) => request<AdminEnrollment[]>({ url: `${adminCourseUrl(id)}/enrollments` });
export const addAdminEnrollment = (id: string, studentId: string) =>
  request<AdminEnrollment>({ method: "POST", url: `${adminCourseUrl(id)}/enrollments`, data: { student_id: studentId } });
export const addAdminClassEnrollment = (id: string, classId: string) =>
  request<{ added_count: number; skipped_count: number }>({ method: "POST", url: `${adminCourseUrl(id)}/enrollments/class`, data: { class_id: classId } });
export const deleteAdminEnrollment = (id: string, studentId: string) =>
  request<void>({ method: "DELETE", url: `${adminCourseUrl(id)}/enrollments/${segment(studentId)}` });

export const getAdminLesson = (id: string, lessonId: string) => request<AdminLesson>({ url: adminLessonUrl(id, lessonId) });
export const saveAdminLesson = (id: string, data: AdminLessonPayload, lessonId?: number) =>
  request<AdminCourse>({ method: lessonId === undefined ? "POST" : "PATCH", url: lessonId === undefined ? `${adminCourseUrl(id)}/lessons` : adminLessonUrl(id, lessonId), data });
export const attachAdminProblems = (id: string, lessonId: string, problemIds: number[]) =>
  request<AdminCourse>({ method: "POST", url: `${adminLessonUrl(id, lessonId)}/problems`, data: { problem_ids: problemIds } });

export const getAdminProblems = (params: { q?: string; level?: string; page?: number; page_size?: number } = {}) =>
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
export const previewAdminProblem = (problemId: number, data: { language: string; code: string }) =>
  request<AdminPreviewResult>({ method: "POST", url: `/problems/${problemId}/run-preview`, data, timeout: 320000 });
export const reviewAdminPreview = (problemId: number, data: { language: string; code: string; preview_token: string }) =>
  request<AdminAIReview>({ method: "POST", url: `/ai/problems/${problemId}/review-preview`, data, timeout: 190000 });
export const testAdminAIConnection = () =>
  request<AdminAIConnection>({ url: "/ai/test-connection", timeout: 15000 });
export const deleteAdminProblem = (id: string, lessonId: string, problemId: number) =>
  request<void>({ method: "DELETE", url: adminProblemUrl(id, lessonId, problemId) });
export const getAdminProblem = (id: string, lessonId: string, problemId: string) =>
  request<AdminProblem>({ url: adminProblemUrl(id, lessonId, problemId) });
export const updateAdminProblem = (id: string, lessonId: string, problemId: string, data: Partial<AdminProblemPayload>) =>
  request<AdminProblem>({ method: "PATCH", url: adminProblemUrl(id, lessonId, problemId), data });
export const uploadAdminTestcases = (id: string, lessonId: string, problemId: string, file: File) => {
  const data = new FormData();
  data.append("file", file);
  return request<AdminProblem>({
    method: "POST", url: `${adminProblemUrl(id, lessonId, problemId)}/testcases/upload`, data,
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const testAdminJudge = () => request<JudgeResult>({ method: "POST", url: "/judge0/test", timeout: 60000 });
export const runAdminJudge = (data: { source_code: string; language_id: number; stdin: string }) =>
  request<JudgeResult>({ method: "POST", url: "/judge0/run", data, timeout: 60000 });

export const getAdminSubmission = (id: string) => request<AdminSubmissionDetail>({ url: `/submissions/${segment(id)}` });
export const saveAdminSubmission = (id: string, data: { feedback: string; status: string; manual_score: number | null }) =>
  request<AdminSubmissionDetail>({ method: "PATCH", url: `/submissions/${segment(id)}`, data });
