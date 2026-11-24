import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";

const PROBLEM_IMPORT_TIMEOUT_MS = 180_000;

export interface ProblemListItem { id: number; code: string | null; title: string; level: string; lesson_id: number | null; total_number_testcase: number; }
export interface ProblemListResponse { items: ProblemListItem[]; total: number; page: number; page_size: number; }
export interface ProblemListParams { q?: string; level?: "easy" | "medium" | "hard"; grading_mode?: "harness" | "stdin_stdout"; course_id?: string; page?: number; page_size?: number; }
export interface ProblemImportResponse {
  created_count: number;
  problems: Array<{ id: number; code: string | null; title: string; total_number_testcase: number }>;
}
export interface ProblemImportPreviewResponse {
  valid: boolean;
  problem_count: number;
  ready_problem_count: number;
  testcase_count: number;
  sample_testcase_count: number;
  hidden_testcase_count: number;
  issues: Array<{ index: number | null; code: string | null; message: string }>;
}

export async function getProblems(params: ProblemListParams = {}): Promise<ProblemListResponse> {
  try { return (await axiosInstance.get<ProblemListResponse>("/problems", { params })).data; } catch (error) { throw wrapAxiosError(error); }
}

export async function importProblems(file: File): Promise<ProblemImportResponse> {
  const data = new FormData();
  data.append("file", file);
  try {
    return (await axiosInstance.post<ProblemImportResponse>("/problems/import", data, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: PROBLEM_IMPORT_TIMEOUT_MS,
    })).data;
  } catch (error) { throw wrapAxiosError(error); }
}

export async function previewProblemImport(file: File): Promise<ProblemImportPreviewResponse> {
  const data = new FormData();
  data.append("file", file);
  try {
    return (await axiosInstance.post<ProblemImportPreviewResponse>("/problems/import/preview", data, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: PROBLEM_IMPORT_TIMEOUT_MS,
    })).data;
  } catch (error) { throw wrapAxiosError(error); }
}
