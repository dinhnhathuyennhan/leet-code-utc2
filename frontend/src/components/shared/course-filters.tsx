"use client";

import { LayoutGrid, List, Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { CourseFilterState } from "@/lib/hooks/use-course-list";
import type { CourseView } from "@/lib/types/course";

const VIEW_ITEM =
  "inline-flex h-8 w-8 items-center justify-center rounded-md p-0 text-slate-500 data-[state=on]:bg-card data-[state=on]:text-indigo-600 data-[state=on]:shadow-sm";

export function CourseFilters({ filters }: { filters: CourseFilterState }) {
  const { search, setSearch, semester, setSemester, year, setYear, view, setView } = filters;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="relative w-full sm:max-w-xs sm:flex-1">
        <Search aria-hidden className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Tìm kiếm lớp học phần..."
          aria-label="Tìm kiếm lớp học phần"
          className="h-9 border-0 bg-card pl-10 shadow-none"
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Select value={semester === undefined ? "__all_semester__" : String(semester)} onValueChange={(value) => setSemester(value === "__all_semester__" ? undefined : Number(value))}>
          <SelectTrigger aria-label="Học kỳ" className="h-9 w-24 border-0 bg-card shadow-none">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all_semester__">Tất cả học kỳ</SelectItem>
            {filters.semesters.map((s) => (
              <SelectItem key={s} value={String(s)}>Học kỳ {s}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={year || "__all_year__"} onValueChange={(value) => value && setYear(value === "__all_year__" ? "" : value)}>
          <SelectTrigger aria-label="Năm học" className="h-9 w-40 border-0 bg-card shadow-none">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all_year__">Tất cả năm học</SelectItem>
            {filters.years.map((y) => (
              <SelectItem key={y} value={y}>Năm học {y.replace("-", " - ")}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <ToggleGroup
          type="single"
          value={view}
          onValueChange={(value) => value && setView(value as CourseView)}
          aria-label="Kiểu hiển thị"
          className="inline-flex h-10 items-center gap-1 rounded-lg bg-indigo-50 p-1 dark:bg-slate-800"
        >
          <ToggleGroupItem value="grid" aria-label="Dạng lưới" className={VIEW_ITEM}>
            <LayoutGrid className="size-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="list" aria-label="Dạng danh sách" className={VIEW_ITEM}>
            <List className="size-4" />
          </ToggleGroupItem>
        </ToggleGroup>
      </div>
    </div>
  );
}
