import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";

export async function reorderLessons(courseId: string, order: number[]): Promise<void> {
  try { await axiosInstance.patch(`/courses/${courseId}/lessons/reorder`, { order }); } catch (error) { throw wrapAxiosError(error); }
}
export async function duplicateLesson(courseId: string, lessonId: number, data: { new_start_date: string; new_end_date: string; target_course_id?: string }): Promise<void> {
  try { await axiosInstance.post(`/courses/${courseId}/lessons/${lessonId}/duplicate`, data); } catch (error) { throw wrapAxiosError(error); }
}
export async function deleteLesson(courseId: string, lessonId: number): Promise<void> {
  try { await axiosInstance.delete(`/courses/${courseId}/lessons/${lessonId}`); } catch (error) { throw wrapAxiosError(error); }
}
