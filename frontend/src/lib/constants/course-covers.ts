import type { CourseLanguage } from "@/lib/types/course";

/**
 * Ảnh bìa theo ngôn ngữ của lớp — đặt trong `public/images/courses/`.
 * Đổi tên file cho khớp với ảnh thật của bạn ở đây (1 chỗ duy nhất).
 */
export const COURSE_COVERS: Record<CourseLanguage, string> = {
  java: "/images/background-java1.jpg",
  python: "/images/background-python1.jpg",
  javascript: "/images/background-js1.jpg",
  c: "/images/background-c.jpg",
  cpp: "/images/background-c++.jpg",
};
