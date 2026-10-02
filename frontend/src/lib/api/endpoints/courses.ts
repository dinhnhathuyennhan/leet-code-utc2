import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type { CourseDetail, CourseListParams, CourseListResponse } from "@/lib/types/course";

export async function getCourses(params: CourseListParams = {}): Promise<CourseListResponse> {
  try {
    const response = await axiosInstance.get<CourseListResponse>("/courses", { params });
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
