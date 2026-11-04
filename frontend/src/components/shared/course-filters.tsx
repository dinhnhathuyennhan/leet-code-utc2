"use client";

import { LayoutGrid, List, Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useLocale } from "@/lib/i18n";
import type { CourseFilterState } from "@/lib/hooks/use-course-list";
import type { CourseView } from "@/lib/types/course";

const VIEW_ITEM =
  "inline-flex h-8 w-8 items-center justify-center rounded-md p-0 text-slate-500 data-[state=on]:bg-card data-[state=on]:text-indigo-600 data-[state=on]:shadow-sm";

/** Giá trị đại diện cho "không lọc học kỳ" (base-ui Select không nhận value rỗng). */
const ALL_SEMESTERS = "__all__";

export function CourseFilters({ filters }: { filters: CourseFilterState }) {
  const { search, setSearch, semester, setSemester, view, setView } = filters;
  const { t } = useLocale();

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="relative w-full sm:max-w-xs sm:flex-1">
        <Search aria-hidden className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder={t("student.classes.searchPlaceholder")}
          aria-label={t("student.dashboard.searchLabel")}
          className="h-9 border-0 bg-card pl-10 shadow-none"
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={semester === undefined ? ALL_SEMESTERS : String(semester)}
          onValueChange={(value) =>
            setSemester(value === ALL_SEMESTERS ? undefined : Number(value))
          }
        >
          <SelectTrigger
            aria-label={t("filter.semester")}
            className="h-9 min-w-[150px] rounded-lg border-0 bg-card px-3 text-sm font-medium shadow-none"
          >
            <SelectValue>
              {semester === undefined
                ? t("filter.allSemesters")
                : `${t("filter.semester")} ${semester}`}
            </SelectValue>
          </SelectTrigger>
          <SelectContent className="rounded-xl p-1.5 shadow-lg">
            <SelectItem value={ALL_SEMESTERS} className="rounded-lg py-2 pl-2.5">
              {t("filter.allSemesters")}
            </SelectItem>
            {filters.semesters.map((s) => (
              <SelectItem key={s} value={String(s)} className="rounded-lg py-2 pl-2.5">
                {t("filter.semester")} {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <ToggleGroup
          type="single"
          value={view}
          onValueChange={(value) => value && setView(value as CourseView)}
          aria-label={t("filter.viewMode")}
          className="inline-flex h-10 items-center gap-1 rounded-lg bg-indigo-50 p-1 dark:bg-slate-800"
        >
          <ToggleGroupItem value="grid" aria-label={t("filter.gridView")} className={VIEW_ITEM}>
            <LayoutGrid className="size-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="list" aria-label={t("filter.listView")} className={VIEW_ITEM}>
            <List className="size-4" />
          </ToggleGroupItem>
        </ToggleGroup>
      </div>
    </div>
  );
}
