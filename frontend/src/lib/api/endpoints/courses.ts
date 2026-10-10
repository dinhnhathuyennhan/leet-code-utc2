import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import {
  toCourseDetail,
  toCourseSummary,
  type CourseResponseRaw,
} from "@/lib/api/transformers/course";
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
    const response = await axiosInstance.get<CourseResponseRaw[]>("/courses", { params });
    return response.data.map(toCourseSummary);
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getCourseById(id: number | string): Promise<CourseDetail> {
  try {
    const response = await axiosInstance.get<CourseResponseRaw>(`/courses/${id}`);
    return toCourseDetail(response.data);
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

/** GET /students/{student_id}/courses — dùng cho SV xem "lớp đang học" / GV xem SV mình dạy. */
export async function getStudentCourses(studentId: string): Promise<CourseSummary[]> {
  try {
    const response = await axiosInstance.get<CourseResponseRaw[]>(
      `/students/${studentId}/courses`,
    );
    return response.data.map(toCourseSummary);
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** Thông tin enrollment của 1 sinh viên — bổ sung cho tab "Lịch sử đăng ký" của Student. */
export interface StudentEnrollmentItem {
  enrollment_id: number;
  course_id: string;
  course_name: string;
  term: string;
  start_date: string;
  end_date: string;
  total_number_student: number;
}

/** GET /students/{student_id}/enrollments */
export async function getStudentEnrollments(
  studentId: string,
): Promise<StudentEnrollmentItem[]> {
  try {
    const response = await axiosInstance.get<StudentEnrollmentItem[]>(
      `/students/${studentId}/enrollments`,
    );
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}
