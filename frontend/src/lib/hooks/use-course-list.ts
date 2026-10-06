"use client";

import { useMemo, useState } from "react";

import { useCourses } from "@/lib/hooks/use-courses";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";

export interface CourseFilterState {
  search: string;
  setSearch: (value: string) => void;
}

/**
 * State bộ lọc + query danh sách lớp — dùng chung cho trang lớp của giảng viên và sinh viên.
 *
 * Lưu ý: Backend hiện chưa hỗ trợ filter (xem `docs/api-design-course.md`,
 * `GET /courses` chỉ trả toàn bộ lớp scope theo role). Search ở FE chỉ lọc
 * client-side; khi BE bổ sung thì chuyển sang filter server.
 */
export function useCourseList() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const base = useCourses({});

  const items = base.data;
  const filtered = useMemo(() => {
    if (!items) return undefined;
    const needle = debouncedSearch.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((c) =>
      c.name.toLowerCase().includes(needle) || c.code.toLowerCase().includes(needle),
    );
  }, [items, debouncedSearch]);

  const filters: CourseFilterState = { search, setSearch };
  return {
    filters,
    query: {
      ...base,
      data: filtered === undefined ? undefined : { items: filtered, stats: undefined },
    },
  };
}