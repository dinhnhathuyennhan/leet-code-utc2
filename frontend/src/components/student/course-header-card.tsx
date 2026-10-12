import type { ReactNode } from "react";
import { CalendarCheck, CalendarPlus, UserCheck, Users } from "lucide-react";

import { formatDate } from "@/lib/helpers/format";
import type { CourseDetail } from "@/lib/types/course";

function MetaItem({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <div className="flex items-center gap-2 text-muted-foreground [&_strong]:font-semibold [&_strong]:text-foreground">
      {icon}
      <span>{children}</span>
    </div>
  );
}

/** Header lớp cho sinh viên — chỉ hiển thị, không có nút chỉnh sửa/tạo. */
export function StudentCourseHeaderCard({ course }: { course: CourseDetail }) {
  return (
    <section className="relative flex flex-wrap items-start justify-between gap-6 overflow-hidden rounded-2xl border bg-card p-6 pl-8 shadow-sm">
      <span aria-hidden className="absolute inset-y-6 left-0 w-1.5 rounded-r-full bg-indigo-600" />

      <div className="space-y-4">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {course.name} — {course.code}
        </h1>
        <span className="inline-block rounded-md bg-indigo-700 px-3 py-1 text-sm font-medium text-white">
          {course.term}
        </span>
        <div className="grid gap-x-14 gap-y-2.5 text-[15px] sm:grid-cols-2">
          <MetaItem icon={<CalendarCheck className="size-4" />}>Bắt đầu: <strong>{formatDate(course.start_date)}</strong></MetaItem>
          <MetaItem icon={<CalendarCheck className="size-4" />}>Kết thúc: <strong>{formatDate(course.end_date)}</strong></MetaItem>
          <MetaItem icon={<UserCheck className="size-4" />}>Sĩ số: <strong>{course.total_number_student} sinh viên</strong></MetaItem>
          <MetaItem icon={<Users className="size-4" />}>Giảng viên: <strong>{course.created_by}</strong></MetaItem>
        </div>
      </div>

      <div className="flex w-full items-center gap-2 self-end text-sm text-muted-foreground sm:w-auto sm:flex-col sm:items-end sm:text-right">
        <CalendarPlus className="size-5 shrink-0 text-indigo-600 sm:order-2" />
        <p className="sm:order-1">Buổi học & bài tập sẽ đến ở Phase 2.</p>
      </div>
    </section>
  );
}