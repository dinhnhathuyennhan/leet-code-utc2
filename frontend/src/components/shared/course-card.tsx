import Link from "next/link";
import { BookOpen, CalendarDays, Users } from "lucide-react";

import { formatDate } from "@/lib/helpers/format";
import type { CourseSummary } from "@/lib/types/course";
import { cn } from "@/lib/utils";

interface CourseCardProps {
  course: CourseSummary;
  href: string;
}

/**
 * Thẻ lớp học phần — đơn giản vì BE hiện chỉ trả vài trường cốt lõi.
 * Khi BE bổ sung `language`/`teacher_name`/`avt_link` thì thêm ảnh bìa + tên GV.
 */
export function CourseCard({ course, href }: CourseCardProps) {
  return (
    <Link
      href={href}
      className={cn(
        "group block rounded-xl border bg-card p-5 shadow-sm outline-none transition duration-200 hover:-translate-y-0.5 hover:shadow-lg focus-visible:ring-2 focus-visible:ring-indigo-500",
      )}
    >
      <div className="space-y-3">
        <span className="inline-block rounded-md bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
          {course.code}
        </span>
        <h3 className="line-clamp-2 text-lg font-semibold leading-snug">{course.name}</h3>

        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <BookOpen className="size-4 shrink-0" />
          <span className="truncate">{course.term}</span>
        </p>

        <div className="grid grid-cols-2 gap-2 pt-1 text-sm text-muted-foreground">
          <p className="flex items-center gap-2">
            <CalendarDays className="size-4 shrink-0" />
            <span className="truncate">{formatDate(course.start_date)}</span>
          </p>
          <p className="flex items-center gap-2">
            <Users className="size-4 shrink-0" />
            <span>{course.total_number_student} SV</span>
          </p>
        </div>
      </div>
    </Link>
  );
}