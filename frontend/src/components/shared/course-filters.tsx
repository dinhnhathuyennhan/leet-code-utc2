"use client";

import { Filter, Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { CourseFilterState } from "@/lib/hooks/use-course-list";

/**
 * Thanh filter — search + chọn học kỳ.
 *
 * - ``search``: lọc client-side theo tên/mã lớp.
 * - ``term``: đẩy xuống server (`GET /courses?term=<giá trị>`).
 *   BE trả các lớp có cột `term` chứa chuỗi này (LIKE %term%).
 *   Dropdown chỉ hiển thị các term có thật trong data của user,
 *   FE tự suy ra từ response.
 */
export function CourseFilters({ filters }: { filters: CourseFilterState }) {
  const { search, setSearch, term, setTerm, availableTerms } = filters;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="relative w-full sm:max-w-md sm:flex-1">
        <Search
          aria-hidden
          className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
        />
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Tìm kiếm lớp học phần..."
          aria-label="Tìm kiếm lớp học phần"
          className="h-11 bg-card pl-10"
        />
      </div>

      {availableTerms.length > 0 && (
        <div className="flex items-center gap-2">
          <Filter className="size-4 text-muted-foreground" aria-hidden />
          <Select
            value={term || "__all__"}
            onValueChange={(value) => setTerm(value === "__all__" || value == null ? "" : value)}
          >
            <SelectTrigger
              className="h-11 min-w-48 bg-card"
              aria-label="Lọc theo học kỳ"
            >
              <SelectValue placeholder="Tất cả học kỳ" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">Tất cả học kỳ</SelectItem>
              {availableTerms.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
    </div>
  );
}
