"use client";

import { LayoutGrid, List, Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { ACADEMIC_YEARS, SEMESTERS } from "@/lib/constants/academic";
import type { CourseFilterState } from "@/lib/hooks/use-course-list";
import type { CourseView } from "@/lib/types/course";

const VIEW_ITEM =
  "size-8 rounded-md text-slate-500 data-[state=on]:bg-card data-[state=on]:text-indigo-600 data-[state=on]:shadow-sm";

export function CourseFilters({ filters }: { filters: CourseFilterState }) {
  const { search, setSearch, semester, setSemester, year, setYear, view, setView } = filters;

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

      <div className="flex flex-wrap items-center gap-3">
        <Select value={String(semester)} onValueChange={(value) => value && setSemester(Number(value))}>
          <SelectTrigger aria-label="Học kỳ" className="h-11 w-32 bg-card">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SEMESTERS.map((s) => (
              <SelectItem key={s} value={String(s)}>Học kỳ {s}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={year} onValueChange={(value) => value && setYear(value)}>
          <SelectTrigger aria-label="Năm học" className="h-11 w-48 bg-card">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ACADEMIC_YEARS.map((y) => (
              <SelectItem key={y} value={y}>Năm học {y.replace("-", " - ")}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <ToggleGroup
          type="single"
          value={view}
          onValueChange={(value) => value && setView(value as CourseView)}
          aria-label="Kiểu hiển thị"
          className="rounded-lg bg-indigo-50 p-1 dark:bg-slate-800"
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
