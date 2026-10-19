import { BookOpen, ClipboardCheck, GraduationCap, Timer } from "lucide-react";
import type { ReactNode } from "react";

import { CourseFilters } from "@/components/shared/course-filters";
import { CourseGrid, CourseGridSkeleton } from "@/components/shared/course-grid";
import { CourseStatsBar, CourseStatsBarSkeleton, type StatItem } from "@/components/shared/course-stats-bar";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
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

function buildStats(role: CourseListViewProps["role"], stats: CourseListStats): StatItem[] {
  return [
    { icon: BookOpen, value: String(stats.active_course_count), label: role === "teacher" ? "Lớp phụ trách" : "Lớp đang học" },
    { icon: ClipboardCheck, value: String(stats.upcoming_courses), label: "Lớp sắp mở" },
    { icon: Timer, value: String(stats.due_this_week), label: "Hạn tuần này", highlight: true },
  ];
}

export function CourseListView({ role, filters, courses, stats, isLoading, isFetching, error, onRetry, hrefFor, actions }: CourseListViewProps) {
  const heading = role === "teacher" ? "Lớp phụ trách" : "Lớp đang học";

  function renderBody() {
    if (isLoading) return <CourseGridSkeleton view={filters.view} />;
    if (error && !courses) return <ErrorState error={error} onRetry={onRetry} />;
    if (!courses?.length) {
      return <EmptyState icon={GraduationCap} title={filters.search ? "Không tìm thấy lớp phù hợp" : `Chưa có ${heading.toLowerCase()}`} description={filters.search ? "Thử đổi từ khoá khác." : "Các lớp của bạn sẽ hiển thị tại đây."} />;
    }
    return <CourseGrid view={filters.view} courses={courses} hrefFor={hrefFor} className={cn("transition-opacity duration-200", isFetching && "opacity-60")} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        {isLoading || !stats ? <CourseStatsBarSkeleton /> : <CourseStatsBar items={buildStats(role, stats)} />}
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
