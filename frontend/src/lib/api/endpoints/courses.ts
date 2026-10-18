import axiosInstance from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import { vnWeekRange } from "@/lib/helpers/datetime";
import type { 
  ClassApiRecord, 
  CourseApiRecord, 
  CourseDetail, 
  CourseLanguage, 
  CourseListParams, 
  CourseListResponse, 
  CourseSession, 
  CourseStudent, 
  CourseTermsResponse, 
  LessonMutationRequest, 
  ProblemDetailData, 
  ProblemUpdateRequest, 
  SessionDetailData, 
  StudentSearchResult 
} from "@/lib/types/course";

export interface CourseCreateRequest {
  course_id: string;
  course_name: string;
  avt_link: string;
  term: string;
  start_date: string;
  end_date: string;
}

export interface CourseUpdateRequest {
  course_name?: string;
  term?: string;
  avt_link?: string;
  start_date?: string;
  end_date?: string;
}

export async function createCourse(data: CourseCreateRequest): Promise<CourseApiRecord> {
  try {
    const response = await axiosInstance.post<CourseApiRecord>("/courses", data);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function updateCourse(courseId: string, data: CourseUpdateRequest): Promise<CourseApiRecord> {
  try {
    const response = await axiosInstance.patch<CourseApiRecord>(`/courses/${courseId}`, data);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}


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

function isDueThisWeek(deadline: string, now = new Date()): boolean {
  const date = new Date(deadline);
  if (Number.isNaN(date.getTime())) return false;
  // F2: Tính khoảng tuần theo lịch VN để tránh lệch khi browser ở múi giờ khác.
  const [startOfWeek, endOfWeek] = vnWeekRange(now);
  return date >= startOfWeek && date < endOfWeek;
}

function toSummary(record: CourseApiRecord) {
  const termMatch = record.term.match(/^HK(\d)\s*(.+)$/i);
  const semester = Number(termMatch?.[1] ?? 1);
  const academicYear = termMatch?.[2] ?? record.term;
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
    sessions: record.sessions ?? [],
    start_date: record.start_date,
  };
}

// SỬA: Giữ số liệu AC do backend tính; chỉ dùng giá trị 0 cho dữ liệu API cũ.
function toStudent(record: { 
  enrollment_id: number; 
  student_id: string; 
  full_name: string; 
  email: string; 
  class_id?: string | null; 
  submitted_lessons?: number;
  accepted_problems?: number;
  total_lessons?: number; 
  progress_percent?: number 
}): CourseStudent {
  return { 
    ...record, 
    submitted_lessons: record.submitted_lessons ?? record.accepted_problems ?? 0,
    accepted_problems: record.accepted_problems ?? record.submitted_lessons ?? 0,
    total_lessons: record.total_lessons ?? 0, 
    progress_percent: record.progress_percent ?? 0, 
    submission_history: [] 
  };
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
    
    const dueThisWeek = items.reduce(
      (total, course) =>
        total + (course.sessions ?? []).filter((session) => isDueThisWeek(session.deadline)).length,
      0,
    );
    return {
      items,
      stats: {
        course_count: items.length,
        active_course_count: items.filter((course) => course.status === "ongoing").length,
        upcoming_courses: items.filter((course) => course.status === "upcoming").length,
        due_this_week: dueThisWeek,
      },
    };
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getCourseTerms(): Promise<CourseTermsResponse> {
  try {
    const response = await axiosInstance.get<CourseTermsResponse>("/courses/terms");
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getCourseById(courseId: number | string): Promise<CourseDetail> {
  try {
    const response = await axiosInstance.get<CourseApiRecord>(`/courses/${courseId}`);
    const course = toSummary(response.data);
    return { 
      ...course, 
      room: "", 
      end_date: response.data.end_date, 
      student_count: response.data.total_number_student, 
      updated_at: response.data.updated_at ?? null,
      sessions: response.data.sessions ?? [], 
      grades: response.data.grades ?? [] 
    };
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function getCourseEnrollments(courseId: string): Promise<CourseStudent[]> {
  try {
    const response = await axiosInstance.get<Array<{ 
      enrollment_id: number; 
      student_id: string; 
      full_name: string; 
      email: string; 
      class_id?: string | null; 
      submitted_lessons?: number;
      accepted_problems?: number;
      total_lessons?: number; 
      progress_percent?: number 
    }>>(`/courses/${courseId}/enrollments`);
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
    const response = await axiosInstance.post<ProblemDetailData>(`/courses/${courseId}/lessons/${lessonId}/problems/${problemId}/testcases/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function createLesson(courseId: string, data: LessonMutationRequest): Promise<CourseDetail> {
  try {
    const response = await axiosInstance.post<CourseApiRecord>(`/courses/${courseId}/lessons`, data);
    const course = toSummary(response.data);
    return { 
      ...course, 
      room: "", 
      end_date: response.data.end_date, 
      student_count: response.data.total_number_student, 
      updated_at: response.data.updated_at ?? null,
      sessions: response.data.sessions ?? [], 
      grades: response.data.grades ?? [] 
    };
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export async function updateLesson(courseId: string, lessonId: number, data: LessonMutationRequest): Promise<CourseDetail> {
  try {
    const response = await axiosInstance.patch<CourseApiRecord>(`/courses/${courseId}/lessons/${lessonId}`, data);
    const course = toSummary(response.data);
    return { 
      ...course, 
      room: "", 
      end_date: response.data.end_date, 
      student_count: response.data.total_number_student, 
      updated_at: response.data.updated_at ?? null,
      sessions: response.data.sessions ?? [], 
      grades: response.data.grades ?? [] 
    };
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

export function isCourseSessionDataAvailable(sessions: CourseSession[]): boolean {
  return sessions.length > 0;
}

/** Tạo bài tập mới thủ công trong một buổi học */
export async function createProblem(courseId: string, lessonId: string | number, data: ProblemUpdateRequest): Promise<ProblemDetailData> {
  try {
    const response = await axiosInstance.post<ProblemDetailData>(`/courses/${courseId}/lessons/${lessonId}/problems`, data);
    return response.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}
