"use client";

import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import type { CourseFilterState } from "@/lib/hooks/use-course-list";

/**
 * Thanh filter — chỉ còn ô search vì BE chưa hỗ trợ filter list.
 * Khi BE bổ sung `search/semester/academic_year` cho `GET /courses`,
 * thêm Select/Toggle vào lại; xem `use-course-list.ts`.
 */
export function CourseFilters({ filters }: { filters: CourseFilterState }) {
  const { search, setSearch } = filters;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="relative w-full sm:max-w-md sm:flex-1">
        <Search aria-hidden className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Tìm kiếm lớp học phần..."
          aria-label="Tìm kiếm lớp học phần"
          className="h-11 bg-card pl-10"
        />
      </div>
    </div>
  );
}