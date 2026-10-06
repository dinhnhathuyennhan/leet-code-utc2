import { CourseCard } from "@/components/shared/course-card";
import { Skeleton } from "@/components/ui/skeleton";
import type { CourseSummary } from "@/lib/types/course";
import { cn } from "@/lib/utils";

const LAYOUT = "grid grid-cols-[repeat(auto-fill,minmax(15rem,1fr))] gap-5";

interface CourseGridProps {
  courses: CourseSummary[];
  hrefFor: (course: CourseSummary) => string;
  className?: string;
}

export function CourseGrid({ courses, hrefFor, className }: CourseGridProps) {
  return (
    <div className={cn(LAYOUT, className)}>
      {courses.map((course) => (
        <CourseCard key={course.id} course={course} href={hrefFor(course)} />
      ))}
    </div>
  );
}

export function CourseGridSkeleton() {
  return (
    <div className={LAYOUT} aria-busy aria-label="Đang tải danh sách lớp">
      {Array.from({ length: 8 }, (_, i) => (
        <div key={i} className="space-y-3 rounded-xl border bg-card p-5">
          <Skeleton className="h-5 w-20" />
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-2/3" />
          <div className="flex gap-4 pt-1">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-16" />
          </div>
        </div>
      ))}
    </div>
  );
}