"use client";

import { useState } from "react";

import { useCourseTerms, useCourses } from "@/lib/hooks/use-courses";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import type { CourseView } from "@/lib/types/course";

export interface CourseFilterState {
  search: string;
  setSearch: (value: string) => void;
  semester?: number;
  setSemester: (value?: number) => void;
  semesters: number[];
  year: string;
  setYear: (value: string) => void;
  years: string[];
  view: CourseView;
  setView: (value: CourseView) => void;
}

/** State bộ lọc + query danh sách lớp — dùng chung cho trang lớp của giảng viên và sinh viên. */
export function useCourseList() {
  const [search, setSearch] = useState("");
  const [semester, setSemester] = useState<number | undefined>(undefined);
  const [year, setYear] = useState("");
  const [view, setView] = useState<CourseView>("grid");

  const debouncedSearch = useDebouncedValue(search, 300);
  const terms = useCourseTerms();
  const availableYears = terms.data?.academic_years ?? [];
  const availableSemesters = terms.data?.semesters ?? [];
  const selectedYear = year === "" || availableYears.includes(year) ? year : "";
  const selectedSemester = semester === undefined || availableSemesters.includes(semester) ? semester : undefined;
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
  return { filters, query };
}
