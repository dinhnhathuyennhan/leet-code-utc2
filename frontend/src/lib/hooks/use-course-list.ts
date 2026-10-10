"use client";

import { useMemo, useState } from "react";

import { useCourses } from "@/lib/hooks/use-courses";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";

export interface CourseFilterState {
  search: string;
  setSearch: (value: string) => void;
  /** Học kỳ hiện chọn, dùng để gọi `GET /courses?term=<giá trị>`. */
  term: string;
  setTerm: (value: string) => void;
  /** Danh sách các term có sẵn (FE suy ra từ data trả về) để dựng dropdown. */
  availableTerms: string[];
}

/**
 * State bộ lọc + query danh sách lớp — dùng chung cho trang lớp của giảng viên và sinh viên.
 *
 * - ``search`` lọc client-side (nhanh, không cần BE hỗ trợ).
 * - ``term`` được đẩy xuống server qua `GET /courses?term=<giá trị>` (BE LIKE %%term%%).
 *
 * Danh sách ``availableTerms`` được FE suy ra từ chính kết quả trả về: gọi
 * 1 lần không filter, lấy unique term, sort theo thứ tự năm học mới nhất.
 */
export function useCourseList() {
  const [search, setSearch] = useState("");
  const [term, setTerm] = useState<string>(""); // "" = tất cả
  const debouncedSearch = useDebouncedValue(search, 300);

  // Lần 1: gọi không filter để lấy danh sách term có sẵn.
  const allQuery = useCourses({});

  // Lần 2: gọi có filter term (khi user đã chọn term cụ thể).
  const filteredQuery = useCourses(term ? { term } : {});

  // Dùng query có filter làm source chính (nếu user đã chọn term), không thì dùng allQuery.
  const baseQuery = term ? filteredQuery : allQuery;

  // Tính availableTerms từ allQuery.data (dữ liệu gốc, không filter).
  const availableTerms = useMemo(() => {
    if (!allQuery.data) return [];
    const set = new Set<string>();
    for (const c of allQuery.data) {
      if (c.term) set.add(c.term);
    }
    // Sắp xếp: tách theo năm học trong ngoặc nếu có, năm mới hơn lên trước.
    return Array.from(set).sort((a, b) => {
      const ya = a.match(/(\d{4})/g)?.map(Number) ?? [];
      const yb = b.match(/(\d{4})/g)?.map(Number) ?? [];
      // so sánh năm cuối cùng (kết thúc năm học)
      const lastA = ya[ya.length - 1] ?? 0;
      const lastB = yb[yb.length - 1] ?? 0;
      if (lastA !== lastB) return lastB - lastA;
      return a.localeCompare(b);
    });
  }, [allQuery.data]);

  // Lọc client-side theo search (term đã filter server-side rồi).
  const items = baseQuery.data;
  const filtered = useMemo(() => {
    if (!items) return undefined;
    const needle = debouncedSearch.trim().toLowerCase();
    if (!needle) return items;
    return items.filter(
      (c) =>
        c.name.toLowerCase().includes(needle) ||
        c.code.toLowerCase().includes(needle),
    );
  }, [items, debouncedSearch]);

  const filters: CourseFilterState = {
    search,
    setSearch,
    term,
    setTerm,
    availableTerms,
  };

  return {
    filters,
    query: {
      ...baseQuery,
      data: filtered === undefined ? undefined : { items: filtered, stats: undefined },
    },
  };
}
