import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { StatusBadge } from "@/components/shared/status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { COURSE_STATUS } from "@/lib/constants/status";
import { formatTerm } from "@/lib/helpers/format";
import type { CourseSummary } from "@/lib/types/course";

interface RecentCoursesProps {
  courses: CourseSummary[];
  hrefFor: (course: CourseSummary) => string;
}

export function RecentCourses({ courses, hrefFor }: RecentCoursesProps) {
  return (
    <ul className="-mx-1 flex snap-x gap-4 overflow-x-auto px-1 pb-3">
      {courses.map((course) => {
        const status = COURSE_STATUS[course.status];
        return (
          <li key={course.id} className="w-[19rem] shrink-0 snap-start">
            <Link
              href={hrefFor(course)}
              className="group flex items-center justify-between gap-3 rounded-xl border bg-card p-5 shadow-sm outline-none transition duration-200 hover:-translate-y-0.5 hover:shadow-lg focus-visible:ring-2 focus-visible:ring-indigo-500"
            >
              <div className="min-w-0 space-y-2">
                <StatusBadge label={status.label} tone={status.tone} />
                <p className="truncate text-lg font-semibold">{course.name}</p>
                <p className="truncate text-sm text-muted-foreground">{formatTerm(course)}</p>
              </div>
              <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white transition-transform duration-200 group-hover:translate-x-0.5">
                <ArrowRight className="size-5" />
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
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
