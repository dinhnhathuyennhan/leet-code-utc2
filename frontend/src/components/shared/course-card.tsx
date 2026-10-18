import Link from "next/link";
import { CalendarDays, Code2, Users } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/helpers/format";
import type { CourseSummary } from "@/lib/types/course";
import { cn } from "@/lib/utils";

interface CourseCardProps {
  course: CourseSummary;
  href: string;
  /** Ngôn ngữ chính của lớp — mặc định "Java" theo Figma. */
  language?: string;
  /** Tên giảng viên — fallback "Giảng viên UTC2". */
  teacherName?: string;
  /** Số bài hoàn thành / tổng. Để undefined nếu BE chưa trả. */
  progress?: { done: number; total: number };
}

/**
 * Thẻ lớp học phần — phiên bản "Modern Minimal + Developer Tool" theo Figma.
 *
 * Cấu trúc:
 *  - Banner ngôn ngữ (gradient + icon) phía trên
 *  - Mã lớp (badge) + tên lớp
 *  - Giảng viên, sĩ số, ngày bắt đầu
 *  - Thanh tiến độ + nhãn "X bài / Y bài"
 */
export function CourseCard({ course, href, language = "Java", teacherName, progress }: CourseCardProps) {
  const teacher = teacherName?.trim() || course.created_by || "Giảng viên UTC2";
  const p = progress ?? { done: 0, total: 0 };
  const pct = p.total > 0 ? Math.min(100, Math.round((p.done / p.total) * 100)) : 0;

  return (
    <Link
      href={href}
      className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-sm outline-none transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md focus-visible:ring-2 focus-visible:ring-[#352078]"
    >
      {/* Language banner — gradient tím thương hiệu */}
      <div className="relative flex h-24 items-center justify-between bg-gradient-to-br from-[#352078] via-[#4a2a9a] to-[#6a3fb5] px-5 text-white">
        <div className="flex flex-col">
          <span className="text-[10px] font-medium uppercase tracking-widest text-white/70">
            Ngôn ngữ
          </span>
          <span className="text-2xl font-bold tracking-tight">{language}</span>
        </div>
        <div className="flex size-12 items-center justify-center rounded-xl bg-white/15 backdrop-blur-sm">
          <Code2 className="size-6" />
        </div>
        {/* Decorative shape */}
        <div
          aria-hidden
          className="absolute -right-6 -top-6 size-20 rounded-full bg-white/8"
        />
        <div
          aria-hidden
          className="absolute -bottom-8 -left-4 size-16 rounded-full bg-white/5"
        />
      </div>

      {/* Body */}
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="space-y-1.5">
          <Badge
            variant="outline"
            className="border-[#352078]/25 bg-[#352078]/8 font-mono text-[10px] text-[#352078]"
          >
            {course.code}
          </Badge>
          <h3 className="line-clamp-2 text-base font-semibold leading-snug text-foreground">
            {course.name}
          </h3>
          <p className="line-clamp-1 text-xs text-muted-foreground">
            GV: <span className="font-medium text-foreground/80">{teacher}</span>
          </p>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
          <p className="flex items-center gap-1.5">
            <CalendarDays className="size-3.5 shrink-0" />
            <span className="truncate">{formatDate(course.start_date)}</span>
          </p>
          <p className="flex items-center gap-1.5">
            <Users className="size-3.5 shrink-0" />
            <span className="truncate">{course.total_number_student} SV</span>
          </p>
        </div>

        {/* Progress */}
        <div className="mt-auto space-y-1.5 border-t border-border/60 pt-3">
          <div className="flex items-center justify-between text-[11px]">
            <span className="font-medium text-muted-foreground">Tiến độ</span>
            <span className="font-semibold text-foreground">
              {p.done}/{p.total} bài
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={cn(
                "h-full rounded-full bg-gradient-to-r from-[#352078] to-[#5b3aa8] transition-all",
              )}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      </div>
    </Link>
  );
}
