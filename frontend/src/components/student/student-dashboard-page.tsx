"use client";

import { useMemo, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import {
  Bell,
  BookCheck,
  CalendarClock,
  CalendarDays,
  ChevronDown,
  GraduationCap,
  LayoutGrid,
  List,
  Search,
  SlidersHorizontal,
} from "lucide-react";

import {
  DashboardCourseCard,
  LANGUAGE_THEMES,
  MiniStat,
  resolveLanguage,
} from "@/components/student/dashboard-course-card";
import { useAuth } from "@/context/auth-context";
import { useStudentOverview } from "@/lib/hooks/use-dashboard";
import { cn } from "@/lib/utils";
import type { CourseSummary, CourseView } from "@/lib/types/course";

/**
 * Trang Dashboard sinh viên.
 *
 * Layout:
 *  - Stats row: lớp đang ký, bài hoàn thành, hạn tuần này.
 *  - Toolbar: search + filter học kỳ + năm học + view switcher.
 *  - Grid/List card lớp học phần.
 */
export function StudentDashboardPage() {
  const auth = useAuth();
  const studentId = auth.status === "authenticated" ? auth.user.user_id : "";
  const overview = useStudentOverview(studentId);

  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  const coursesWithMeta: CourseSummary[] = useMemo(() => {
    if (!overview.data) return [];
    return overview.data.courses;
  }, [overview.data]);

  // Filter state
  const [search, setSearch] = useState("");
  const [term, setTerm] = useState<string>("");
  const [year, setYear] = useState<string>("2024 - 2025");
  const [view, setView] = useState<CourseView>("grid");

  const terms = useMemo(() => {
    const set = new Set<string>();
    coursesWithMeta.forEach((c) => {
      const key = `${c.semester} (${c.academic_year})`;
      set.add(key);
    });
    return Array.from(set);
  }, [coursesWithMeta]);

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
      dueThisWeek: 2, // mock — BE chưa trả
    };
  }, [overview.data]);

  return (
    <div className="space-y-5">
      {/* ── Stats row ─────────────────────────────────────────── */}
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <MiniStat
          icon={GraduationCap}
          label="Lớp đang ký"
          value={statsData.classes}
          tone="indigo"
        />
        <MiniStat
          icon={BookCheck}
          label="Bài hoàn thành"
          value={statsData.progress}
          tone="emerald"
        />
        <MiniStat
          icon={CalendarClock}
          label="Hạn tuần này"
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
            placeholder="Tìm kiếm lớp học phần…"
            aria-label="Tìm kiếm lớp học phần"
            className="h-10 w-full rounded-full border border-border bg-background pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-[#352078] focus:outline-none focus:ring-2 focus:ring-[#352078]/20"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 lg:ml-auto">
          <FilterDropdown
            label="Học kỳ"
            value={term}
            onChange={setTerm}
            options={[
              { value: "", label: "Tất cả học kỳ" },
              ...terms.map((t) => ({ value: t, label: t })),
            ]}
          />

          <FilterDropdown
            label="Năm học"
            value={year}
            onChange={setYear}
            options={[
              { value: "2024 - 2025", label: "2024 - 2025" },
              { value: "2023 - 2024", label: "2023 - 2024" },
              { value: "2022 - 2023", label: "2022 - 2023" },
            ]}
          />

          <button
            type="button"
            title="Bộ lọc nâng cao"
            aria-label="Bộ lọc nâng cao"
            className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border text-foreground/60 transition-colors hover:bg-muted sm:flex"
          >
            <SlidersHorizontal className="size-4" />
          </button>

          <div className="inline-flex shrink-0 rounded-lg border border-border bg-background p-0.5">
            <button
              type="button"
              onClick={() => setView("grid")}
              aria-label="Xem dạng lưới"
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
              aria-label="Xem dạng danh sách"
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
        view === "grid" ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredCourses.map((c, i) => (
              <DashboardCourseCard
                key={c.id}
                course={c}
                language={c.language}
                teacherName={c.teacher_name}
                status={c.status}
                messageCount={(i + 1) * 3}
                memberCount={0}
                href={`/student/classes/${encodeURIComponent(String(c.id))}`}
              />
            ))}
          </div>
        ) : (
          <CourseList courses={filteredCourses} />
        )
      ) : (
        <EmptyState mounted={mounted} />
      )}
    </div>
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────

interface FilterDropdownProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}

function FilterDropdown({ label, value, onChange, options }: FilterDropdownProps) {
  const selected = options.find((o) => o.value === value) ?? options[0];
  return (
    <label className="relative flex h-10 shrink-0 items-center gap-2 rounded-lg border border-border bg-background px-3 text-sm hover:border-foreground/30">
      <span className="text-xs font-medium text-muted-foreground">{label}:</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={label}
        className="appearance-none bg-transparent pr-5 text-sm font-semibold text-foreground outline-none"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
      <span className="sr-only">{selected?.label}</span>
    </label>
  );
}

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

function EmptyState({ mounted }: { mounted: boolean }) {
  return (
    <div className="rounded-2xl border border-dashed border-border bg-card p-10 text-center">
      <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <CalendarDays className="size-6" />
      </div>
      <h3 className="mt-3 text-base font-semibold text-foreground">
        {mounted ? "Chưa có lớp học phần nào" : " "}
      </h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Bạn chưa được ghi danh vào lớp nào trong kỳ này. Liên hệ giáo viên hoặc admin.
      </p>
    </div>
  );
}

function CourseList({ courses }: { courses: CourseSummary[] }) {
  return (
    <ul className="overflow-hidden rounded-2xl bg-card shadow-sm">
      {courses.map((c, i) => {
        const theme = LANGUAGE_THEMES[resolveLanguage(c.language)] ?? LANGUAGE_THEMES.default;
        return (
          <li
            key={c.id}
            className={cn(
              "transition-colors hover:bg-muted/30",
              i > 0 && "border-t border-border/60",
            )}
          >
            <Link
              href={`/student/classes/${encodeURIComponent(String(c.id))}`}
              className="flex items-center gap-4 px-4 py-3 outline-none focus-visible:ring-2 focus-visible:ring-[#352078]"
            >
              <div
                className={cn(
                  "flex h-12 w-14 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br text-xs font-bold text-white",
                  theme.gradient,
                )}
              >
                {theme.display}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-muted-foreground">{c.code}</span>
                  <span className="truncate text-sm font-semibold text-foreground">{c.name}</span>
                </div>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">
                  Học kỳ {c.semester} ({c.academic_year.replace("-", " - ")})
                </p>
              </div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

// ─── Re-exports (cho callers cũ) ──────────────────────────────────
export { Bell };
