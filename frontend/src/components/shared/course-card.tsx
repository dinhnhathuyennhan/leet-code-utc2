import Image from "next/image";
import Link from "next/link";
import { CalendarDays, CircleUser } from "lucide-react";

import { StatusBadge } from "@/components/shared/status-badge";
import { COURSE_COVERS } from "@/lib/constants/course-covers";
import { COURSE_STATUS } from "@/lib/constants/status";
import { formatTerm } from "@/lib/helpers/format";
import type { CourseSummary, CourseView } from "@/lib/types/course";
import { cn } from "@/lib/utils";

interface CourseCardProps {
  course: CourseSummary;
  href: string;
  view: CourseView;
}

/** Thẻ lớp học phần — dùng chung cho giảng viên và sinh viên, có 2 kiểu hiển thị lưới/danh sách. */
export function CourseCard({ course, href, view }: CourseCardProps) {
  const status = COURSE_STATUS[course.status];
  const isList = view === "list";

  return (
    <Link
      href={href}
      className={cn(
        "group overflow-hidden rounded-xl border bg-card shadow-sm outline-none transition duration-200 hover:-translate-y-0.5 hover:shadow-lg focus-visible:ring-2 focus-visible:ring-indigo-500",
        isList ? "flex items-stretch" : "block",
      )}
    >
      <div className={cn("relative shrink-0 overflow-hidden bg-slate-900", isList ? "w-40 sm:w-56" : "aspect-[13/5] w-full")}>
        <Image
          src={COURSE_COVERS[course.language]}
          alt=""
          fill
          sizes={isList ? "224px" : "(min-width: 1536px) 20vw, (min-width: 1024px) 30vw, 90vw"}
          className="object-cover transition-transform duration-300 group-hover:scale-105"
        />
      </div>

      <div className={cn("space-y-2.5 p-4", isList && "flex flex-1 flex-col justify-center")}>
        <StatusBadge label={status.label} tone={status.tone} className="w-fit" />
        <h3 className="text-lg font-semibold leading-snug">{course.name}</h3>
        <p className="flex items-center gap-2 text-sm font-medium">
          <CircleUser className="size-4 shrink-0 text-muted-foreground" />
          <span className="truncate">{course.teacher_name}</span>
        </p>
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          <CalendarDays className="size-4 shrink-0" />
          <span className="truncate">{formatTerm(course)}</span>
        </p>
      </div>
    </Link>
  );
}
