import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";

export interface Testcase { id: number; input: unknown; expected_output: unknown; is_sample: boolean; input_type: string; expected_output_type: string; }
export interface TestcaseListResponse { testcases: Testcase[]; total_sample: number; total_hidden: number; }
type Path = { courseId: string; lessonId: string | number; problemId: string | number };
const path = ({ courseId, lessonId, problemId }: Path) => `/courses/${courseId}/lessons/${lessonId}/problems/${problemId}/testcases`;
export async function getTestcases(args: Path & { isSample?: boolean }): Promise<TestcaseListResponse> {
  try { return (await axiosInstance.get<TestcaseListResponse>(path(args), { params: args.isSample === undefined ? {} : { is_sample: args.isSample } })).data; } catch (error) { throw wrapAxiosError(error); }
}
export async function addTestcase(args: Path, data: { input: unknown[]; expected_output: unknown; is_sample?: boolean }): Promise<void> {
  try { await axiosInstance.post(path(args), data); } catch (error) { throw wrapAxiosError(error); }
}
export async function updateTestcase(args: Path & { testcaseId: number }, data: { input?: unknown[]; expected_output?: unknown; is_sample?: boolean }): Promise<void> {
  try { await axiosInstance.patch(`${path(args)}/${args.testcaseId}`, data); } catch (error) { throw wrapAxiosError(error); }
}
export async function deleteTestcase(args: Path & { testcaseId: number }): Promise<void> {
  try { await axiosInstance.delete(`${path(args)}/${args.testcaseId}`); } catch (error) { throw wrapAxiosError(error); }
}
export async function downloadTestcases(args: Path, format: "json" | "zip" = "json"): Promise<Blob> {
  try { return (await axiosInstance.get<Blob>(`${path(args)}/download`, { params: { format }, responseType: "blob" })).data; } catch (error) { throw wrapAxiosError(error); }
}
export async function batchUpdateSamples(args: Path, testcaseIds: number[], isSample: boolean): Promise<void> {
  try { await axiosInstance.patch(`${path(args)}/batch`, { testcase_ids: testcaseIds, is_sample: isSample }); } catch (error) { throw wrapAxiosError(error); }
}
export async function previewTestcases(args: Path, testcases: unknown[]): Promise<{ valid: boolean; count: number; sample_count: number; hidden_count: number; errors: Array<{ index: number; message: string }>; warnings: Array<{ message: string }> }> {
  try { return (await axiosInstance.post(`${path(args)}/preview`, { testcases })).data; } catch (error) { throw wrapAxiosError(error); }
}
