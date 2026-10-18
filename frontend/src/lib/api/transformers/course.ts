import type { CourseDetail, CourseLanguage, CourseStatus, CourseSummary } from "@/lib/types/course";

/**
 * Shape trả về thẳng từ backend `GET /courses` và `GET /courses/{id}`.
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
  sessions?: unknown[];
  grades?: unknown[];
}

function parseSemester(term: string): number {
  const match = term.match(/HK\s*(\d+)/i);
  if (match) return Number(match[1]);
  return 1;
}

function parseAcademicYear(term: string, endDate: string): string {
  const startYearMatch = term.match(/(\d{4})/);
  const startYear = startYearMatch ? Number(startYearMatch[1]) : new Date(endDate).getFullYear() - 1;
  const endYear = startYear + 1;
  return `${startYear}-${endYear}`;
}

function parseGroup(code: string): number {
  const match = code.match(/\.K(\d+)/i);
  if (match) return Number(match[1]);
  return 1;
}

function inferLanguage(avtLink: string | null, code: string): CourseLanguage {
  const hay = `${avtLink ?? ""} ${code}`.toLowerCase();
  if (hay.includes("python")) return "python";
  if (hay.includes("javascript") || hay.includes("js")) return "javascript";
  if (hay.includes("cpp") || hay.includes("c++")) return "cpp";
  if (/\bc\b/.test(hay) && !hay.includes("cpp")) return "c";
  return "java";
}

function inferStatus(start: string, end: string): CourseStatus {
  const now = Date.now();
  if (now < new Date(start).getTime()) return "upcoming";
  if (now > new Date(end).getTime()) return "closed";
  return "ongoing";
}

export function toCourseSummary(raw: CourseResponseRaw): CourseSummary {
  return {
    id: raw.course_id,
    code: raw.course_id,
    name: raw.course_name,
    language: inferLanguage(raw.avt_link, raw.course_id),
    status: inferStatus(raw.start_date, raw.end_date),
    teacher_name: raw.created_by,
    semester: parseSemester(raw.term),
    academic_year: parseAcademicYear(raw.term, raw.end_date),
    group: parseGroup(raw.course_id),
    sessions: (raw.sessions ?? []) as CourseSummary["sessions"],
  };
}

export function toCourseDetail(raw: CourseResponseRaw): CourseDetail {
  return {
    ...toCourseSummary(raw),
    room: "",
    end_date: raw.end_date,
    student_count: raw.total_number_student,
    updated_at: "",
    sessions: (raw.sessions ?? []) as CourseDetail["sessions"],
    grades: raw.grades as CourseDetail["grades"],
  };
}
