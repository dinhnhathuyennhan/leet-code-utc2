import { getCourses } from "@/lib/api/endpoints/courses";
import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type { PendingFilter, PendingSubmissionParams, PendingSubmissionsResponse, StudentOverview, SubmissionDetail, TeacherOverview } from "@/lib/types/dashboard";
import type { UserResponse } from "@/lib/api/types";

export async function getTeacherOverview(): Promise<TeacherOverview> {
  const [courses, pending, user] = await Promise.all([
    getCourses(),
    getPendingSubmissions({ filter: "all", limit: 500 }),
    getCurrentUser(),
  ]);
  const pendingForReview = await Promise.all(pending.items.map(async (item) => {
    try {
      const detail = await getSubmissionDetail(item.id);
      return detail.manual_score == null && ["pending", "wrong_answer", "compile_error"].includes(detail.status);
    } catch {
      return false;
    }
  }));
  return {
    teacher_name: user.full_name,
    term_label: courses.items[0] ? `Học kỳ ${courses.items[0].semester} (${courses.items[0].academic_year})` : "",
    stats: { active_courses: courses.items.filter((course) => course.status === "ongoing").length, pending_grading: pendingForReview.filter(Boolean).length },
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
      params: { filter: params.filter, search: params.search, limit: params.limit, course: params.course, lesson_id: params.lesson_id, problem_id: params.problem_id, include_graded: params.include_graded },
    });
    const counts = response.data.counts ?? {};
    return {
      ...response.data,
      counts: {
        all: counts.all ?? response.data.total ?? 0,
        pending: counts.pending ?? 0,
        wrong_answer: counts.wrong_answer ?? 0,
        compile_error: counts.compile_error ?? counts.error ?? 0,
        graded: counts.graded ?? 0,
        ungraded: counts.ungraded ?? 0,
        late_appeal: counts.late_appeal ?? 0,
        similarity: counts.similarity ?? 0,
        error: counts.error ?? 0,
      },
    };
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

export const EMPTY_PENDING_COUNTS: Record<PendingFilter, number> = { all: 0, pending: 0, wrong_answer: 0, compile_error: 0 };
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

