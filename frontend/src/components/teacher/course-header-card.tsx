import type { ReactNode } from "react";
import { CalendarCheck, MapPin, Pencil, Plus, UserCheck, Users } from "lucide-react";

import { Button } from "@/components/ui/button";
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

interface CourseHeaderCardProps {
  course: CourseDetail;
  onCreateSession?: () => void;
  onEditCourse?: () => void;
}

export function CourseHeaderCard({ course, onCreateSession, onEditCourse }: CourseHeaderCardProps) {
  return (
    <section className="relative flex flex-wrap items-start justify-between gap-6 overflow-hidden rounded-2xl border bg-card p-6 pl-8 shadow-sm">
      <span aria-hidden className="absolute inset-y-6 left-0 w-1.5 rounded-r-full bg-indigo-600" />

      <div className="space-y-4">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {course.name} — {course.code}
        </h1>
        <span className="inline-block rounded-md bg-indigo-700 px-3 py-1 text-sm font-medium text-white">
          Học kỳ {course.semester} ({course.academic_year.replace("-", " - ")})
        </span>
        <div className="grid gap-x-14 gap-y-2.5 text-[15px] sm:grid-cols-2">
          <MetaItem icon={<MapPin className="size-4" />}>Phòng {course.room}</MetaItem>
          <MetaItem icon={<Users className="size-4" />}>Nhóm {String(course.group).padStart(2, "0")}</MetaItem>
          <MetaItem icon={<CalendarCheck className="size-4" />}>Ngày kết thúc: <strong>{formatDate(course.end_date)}</strong></MetaItem>
          <MetaItem icon={<UserCheck className="size-4" />}>Sĩ số: <strong>{course.student_count} sinh viên</strong></MetaItem>
        </div>
      </div>

      <div className="flex w-full flex-col gap-3 sm:w-auto">
        <Button onClick={onCreateSession} className="h-12 bg-indigo-600 px-6 text-base hover:bg-indigo-700">
          <Plus className="size-5" /> Tạo buổi học
        </Button>
        <Button onClick={onEditCourse} variant="outline" className="h-12 border-indigo-600 px-6 text-base text-indigo-700 hover:bg-indigo-50 dark:text-indigo-300">
          <Pencil className="size-4" /> Chỉnh sửa lớp
        </Button>
      </div>
    </section>
  );
}
