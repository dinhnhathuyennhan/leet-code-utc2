import type { ReactNode } from "react";
import { CalendarCheck, Pencil, Plus, UserCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/helpers/format";
import { formatUpdatedAt } from "@/lib/helpers/datetime";
import type { CourseDetail } from "@/lib/types/course";

function MetaItem({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <div className="flex items-center gap-2 text-muted-foreground [&_strong]:font-semibold [&_strong]:text-foreground">
      {icon}
      <span>{children}</span>
    </div>
  );
}

interface CourseHeaderCardProps {
  course: CourseDetail;
  onCreateSession?: () => void;
  onEditCourse?: () => void;
}

export function CourseHeaderCard({ course, onCreateSession, onEditCourse }: CourseHeaderCardProps) {
  return (
    <section className="relative flex flex-wrap items-start justify-between gap-6 overflow-hidden rounded-2xl border bg-card p-6 pl-8 shadow-sm">
      <span aria-hidden className="absolute inset-y-6 left-0 w-1.5 rounded-r-full bg-[#2f226b]" />

      <div className="min-w-0 space-y-4">
        <h1 className="max-w-full truncate text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-3xl" title={`${course.name} — ${course.code}`}>
          {course.name} — {course.code}
        </h1>
        <div>
          <span className="inline-block rounded-md bg-[#3b2a82] px-3.5 py-1 text-sm font-medium text-white shadow-sm">
            Học kỳ {course.semester} ({course.academic_year.replace("-", " - ")})
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-x-8 gap-y-2 text-[15px]">
          <MetaItem icon={<CalendarCheck className="size-4 text-slate-500" />}>
            Ngày bắt đầu: <strong>{formatDate(course.start_date)}</strong>
          </MetaItem>
          <MetaItem icon={<CalendarCheck className="size-4 text-slate-500" />}>
            Ngày kết thúc: <strong>{formatDate(course.end_date)}</strong>
          </MetaItem>
          <MetaItem icon={<UserCheck className="size-4 text-slate-500" />}>
            Sĩ số: <strong>{course.student_count} sinh viên</strong>
          </MetaItem>
          {course.updated_at && formatUpdatedAt(course.updated_at) && <MetaItem icon={<CalendarCheck className="size-4 text-slate-500" />}>
            Cập nhật lúc: <strong>{formatUpdatedAt(course.updated_at)}</strong>
          </MetaItem>}
        </div>
      </div>

      <div className="flex w-full flex-col gap-3 sm:w-auto sm:shrink-0">
        <Button
          onClick={onCreateSession}
          className="h-11 bg-[#2f226b] px-6 text-[15px] font-semibold text-white shadow-sm hover:bg-[#251b56]"
        >
          <Plus className="size-5" /> Tạo buổi học
        </Button>
        <Button
          onClick={onEditCourse}
          variant="outline"
          className="h-11 border-[#2f226b] px-6 text-[15px] font-semibold text-[#2f226b] hover:bg-indigo-50 dark:border-indigo-400 dark:text-indigo-300 dark:hover:bg-slate-800"
        >
          <Pencil className="size-4" /> Chỉnh sửa lớp
        </Button>
      </div>
    </section>
  );
}
