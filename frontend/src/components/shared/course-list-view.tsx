import { BookOpen, ClipboardCheck, GraduationCap, Timer } from "lucide-react";
import type { ReactNode } from "react";

import { CourseFilters } from "@/components/shared/course-filters";
import { CourseGrid, CourseGridSkeleton } from "@/components/shared/course-grid";
import { CourseStatsBar, CourseStatsBarSkeleton, type StatItem } from "@/components/shared/course-stats-bar";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { useLocale } from "@/lib/i18n";
import type { CourseFilterState } from "@/lib/hooks/use-course-list";
import type { CourseListStats, CourseSummary } from "@/lib/types/course";
import { cn } from "@/lib/utils";

interface CourseListViewProps {
  role: "teacher" | "student";
  filters: CourseFilterState;
  courses?: CourseSummary[];
  stats?: CourseListStats;
  isLoading: boolean;
  isFetching: boolean;
  error: unknown;
  onRetry: () => void;
  hrefFor: (course: CourseSummary) => string;
  actions?: ReactNode;
}

export function CourseListView({ role, filters, courses, stats, isLoading, isFetching, error, onRetry, hrefFor, actions }: CourseListViewProps) {
  const { t } = useLocale();
  const heading = role === "teacher" ? t("teacher.courses.heading") : t("student.classes.heading");

  function buildStats(stats: CourseListStats): StatItem[] {
    return [
      {
        icon: BookOpen,
        value: String(stats.active_course_count),
        label: role === "teacher" ? t("student.classes.stats.teaching") : t("student.classes.stats.learning"),
      },
      { icon: ClipboardCheck, value: String(stats.upcoming_courses), label: t("student.classes.stats.upcoming") },
      { icon: Timer, value: String(stats.due_this_week), label: t("student.dashboard.stats.dueThisWeek"), highlight: true },
    ];
  }

  function renderBody() {
    if (isLoading) return <CourseGridSkeleton view={filters.view} />;
    if (error && !courses) return <ErrorState error={error} onRetry={onRetry} />;
    if (!courses?.length) {
      return (
        <EmptyState
          icon={GraduationCap}
          title={filters.search ? t("student.classes.empty.noMatch") : t("student.classes.empty.title")}
          description={filters.search ? t("student.classes.empty.noMatchDesc") : t("student.classes.empty.desc")}
        />
      );
    }
    return <CourseGrid view={filters.view} courses={courses} hrefFor={hrefFor} className={cn("transition-opacity duration-200", isFetching && "opacity-60")} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        {isLoading || !stats ? <CourseStatsBarSkeleton /> : <CourseStatsBar items={buildStats(stats)} />}
        {actions && <div className="flex justify-end">{actions}</div>}
      </div>
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{heading}</h1>
      </header>
      <CourseFilters filters={filters} />
      {renderBody()}
    </div>
  );
}
