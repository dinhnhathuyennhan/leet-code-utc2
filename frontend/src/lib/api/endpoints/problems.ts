import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";

export interface ProblemListItem { id: number; code: string | null; title: string; level: string; lesson_id: number | null; total_number_testcase: number; }
export interface ProblemListResponse { items: ProblemListItem[]; total: number; page: number; page_size: number; }
export interface ProblemListParams { q?: string; level?: "easy" | "medium" | "hard"; course_id?: string; page?: number; page_size?: number; }

export async function getProblems(params: ProblemListParams = {}): Promise<ProblemListResponse> {
  try { return (await axiosInstance.get<ProblemListResponse>("/problems", { params })).data; } catch (error) { throw wrapAxiosError(error); }
}
export async function deleteProblem(courseId: string, lessonId: string | number, problemId: string | number): Promise<void> {
  try { await axiosInstance.delete(`/courses/${courseId}/lessons/${lessonId}/problems/${problemId}`); } catch (error) { throw wrapAxiosError(error); }
}
