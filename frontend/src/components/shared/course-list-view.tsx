import { BookOpen, ClipboardCheck, Timer } from "lucide-react";

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
  /** Đang tải lại (đổi bộ lọc) — làm mờ lưới thay vì nhấp nháy skeleton. */
  isFetching: boolean;
  error: unknown;
  onRetry: () => void;
  hrefFor: (course: CourseSummary) => string;
}

function buildStats(role: CourseListViewProps["role"], stats: CourseListStats): StatItem[] {
  return [
    { icon: BookOpen, value: String(stats.course_count), label: role === "teacher" ? "Lớp phụ trách" : "Lớp đăng ký" },
    { icon: ClipboardCheck, value: `${stats.completed_problems}/${stats.total_problems}`, label: "Bài hoàn thành" },
    { icon: Timer, value: String(stats.due_this_week), label: "Hạn tuần này", highlight: true },
  ];
}

/** Màn hình danh sách lớp — thuần hiển thị, dữ liệu do page truyền xuống. */
export function CourseListView({ role, filters, courses, stats, isLoading, isFetching, error, onRetry, hrefFor }: CourseListViewProps) {
  function renderBody() {
    if (isLoading) return <CourseGridSkeleton view={filters.view} />;
    if (error && !courses) return <ErrorState error={error} onRetry={onRetry} />;
    if (!courses?.length) {
      return (
        <EmptyState
          title={filters.search ? "Không tìm thấy lớp phù hợp" : "Chưa có lớp học phần"}
          description={filters.search ? "Thử đổi từ khoá hoặc học kỳ, năm học khác." : "Các lớp trong học kỳ này sẽ hiển thị tại đây."}
        />
      );
    }
    return (
      <CourseGrid
        courses={courses}
        view={filters.view}
        hrefFor={hrefFor}
        className={cn("transition-opacity duration-200", isFetching && "opacity-60")}
      />
    );
  }

  return (
    <div className="space-y-6">
      {isLoading || !stats ? <CourseStatsBarSkeleton /> : <CourseStatsBar items={buildStats(role, stats)} />}
      <CourseFilters filters={filters} />
      {renderBody()}
    </div>
  );
}
