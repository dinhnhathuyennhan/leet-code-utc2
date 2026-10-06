import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type {
  CourseDetail,
  CourseListParams,
  CourseStudent,
  CourseSummary,
} from "@/lib/types/course";

/**
 * GET /courses — BE trả về `CourseResponse[]` thuần, không có `items`/`stats`.
 * Sau khi FE bổ sung stats, đổi kiểu trả về sang `CourseListResponse`.
 */
export async function getCourses(params: CourseListParams = {}): Promise<CourseSummary[]> {
  try {
    const response = await axiosInstance.get<CourseSummary[]>("/courses", { params });
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getCourseById(id: number | string): Promise<CourseDetail> {
  try {
    const response = await axiosInstance.get<CourseDetail>(`/courses/${id}`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** GET /courses/{course_id}/enrollments — dùng cho sinh viên/giảng viên xem danh sách SV trong lớp. */
export async function getCourseStudents(courseId: string): Promise<CourseStudent[]> {
  try {
    const response = await axiosInstance.get<CourseStudent[]>(`/courses/${courseId}/enrollments`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}