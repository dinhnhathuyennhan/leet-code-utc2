import { GraduationCap } from "lucide-react";

import { CourseFilters } from "@/components/shared/course-filters";
import { CourseGrid, CourseGridSkeleton } from "@/components/shared/course-grid";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import type { CourseFilterState } from "@/lib/hooks/use-course-list";
import type { CourseSummary } from "@/lib/types/course";
import { cn } from "@/lib/utils";

interface CourseListViewProps {
  role: "teacher" | "student";
  filters: CourseFilterState;
  courses?: CourseSummary[];
  isLoading: boolean;
  /** Đang tải lại (đổi bộ lọc) — làm mờ lưới thay vì nhấp nháy skeleton. */
  isFetching: boolean;
  error: unknown;
  onRetry: () => void;
  hrefFor: (course: CourseSummary) => string;
}

/**
 * Màn hình danh sách lớp — thuần hiển thị, dữ liệu do page truyền xuống.
 * Stats bar đã bỏ (BE chưa trả); sẽ thêm lại khi endpoint bổ sung.
 */
export function CourseListView({
  role,
  filters,
  courses,
  isLoading,
  isFetching,
  error,
  onRetry,
  hrefFor,
}: CourseListViewProps) {
  const heading = role === "teacher" ? "Lớp phụ trách" : "Lớp đang học";

  function renderBody() {
    if (isLoading) return <CourseGridSkeleton view={filters.view} />;
    if (error && !courses) return <ErrorState error={error} onRetry={onRetry} />;
    if (!courses?.length) {
      return (
        <EmptyState
          icon={GraduationCap}
          title={filters.search ? "Không tìm thấy lớp phù hợp" : `Chưa có ${heading.toLowerCase()}`}
          description={filters.search ? "Thử đổi từ khoá khác." : "Các lớp của bạn sẽ hiển thị tại đây."}
        />
      );
    }
    return (
      <CourseGrid
        view={filters.view}
        courses={courses}
        hrefFor={hrefFor}
        className={cn("transition-opacity duration-200", isFetching && "opacity-60")}
      />
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{heading}</h1>
      </header>
      <CourseFilters filters={filters} />
      {renderBody()}
    </div>
  );
}