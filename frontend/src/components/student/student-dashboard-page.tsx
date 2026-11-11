"use client";

import { useMemo, useState, useSyncExternalStore } from "react";
import {
  BookCheck,
  CalendarClock,
  CalendarDays,
  GraduationCap,
  LayoutGrid,
  List,
  Search,
} from "lucide-react";

import { CourseCard } from "@/components/shared/course-card";
import { MiniStat } from "@/components/student/mini-stat";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/context/auth-context";
import { useStudentOverview } from "@/lib/hooks/use-dashboard";
import { useLocale } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { CourseSummary, CourseView } from "@/lib/types/course";

/**
 * Trang Dashboard sinh viên.
 *
 * Layout:
 *  - Stats row: lớp đang ký, bài hoàn thành, hạn tuần này.
 *  - Toolbar: search + filter học kỳ + view switcher.
 *  - Grid/List card lớp học phần (dùng chung `CourseCard` với trang Lớp học phần
 *    để hai nơi hiển thị giống nhau: ảnh bìa theo ngôn ngữ + hiệu ứng hover).
 */

/** Giá trị đại diện cho "không lọc học kỳ" (base-ui Select không nhận value rỗng). */
const ALL_TERMS = "__all__";

export function StudentDashboardPage() {
  const auth = useAuth();
  const studentId = auth.status === "authenticated" ? auth.user.user_id : "";
  const overview = useStudentOverview(studentId);
  const { t, locale } = useLocale();

  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  const coursesWithMeta: CourseSummary[] = useMemo(() => {
    if (!overview.data) return [];
    return overview.data.courses;
  }, [overview.data]);

  // Filter state — chỉ lọc theo học kỳ (bỏ lọc "Năm học": học kỳ đã bao gồm
  // năm học trong nhãn, hai bộ lọc chồng nhau gây khó hiểu cho người dùng).
  const [search, setSearch] = useState("");
  const [term, setTerm] = useState<string>("");
  const [view, setView] = useState<CourseView>("grid");

  const terms = useMemo(() => {
    const set = new Set<string>();
    coursesWithMeta.forEach((c) => {
      const key = `${c.semester} (${c.academic_year})`;
      set.add(key);
    });
    return Array.from(set);
  }, [coursesWithMeta]);

  /** "1 (2026-2027)" -> "Học kỳ 1 (2026 - 2027)" / "Semester 1 (2026 - 2027)" */
  const termLabel = useMemo(
    () => (key: string) => {
      const value = key.replace("-", " - ");
      return locale === "en" ? `Semester ${value}` : `Học kỳ ${value}`;
    },
    [locale],
  );

  const filteredCourses = useMemo(() => {
    const q = search.trim().toLowerCase();
    return coursesWithMeta.filter((c) => {
      if (term) {
        const key = `${c.semester} (${c.academic_year})`;
        if (key !== term) return false;
      }
      if (q) {
        const hay = `${c.code} ${c.name} ${c.teacher_name}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [coursesWithMeta, search, term]);

  const statsData = useMemo(() => {
    return {
      classes: overview.data?.total_classes ?? 0,
      progress: overview.data
        ? `${overview.data.completed_problems}/${overview.data.total_problems}`
        : "—",
      dueThisWeek: overview.data?.due_this_week ?? 0,
    };
  }, [overview.data]);

  return (
    <div className="space-y-5">
      {/* ── Stats row ─────────────────────────────────────────── */}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <MiniStat
          icon={GraduationCap}
          label={t("student.dashboard.stats.enrolled")}
          value={statsData.classes}
          tone="indigo"
        />
        <MiniStat
          icon={BookCheck}
          label={t("student.dashboard.stats.completed")}
          value={statsData.progress}
          tone="emerald"
        />
        <MiniStat
          icon={CalendarClock}
          label={t("student.dashboard.stats.dueThisWeek")}
          value={statsData.dueThisWeek}
          tone="amber"
        />
      </section>

      {/* ── Toolbar ────────────────────────────────────────────── */}
      <section className="flex flex-col items-stretch gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:max-w-sm">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("student.dashboard.searchPlaceholder")}
            aria-label={t("student.dashboard.searchLabel")}
            className="h-10 w-full rounded-full border border-border bg-background pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-[#352078] focus:outline-none focus:ring-2 focus:ring-[#352078]/20"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 lg:ml-auto">
          <Select
            value={term || ALL_TERMS}
            onValueChange={(value) => setTerm(value === ALL_TERMS ? "" : (value ?? ""))}
          >
            <SelectTrigger
              aria-label={t("filter.semester")}
              className="h-10 min-w-[172px] rounded-full border border-border bg-background px-3.5 text-sm font-semibold shadow-none"
            >
              <SelectValue>
                {term ? termLabel(term) : t("filter.allSemesters")}
              </SelectValue>
            </SelectTrigger>
            <SelectContent className="rounded-xl p-1.5 shadow-lg">
              <SelectItem value={ALL_TERMS} className="rounded-lg py-2 pl-2.5">
                {t("filter.allSemesters")}
              </SelectItem>
              {terms.map((t) => (
                <SelectItem key={t} value={t} className="rounded-lg py-2 pl-2.5">
                  {termLabel(t)}
                </SelectItem>
              ))}            </SelectContent>
          </Select>

          <div className="inline-flex shrink-0 rounded-lg border border-border bg-background p-0.5">
            <button
              type="button"
              onClick={() => setView("grid")}
              aria-label={t("filter.gridView")}
              aria-pressed={view === "grid"}
              className={cn(
                "flex size-9 items-center justify-center rounded-md transition-colors",
                view === "grid"
                  ? "bg-[#352078] text-white shadow-sm"
                  : "text-foreground/60 hover:bg-muted",
              )}
            >
              <LayoutGrid className="size-4" />
            </button>
            <button
              type="button"
              onClick={() => setView("list")}
              aria-label={t("filter.listView")}
              aria-pressed={view === "list"}
              className={cn(
                "flex size-9 items-center justify-center rounded-md transition-colors",
                view === "list"
                  ? "bg-[#352078] text-white shadow-sm"
                  : "text-foreground/60 hover:bg-muted",
              )}
            >
              <List className="size-4" />
            </button>
          </div>
        </div>
      </section>

      {/* ── Courses grid ──────────────────────────────────────── */}
      {overview.isPending ? (
        <CoursesGridSkeleton />
      ) : filteredCourses.length > 0 ? (
        <div
          className={cn(
            view === "grid"
              ? "grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4"
              : "flex flex-col gap-3",
          )}
        >
          {filteredCourses.map((c) => (
            <CourseCard
              key={c.id}
              course={c}
              view={view}
              href={`/student/classes/${encodeURIComponent(String(c.id))}`}
            />
          ))}
        </div>
      ) : (
        <EmptyState mounted={mounted} noMatch={coursesWithMeta.length > 0} />
      )}
    </div>
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────

function CoursesGridSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 4 }, (_, i) => (
        <div key={i} className="overflow-hidden rounded-2xl bg-card shadow-sm">
          <div className="h-32 animate-pulse bg-gradient-to-br from-[#352078]/40 to-[#5b3aa8]/40" />
          <div className="space-y-2 p-4">
            <div className="h-3 w-16 animate-pulse rounded bg-muted" />
            <div className="h-3 w-12 animate-pulse rounded bg-muted" />
            <div className="h-4 w-3/4 animate-pulse rounded bg-muted" />
          </div>
          <div className="flex items-center justify-between border-t border-border/60 px-4 py-2.5">
            <div className="h-3 w-20 animate-pulse rounded bg-muted" />
            <div className="flex gap-3">
              <div className="h-3 w-6 animate-pulse rounded bg-muted" />
              <div className="h-3 w-6 animate-pulse rounded bg-muted" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/** `noMatch`: SV có lớp nhưng bộ lọc/tìm kiếm không khớp — khác với chưa ghi danh lớp nào. */
function EmptyState({ mounted, noMatch }: { mounted: boolean; noMatch: boolean }) {
  const { t } = useLocale();
  return (
    <div className="rounded-2xl border border-dashed border-border bg-card p-10 text-center">
      <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <CalendarDays className="size-6" />
      </div>
      <h3 className="mt-3 text-base font-semibold text-foreground">
        {mounted ? t(noMatch ? "student.classes.empty.noMatch" : "student.dashboard.empty.title") : " "}
      </h3>
      <p className="mt-1 text-sm text-muted-foreground">
        {t(noMatch ? "student.classes.empty.noMatchDesc" : "student.dashboard.empty.desc")}
      </p>
    </div>
  );
}

