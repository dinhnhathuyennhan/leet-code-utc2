import { ApiError } from "@/lib/api/error";
import { getCourses } from "@/lib/api/endpoints/courses";
import type { PendingFilter, PendingSubmissionParams, PendingSubmissionsResponse, PlagiarismAlert, TeacherOverview } from "@/lib/types/dashboard";

export async function getTeacherOverview(): Promise<TeacherOverview> {
  const courses = await getCourses();
  return {
    teacher_name: courses.items[0]?.teacher_name ?? "",
    term_label: courses.items[0] ? `Học kỳ ${courses.items[0].semester} (${courses.items[0].academic_year})` : "",
    stats: { active_courses: courses.items.filter((course) => course.status === "ongoing").length, pending_grading: 0, plagiarism_cases: 0 },
    recent_courses: courses.items.slice(0, 5),
  };
}

export async function getPendingSubmissions(_params: PendingSubmissionParams): Promise<PendingSubmissionsResponse> {
  void _params;
  throw new ApiError({ status: 501, detail: "API bài nộp chưa được backend cung cấp." });
}

export async function getPlagiarismAlerts(): Promise<PlagiarismAlert[]> {
  throw new ApiError({ status: 501, detail: "API cảnh báo đạo văn chưa được backend cung cấp." });
}

export const EMPTY_PENDING_COUNTS: Record<PendingFilter, number> = { all: 0, late_appeal: 0, similarity: 0, error: 0 };
