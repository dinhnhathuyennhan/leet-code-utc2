import { wrapAxiosError } from "@/lib/api/client";
import axiosInstance from "@/lib/axios";
import type {
  StudentSubmissionDetail,
  StudentSubmissionsResponse,
  SubmissionResult,
  SubmitCodePayload,
} from "@/lib/types/submission";

/**
 * Nộp bài cho một bài tập.
 *
 * Backend nhận bài rồi chấm nền (trả 202 ngay), nên kết quả chấm được lấy
 * riêng bằng `getSubmissionResult` trong lúc poll.
 *
 * `courseId` cần encode vì mã lớp có thể chứa ký tự đặc biệt (#, ?, /).
 */
export async function submitAssignment(
  courseId: string,
  lessonId: string | number,
  problemId: string | number,
  payload: SubmitCodePayload,
): Promise<{ submission_id: number; status: string }> {
  try {
    const response = await axiosInstance.post<{ submission_id: number; status: string }>(
      `/courses/${encodeURIComponent(courseId)}/lessons/${lessonId}/problems/${problemId}/submissions`,
      payload,
    );
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** Chạy thử code với các testcase mẫu (không tạo bài nộp). */
export async function runCode(
  courseId: string,
  lessonId: string | number,
  problemId: string | number,
  payload: SubmitCodePayload,
): Promise<RunCodeResponse> {
  try {
    const response = await axiosInstance.post<RunCodeResponse>(
      `/courses/${encodeURIComponent(courseId)}/lessons/${lessonId}/problems/${problemId}/run`,
      payload,
      // Judge0 có thể mất vài giây cho mỗi testcase -> nới timeout so với mặc định 10s.
      { timeout: 60_000 },
    );
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** Lịch sử bài nộp của chính sinh viên đang đăng nhập. */
export async function getMySubmissions(params?: {
  course?: string;
  problem_id?: number;
}): Promise<StudentSubmissionsResponse> {
  try {
    const response = await axiosInstance.get<StudentSubmissionsResponse>("/submissions/mine", {
      params: {
        course: params?.course ? encodeURIComponent(params.course) : undefined,
        problem_id: params?.problem_id,
      },
    });
    const counts = response.data.counts ?? ({} as StudentSubmissionsResponse["counts"]);
    return {
      items: response.data.items ?? [],
      total: response.data.total ?? 0,
      counts: {
        all: counts.all ?? response.data.total ?? 0,
        accepted: counts.accepted ?? 0,
        wrong_answer: counts.wrong_answer ?? 0,
        compile_error: counts.compile_error ?? 0,
        pending: counts.pending ?? 0,
      },
    };
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** Chi tiết kết quả chấm của một bài nộp. */
export async function getMySubmissionDetail(id: string | number): Promise<StudentSubmissionDetail> {
  try {
    const response = await axiosInstance.get<StudentSubmissionDetail>(`/submissions/mine/${id}`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** Kết quả chấm rút gọn — dùng để poll trong lúc backend chấm nền. */
export async function getSubmissionResult(id: string | number): Promise<SubmissionResult> {
  try {
    const response = await axiosInstance.get<SubmissionResult>(`/submissions/${id}/result`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export interface RunCodeResponse {
  status: string;
  compile_output: string | null;
  cases: {
    index: number;
    status: string;
    input: unknown;
    expected_output: unknown;
    actual_output: unknown;
    stderr: string | null;
    time: number | null;
  }[];
}
