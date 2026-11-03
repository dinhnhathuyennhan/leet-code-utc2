"use client";

import { useState } from "react";

import { useCourseTerms, useCourses } from "@/lib/hooks/use-courses";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import type { CourseSummary, CourseView } from "@/lib/types/course";

export interface CourseFilterState {
  search: string;
  setSearch: (value: string) => void;
  semester?: number;
  setSemester: (value?: number) => void;
  semesters: number[];
  view: CourseView;
  setView: (value: CourseView) => void;
}

/**
 * State bộ lọc + query danh sách lớp — dùng chung cho trang lớp của giảng viên và sinh viên.
 *
 * - ``search`` được đẩy xuống server (BE `GET /courses?search=...`).
 * - ``semester`` đẩy xuống server qua param tương ứng.
 * - ``view`` chỉ là state UI (grid / list), không ảnh hưởng tới request.
 *
 * Không còn bộ lọc "Năm học": học kỳ chỉ có nghĩa trong một năm học cụ thể nên
 * backend trả kèm nhãn đầy đủ; lọc thêm theo năm chỉ làm hai bộ lọc chồng nhau.
 */
export function useCourseList() {
  const [search, setSearch] = useState("");
  const [semester, setSemester] = useState<number | undefined>(undefined);
  const [view, setView] = useState<CourseView>("grid");

  const debouncedSearch = useDebouncedValue(search, 300);
  const terms = useCourseTerms();
  const availableSemesters = terms.data?.semesters ?? [];
  const selectedSemester = semester === undefined || availableSemesters.includes(semester) ? semester : undefined;

  const query = useCourses({
    search: debouncedSearch.trim() || undefined,
    semester: selectedSemester || undefined,
  });

  const filters: CourseFilterState = {
    search,
    setSearch,
    semester: selectedSemester,
    setSemester,
    semesters: availableSemesters.length ? availableSemesters : [1, 2, 3],
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
