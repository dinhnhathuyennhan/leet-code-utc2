"use client";

import { useState } from "react";

import { DEFAULT_TERM } from "@/lib/constants/academic";
import { useCourses } from "@/lib/hooks/use-courses";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import type { CourseView } from "@/lib/types/course";

export interface CourseFilterState {
  search: string;
  setSearch: (value: string) => void;
  semester: number;
  setSemester: (value: number) => void;
  year: string;
  setYear: (value: string) => void;
  view: CourseView;
  setView: (value: CourseView) => void;
}

/** State bộ lọc + query danh sách lớp — dùng chung cho trang lớp của giảng viên và sinh viên. */
export function useCourseList() {
  const [search, setSearch] = useState("");
  const [semester, setSemester] = useState(DEFAULT_TERM.semester);
  const [year, setYear] = useState(DEFAULT_TERM.academicYear);
  const [view, setView] = useState<CourseView>("grid");

  const debouncedSearch = useDebouncedValue(search, 300);
  const query = useCourses({
    search: debouncedSearch.trim() || undefined,
    semester,
    academic_year: year,
  });

  const filters: CourseFilterState = { search, setSearch, semester, setSemester, year, setYear, view, setView };
  return { filters, query };
}
