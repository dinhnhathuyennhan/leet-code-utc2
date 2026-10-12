import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type { ClassApiRecord, CourseApiRecord, CourseDetail, CourseLanguage, CourseListParams, CourseListResponse, CourseSession, CourseStudent, LessonMutationRequest, ProblemDetailData, ProblemUpdateRequest, SessionDetailData, StudentSearchResult } from "@/lib/types/course";

function languageFromCover(cover: string | null): CourseLanguage {
  const value = (cover ?? "").toLowerCase();
  if (value.includes("python")) return "python";
  if (value.includes("javascript") || value === "js") return "javascript";
  if (value.includes("cpp") || value.includes("c++")) return "cpp";
  if (value === "c") return "c";
  return "java";
}

function statusFromDates(start: string, end: string): CourseDetail["status"] {
  const now = Date.now();
  if (now < new Date(start).getTime()) return "upcoming";
  if (now > new Date(end).getTime()) return "closed";
  return "ongoing";
}

function toSummary(record: CourseApiRecord) {
  const academicYear = record.term.replace(/^HK\d-/, "");
  const semester = Number(record.term.match(/^HK(\d)/)?.[1] ?? 1);
  return {
    id: record.course_id,
    code: record.course_id,
    name: record.course_name,
    language: languageFromCover(record.avt_link),
    status: statusFromDates(record.start_date, record.end_date),
    teacher_name: record.created_by,
    semester,
    academic_year: academicYear,
    group: 1,
  };
}

// SỬA: Giữ số liệu AC do backend tính; chỉ dùng giá trị 0 cho dữ liệu API cũ.
function toStudent(record: { enrollment_id: number; student_id: string; full_name: string; email: string; class_id?: string | null; submitted_lessons?: number; total_lessons?: number; progress_percent?: number }): CourseStudent {
  return { ...record, submitted_lessons: record.submitted_lessons ?? 0, total_lessons: record.total_lessons ?? 0, progress_percent: record.progress_percent ?? 0, submission_history: [] };
}

export async function getCourses(params: CourseListParams = {}): Promise<CourseListResponse> {
  try {
    const response = await axiosInstance.get<CourseApiRecord[]>("/courses");
    let items = response.data.map(toSummary);
    if (params.search) {
      const query = params.search.toLowerCase();
      items = items.filter((course) => `${course.code} ${course.name}`.toLowerCase().includes(query));
    }
    if (params.semester) items = items.filter((course) => course.semester === params.semester);
    if (params.academic_year) items = items.filter((course) => course.academic_year === params.academic_year);
    return { items, stats: { course_count: items.length, completed_problems: 0, total_problems: 0, due_this_week: 0 } };
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getCourseById(courseId: number | string): Promise<CourseDetail> {
  try {
    const response = await axiosInstance.get<CourseApiRecord>(`/courses/${courseId}`);
    const course = toSummary(response.data);
    return { ...course, room: "", end_date: response.data.end_date, student_count: response.data.total_number_student, updated_at: "", sessions: response.data.sessions ?? [], grades: response.data.grades ?? [] };
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getCourseEnrollments(courseId: string): Promise<CourseStudent[]> {
  try {
    const response = await axiosInstance.get<Array<{ enrollment_id: number; student_id: string; full_name: string; email: string; class_id?: string | null; submitted_lessons?: number; total_lessons?: number; progress_percent?: number }>>(`/courses/${courseId}/enrollments`);
    return response.data.map(toStudent);
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** Requires backend GET /students?email=...&class_id=.... */
export async function searchStudents(params: { email?: string; classId?: string }): Promise<StudentSearchResult[]> {
  try {
    const response = await axiosInstance.get<StudentSearchResult[]>("/students", {
      params: { email: params.email || undefined, class_id: params.classId || undefined },
    });
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** Requires backend GET /classes. */
export async function getClasses(): Promise<ClassApiRecord[]> {
  try {
    const response = await axiosInstance.get<ClassApiRecord[]>("/classes");
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

/** Requires backend GET /classes/{classId}/students. */
export async function getClassStudents(classId: string): Promise<StudentSearchResult[]> {
  try {
    const response = await axiosInstance.get<StudentSearchResult[]>(`/classes/${classId}/students`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function addStudentToCourse(courseId: string, studentId: string): Promise<void> {
  try {
    await axiosInstance.post(`/courses/${courseId}/enrollments`, { student_id: studentId });
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function addClassToCourse(courseId: string, classId: string): Promise<{ added_count: number; skipped_count: number }> {
  try {
    const response = await axiosInstance.post<{ added_count: number; skipped_count: number }>(`/courses/${courseId}/enrollments/class`, { class_id: classId });
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function deleteStudentFromCourse(courseId: string, studentId: string): Promise<void> {
  try {
    await axiosInstance.delete(`/courses/${courseId}/enrollments/${studentId}`);
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getSessionDetail(courseId: string, lessonId: string | number): Promise<SessionDetailData> {
  try {
    const response = await axiosInstance.get<SessionDetailData>(`/courses/${courseId}/lessons/${lessonId}`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getProblemDetail(courseId: string, lessonId: string | number, problemId: string | number): Promise<ProblemDetailData> {
  try {
    const response = await axiosInstance.get<ProblemDetailData>(`/courses/${courseId}/lessons/${lessonId}/problems/${problemId}`);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

// SỬA: Gọi API cập nhật đúng bài tập đang được chọn trong trang Soạn bài tập.
export async function updateProblem(courseId: string, lessonId: string | number, problemId: string | number, data: ProblemUpdateRequest): Promise<ProblemDetailData> {
  try {
    const response = await axiosInstance.patch<ProblemDetailData>(`/courses/${courseId}/lessons/${lessonId}/problems/${problemId}`, data);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

// SỬA: Upload ZIP/JSON testcase tới backend để giải nén, chuẩn hóa và lưu theo Problem hiện tại.
export async function uploadProblemTestcases(courseId: string, lessonId: string | number, problemId: string | number, file: File): Promise<ProblemDetailData> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await axiosInstance.post<ProblemDetailData>(`/courses/${courseId}/lessons/${lessonId}/problems/${problemId}/testcases/upload`, formData);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function createLesson(courseId: string, data: LessonMutationRequest): Promise<CourseDetail> {
  try {
    const response = await axiosInstance.post<CourseApiRecord>(`/courses/${courseId}/lessons`, data);
    const course = toSummary(response.data);
    return { ...course, room: "", end_date: response.data.end_date, student_count: response.data.total_number_student, updated_at: "", sessions: response.data.sessions ?? [], grades: response.data.grades ?? [] };
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function updateLesson(courseId: string, lessonId: number, data: LessonMutationRequest): Promise<CourseDetail> {
  try {
    const response = await axiosInstance.patch<CourseApiRecord>(`/courses/${courseId}/lessons/${lessonId}`, data);
    const course = toSummary(response.data);
    return { ...course, room: "", end_date: response.data.end_date, student_count: response.data.total_number_student, updated_at: "", sessions: response.data.sessions ?? [], grades: response.data.grades ?? [] };
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export function isCourseSessionDataAvailable(sessions: CourseSession[]): boolean {
  return sessions.length > 0;
}
