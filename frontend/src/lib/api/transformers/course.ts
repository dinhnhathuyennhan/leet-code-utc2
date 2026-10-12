import type { CourseDetail, CourseSummary } from "@/lib/types/course";

/**
 * Shape trả về thẳng từ backend `GET /courses` và `GET /courses/{id}`
 * (xem `backend/app/schemas/course.py::CourseResponse`).
 *
 * Frontend tự dựng type `CourseSummary`/`CourseDetail` cho UI với tên field
 * ngắn gọn hơn (id, code, name) → cần mapper này để khoảng cách backend
 * không ảnh hưởng tới component (xem lỗi "My Courses không hiển thị").
 */
export interface CourseResponseRaw {
  course_id: string;
  course_name: string;
  term: string;
  start_date: string;
  end_date: string;
  avt_link: string | null;
  created_by: string;
  total_number_student: number;
}

/**
 * Map `CourseResponseRaw` (BE) → `CourseSummary` (FE UI).
 * - `id`  = `course_id`  (dùng làm React key + routing)
 * - `code` = `course_id` (hiển thị nhãn ngắn trên card)
 * - `name` = `course_name` (tiêu đề đầy đủ)
 */
export function toCourseSummary(raw: CourseResponseRaw): CourseSummary {
  return {
    id: raw.course_id,
    code: raw.course_id,
    name: raw.course_name,
    term: raw.term,
    start_date: raw.start_date,
    end_date: raw.end_date,
    avt_link: raw.avt_link,
    created_by: raw.created_by,
    total_number_student: raw.total_number_student,
  };
}

/** `CourseDetail` hiện cùng shape với `CourseSummary`; vẫn qua mapper để dễ mở rộng sau này. */
export function toCourseDetail(raw: CourseResponseRaw): CourseDetail {
  return toCourseSummary(raw);
}
