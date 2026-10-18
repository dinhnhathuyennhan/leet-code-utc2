import { Skeleton } from "@/components/ui/skeleton";
import type { CourseSummary } from "@/lib/types/course";

interface RecentCoursesProps {
  courses: CourseSummary[];
  hrefFor: (course: CourseSummary) => string;
}

/** Component tạm — Phase 1 chưa dùng, giữ skeleton để TS pass. */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function RecentCourses(_props: RecentCoursesProps) {
  return null;
}

export function RecentCoursesSkeleton() {
  return (
    <div className="flex gap-4 overflow-hidden">
      {[0, 1, 2, 3].map((i) => (
        <Skeleton key={i} className="h-[7.5rem] w-[19rem] shrink-0 rounded-xl" />
      ))}
    </div>
  );
}