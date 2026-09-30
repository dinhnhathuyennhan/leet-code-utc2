import { CourseCard } from "@/components/shared/course-card";
import { Skeleton } from "@/components/ui/skeleton";
import type { CourseSummary, CourseView } from "@/lib/types/course";
import { cn } from "@/lib/utils";

const LAYOUT: Record<CourseView, string> = {
  // auto-fill: tự chia 2–5 cột theo bề rộng, không cần breakpoint thủ công
  grid: "grid grid-cols-[repeat(auto-fill,minmax(15rem,1fr))] gap-5",
  list: "flex flex-col gap-3",
};

interface CourseGridProps {
  courses: CourseSummary[];
  view: CourseView;
  hrefFor: (course: CourseSummary) => string;
  className?: string;
}

export function CourseGrid({ courses, view, hrefFor, className }: CourseGridProps) {
  return (
    <div className={cn(LAYOUT[view], className)}>
      {courses.map((course) => (
        <CourseCard key={course.id} course={course} href={hrefFor(course)} view={view} />
      ))}
    </div>
  );
}

export function CourseGridSkeleton({ view }: { view: CourseView }) {
  return (
    <div className={LAYOUT[view]} aria-busy aria-label="Đang tải danh sách lớp">
      {Array.from({ length: 8 }, (_, i) => (
        <div key={i} className={cn("overflow-hidden rounded-xl border bg-card", view === "list" && "flex")}>
          <Skeleton className={cn("rounded-none", view === "list" ? "h-28 w-40 sm:w-56" : "aspect-[13/5] w-full")} />
          <div className="flex-1 space-y-3 p-4">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}
