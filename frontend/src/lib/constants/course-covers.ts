import type { CourseLanguage } from "@/lib/types/course";

/**
 * Ảnh bìa theo ngôn ngữ của lớp — đặt trong `public/images/courses/`.
 * Đổi tên file cho khớp với ảnh thật của bạn ở đây (1 chỗ duy nhất).
 */
export const COURSE_COVERS: Record<CourseLanguage, string> = {
  java: "/images/courses/java.png",
  python: "/images/courses/python.png",
  javascript: "/images/courses/javascript.png",
  c: "/images/courses/c.png",
  cpp: "/images/courses/cpp.png",
};
