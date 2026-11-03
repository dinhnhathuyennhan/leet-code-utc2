"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getMySubmissionDetail,
  getMySubmissions,
  getSubmissionResult,
  runCode,
  submitAssignment,
} from "@/lib/api/endpoints/submissions";
import { getCourseById, getProblemDetail } from "@/lib/api/endpoints/courses";
import type {
  SubmitCodePayload,
  SubmissionResult,
} from "@/lib/types/submission";

export const submissionKeys = {
  all: ["submissions"] as const,
  mine: (course?: string, problemId?: number) =>
    [...submissionKeys.all, "mine", course ?? "all", problemId ?? "all"] as const,
  mineDetail: (id: string | number) => [...submissionKeys.all, "mine", "detail", id] as const,
  result: (id: string | number) => [...submissionKeys.all, "result", id] as const,
};

export interface MySubmissionsParams {
  course?: string;
  problem_id?: number;
}

/** Lịch sử bài nộp của sinh viên đang đăng nhập. */
export function useMySubmissions(params: MySubmissionsParams = {}) {
  return useQuery({
    // problem_id cũng phải nằm trong key, nếu không hai lần lọc khác nhau sẽ
    // dùng chung một cache entry và hiển thị sai danh sách.
    queryKey: submissionKeys.mine(params.course, params.problem_id),
    queryFn: () => getMySubmissions(params),
  });
}

/** Chi tiết kết quả chấm của một bài nộp. */
export function useMySubmissionDetail(id: string | number | undefined) {
  return useQuery({
    queryKey: submissionKeys.mineDetail(id ?? ""),
    queryFn: () => getMySubmissionDetail(id as string | number),
    enabled: id !== undefined && id !== "",
  });
}

/**
 * Kết quả chấm của một bài nộp, tự poll cho tới khi backend chấm xong.
 *
 * Backend chấm nền nên trạng thái ban đầu là `pending`/`processing`; hook này
 * poll lại mỗi 1.5s và tự dừng khi trạng thái đã kết thúc.
 */
export function useSubmissionResult(id: string | number | undefined) {
  return useQuery({
    queryKey: submissionKeys.result(id ?? ""),
    queryFn: () => getSubmissionResult(id as string | number),
    enabled: id !== undefined && id !== "",
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "processing" ? 1_500 : false;
    },
  });
}

/**
 * Nộp bài + nhận kết quả chấm.
 *
 * `onSuccess` invalidate cả lịch sử nộp bài lẫn chi tiết lớp học, vì điểm và
 * trạng thái "Đã nộp / Đã chấm" trong bảng bài tập được suy ra từ submission.
 */
export function useSubmitAssignment(
  courseId: string | undefined,
  lessonId: string | number | undefined,
  problemId: string | number | undefined,
) {
  const queryClient = useQueryClient();

  return useMutation<
    { submission_id: number; status: string },
    unknown,
    SubmitCodePayload
  >({
    mutationFn: (payload) =>
      submitAssignment(
        courseId as string,
        lessonId as string | number,
        problemId as string | number,
        payload,
      ),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: submissionKeys.all });
      if (courseId) {
        void queryClient.invalidateQueries({ queryKey: ["courses", "detail", courseId] });
      }
      // Bắt đầu poll ngay kết quả của bài vừa nộp.
      void queryClient.invalidateQueries({ queryKey: submissionKeys.result(data.submission_id) });
    },
  });
}

/** Chạy thử code với testcase mẫu (không tạo bài nộp). */
export function useRunCode(
  courseId: string | undefined,
  lessonId: string | number | undefined,
  problemId: string | number | undefined,
) {
  return useMutation<unknown, unknown, SubmitCodePayload>({
    mutationFn: (payload) =>
      runCode(
        courseId as string,
        lessonId as string | number,
        problemId as string | number,
        payload,
      ),
  });
}

export interface ProblemDetailQuery {
  course?: string;
  lessonId?: string | number;
  problemId?: string | number;
}

/**
 * Chi tiết bài tập cho sinh viên.
 *
 * Gộp hai lệnh API của backend: `GET /courses/{id}` để tìm buổi học chứa bài
 * tập, rồi `GET .../problems/{problem_id}` để lấy đề + testcase mẫu.
 * `enabled` chỉ bật khi đã biết đủ course/lesson/problem.
 */
export function useProblemDetail({ course, lessonId, problemId }: ProblemDetailQuery) {
  return useQuery({
    // Key riêng (không dùng ["courses","detail",...]) để không đè cache của
    // useCourse() — hai hook trả về shape khác nhau, dùng chung key sẽ khiến
    // trang nhận nhầm dữ liệu và render rỗng.
    queryKey: ["courses", "problem-detail", course ?? "", lessonId ?? "", problemId ?? ""],
    queryFn: async () => {
      if (!course || lessonId === undefined || problemId === undefined) {
        throw new Error("Thiếu tham số bài tập");
      }
      return getProblemDetail(course, lessonId, problemId);
    },
    enabled: Boolean(course) && lessonId !== undefined && problemId !== undefined,
  });
}

/**
 * Tìm buổi học chứa một bài tập trong một lớp.
 *
 * Dùng cho trang chi tiết bài tập khi URL chỉ có courseId + problemId
 * (route `/student/classes/[id]/assignments/[assignmentId]`).
 */
export function useCourseWithProblem(
  courseId: string | undefined,
  problemId: string | undefined,
) {
  return useQuery({
    // KHÔNG dùng courseKeys.detail() ở đây: hook này trả về { course, session }
    // còn useCourse() trả về CourseDetail. Dùng chung key thì React Query sẽ
    // trả nhầm cache của hook kia -> `course.sessions` là undefined và trang
    // chi tiết bài tập render rỗng (màn hình trắng).
    queryKey: ["courses", "course-with-problem", courseId ?? "", problemId ?? ""],
    queryFn: async () => {
      const course = await getCourseById(courseId as string);
      const numericProblemId = Number(problemId);
      const session =
        course.sessions.find((item) =>
          item.problems.some((problem) => problem.id === numericProblemId),
        ) ?? null;
      return { course, session };
    },
    enabled: Boolean(courseId) && problemId !== undefined,
  });
}

export type { SubmissionResult };
