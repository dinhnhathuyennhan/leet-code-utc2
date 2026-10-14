import Link from "next/link";
import { BookCheck, CalendarClock, GraduationCap, MessageSquare, Users } from "lucide-react";

import { cn } from "@/lib/utils";
import type { CourseSummary } from "@/lib/types/course";

/**
 * Card lớp học phần — phiên bản "Language Hero" theo Figma (rút gọn).
 *
 * Theo ảnh 3 (Figma):
 *  - Banner ngôn ngữ gradient đậm (không có logo chữ ở góc).
 *  - Body: badge trạng thái + mã lớp + tên lớp.
 *  - Footer: tên giảng viên bên trái + 2 icon (chat, members) bên phải.
 *  - Toàn bộ card là 1 link — click anywhere để vào lớp.
 */

export type LanguageKey =
  | "java"
  | "python"
  | "javascript"
  | "c"
  | "cpp"
  | "go"
  | "default";

export const LANGUAGE_THEMES: Record<LanguageKey, {
  label: string;
  /** Tailwind classes cho gradient. */
  gradient: string;
  /** Tên hiển thị trên banner. */
  display: string;
}> = {
  java: {
    label: "Java",
    gradient: "from-[#1e3a8a] via-[#3b3f8a] to-[#7e3a8a]",
    display: "Java",
  },
  python: {
    label: "Python",
    gradient: "from-[#1e3a8a] via-[#1d4ed8] to-[#3b82f6]",
    display: "Python",
  },
  javascript: {
    label: "JavaScript",
    gradient: "from-[#b45309] via-[#d97706] to-[#fbbf24]",
    display: "JavaScript",
  },
  c: {
    label: "C",
    gradient: "from-[#0f172a] via-[#1e293b] to-[#334155]",
    display: "C",
  },
  cpp: {
    label: "C++",
    gradient: "from-[#0c4a6e] via-[#0369a1] to-[#0284c7]",
    display: "C++",
  },
  go: {
    label: "Go",
    gradient: "from-[#0f766e] via-[#0d9488] to-[#14b8a6]",
    display: "Go",
  },
  default: {
    label: "Default",
    gradient: "from-[#352078] via-[#5b3aa8] to-[#7c3aed]",
    display: "Course",
  },
};

/** Map từ label ngôn ngữ (mock) sang theme. */
export function resolveLanguage(input?: string): LanguageKey {
  if (!input) return "default";
  const k = input.toLowerCase().trim();
  if (k.includes("java") && !k.includes("script")) return "java";
  if (k.includes("python")) return "python";
  if (k.includes("javascript") || k.includes("js")) return "javascript";
  if (k.includes("c++") || k.includes("cpp")) return "cpp";
  if (k.includes("c")) return "c";
  if (k.includes("go")) return "go";
  return "default";
}

export interface DashboardCourseCardProps {
  course: CourseSummary;
  /** Ngôn ngữ (input có thể là "Java", "Python", …). */
  language: string;
  /** Tên giảng viên. */
  teacherName?: string;
  /** Trạng thái: "ongoing" | "upcoming" | "closed". */
  status?: "ongoing" | "upcoming" | "closed";
  /** Số tin nhắn / thành viên (mock — thay bằng API thật). */
  messageCount?: number;
  memberCount?: number;
  href: string;
}

const STATUS_LABEL: Record<NonNullable<DashboardCourseCardProps["status"]>, string> = {
  ongoing: "Đang diễn ra",
  upcoming: "Sắp khai giảng",
  closed: "Đã kết thúc",
};

const STATUS_STYLES: Record<NonNullable<DashboardCourseCardProps["status"]>, string> = {
  ongoing: "bg-[#352078]/8 text-[#352078] border-[#352078]/20",
  upcoming: "bg-sky-50 text-sky-700 border-sky-200",
  closed: "bg-slate-100 text-slate-600 border-slate-200",
};

export function DashboardCourseCard({
  course,
  language,
  teacherName,
  status = "ongoing",
  messageCount = 0,
  memberCount = 0,
  href,
}: DashboardCourseCardProps) {
  const theme = LANGUAGE_THEMES[resolveLanguage(language)];
  const teacher = teacherName?.trim() || course.created_by || "Giảng viên UTC2";

  return (
    <Link
      href={href}
      className={cn(
        "group flex h-full flex-col overflow-hidden rounded-2xl bg-card shadow-sm",
        "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md",
        "outline-none focus-visible:ring-2 focus-visible:ring-[#352078]",
      )}
    >
      {/* Language hero banner — không có logo ở góc */}
      <div
        className={cn(
          "relative flex h-32 items-center justify-center bg-gradient-to-br",
          theme.gradient,
        )}
      >
        <div
          aria-hidden
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle, rgba(255,255,255,0.4) 1px, transparent 1px)",
            backgroundSize: "16px 16px",
          }}
        />
        <span className="relative text-3xl font-extrabold tracking-tight text-white drop-shadow-sm">
          {theme.display}
        </span>
      </div>

      {/* Body */}
      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="space-y-1.5">
          <span
            className={cn(
              "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold",
              STATUS_STYLES[status],
            )}
          >
            {STATUS_LABEL[status]}
          </span>
          <p className="font-mono text-[10px] text-muted-foreground">{course.code}</p>
          <h3 className="line-clamp-2 text-base font-semibold leading-snug text-foreground">
            {course.name}
          </h3>
        </div>
      </div>

      {/* Footer: tên GV bên trái + 2 icon bên phải */}
      <div className="flex items-center justify-between border-t border-border/60 px-4 py-2.5 text-xs">
        <span className="truncate text-muted-foreground">
          GV: <span className="font-medium text-foreground/80">{teacher}</span>
        </span>
        <div className="flex shrink-0 items-center gap-3 text-muted-foreground">
          <span
            className="inline-flex items-center gap-1"
            aria-label={`${messageCount} tin nhắn`}
          >
            <MessageSquare className="size-3.5" />
            {messageCount}
          </span>
          <span
            className="inline-flex items-center gap-1"
            aria-label={`${memberCount} thành viên`}
          >
            <Users className="size-3.5" />
            {memberCount}
          </span>
        </div>
      </div>
    </Link>
  );
}

/** Mini stat card (icon + label + value) cho hàng stats phía trên dashboard. */
export function MiniStat({
  icon: Icon,
  label,
  value,
  tone = "indigo",
}: {
  icon: typeof BookCheck;
  label: string;
  value: string | number;
  tone?: "indigo" | "emerald" | "amber";
}) {
  const toneClasses = {
    indigo: "bg-indigo-50 text-indigo-600",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
  }[tone];
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-border bg-card p-4 shadow-sm">
      <span
        className={cn(
          "flex size-11 shrink-0 items-center justify-center rounded-xl",
          toneClasses,
        )}
      >
        <Icon className="size-5" />
      </span>
      <div className="min-w-0">
        <p className="truncate text-xs font-medium text-muted-foreground">{label}</p>
        <p className="text-xl font-bold leading-tight text-foreground">{value}</p>
      </div>
    </div>
  );
}

export { CalendarClock, GraduationCap };
