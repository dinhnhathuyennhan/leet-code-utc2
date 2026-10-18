"use client";

import { useState } from "react";

import { DEFAULT_TERM } from "@/lib/constants/academic";
import { useCourseTerms, useCourses } from "@/lib/hooks/use-courses";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import type { CourseSummary, CourseView } from "@/lib/types/course";

export interface CourseFilterState {
  search: string;
  setSearch: (value: string) => void;
  semester: number;
  setSemester: (value: number) => void;
  semesters: number[];
  year: string;
  setYear: (value: string) => void;
  years: string[];
  view: CourseView;
  setView: (value: CourseView) => void;
}

/**
 * State bộ lọc + query danh sách lớp — dùng chung cho trang lớp của giảng viên và sinh viên.
 *
 * - ``search`` được đẩy xuống server (BE `GET /courses?search=...`).
 * - ``semester`` + ``academic_year`` đẩy xuống server qua params tương ứng.
 * - ``view`` chỉ là state UI (grid / list), không ảnh hưởng tới request.
 */
export function useCourseList() {
  const [search, setSearch] = useState("");
  const [semester, setSemester] = useState(DEFAULT_TERM.semester);
  const [year, setYear] = useState("");
  const [view, setView] = useState<CourseView>("grid");

  const debouncedSearch = useDebouncedValue(search, 300);
  const terms = useCourseTerms();
  const availableYears = terms.data?.academic_years ?? [];
  const availableSemesters = terms.data?.semesters ?? [];
  const selectedYear = availableYears.includes(year) ? year : (availableYears[0] ?? "");
  const selectedSemester = availableSemesters.includes(semester)
    ? semester
    : (availableSemesters[0] ?? DEFAULT_TERM.semester);

  const query = useCourses({
    search: debouncedSearch.trim() || undefined,
    semester: selectedSemester || undefined,
    academic_year: selectedYear || undefined,
  });

  const filters: CourseFilterState = {
    search,
    setSearch,
    semester: selectedSemester,
    setSemester,
    year: selectedYear,
    setYear,
    semesters: availableSemesters.length ? availableSemesters : [1, 2, 3],
    years: availableYears,
    view,
    setView,
  };

  // Trả về `courses` (mảng items) cho consumer dùng trực tiếp.
  const courses: CourseSummary[] = query.data?.items ?? [];

  return {
    filters,
    query,
    courses,
  };
}
