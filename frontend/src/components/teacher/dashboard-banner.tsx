import { Skeleton } from "@/components/ui/skeleton";
import type { TeacherOverview } from "@/lib/dashboard";
import { cn } from "@/lib/utils";

// clip-path là phần đặc thù (hình mũi tên) nên viết bằng style — Tailwind không có utility tương đương.
const ARROW_FIRST = "polygon(0 0, calc(100% - 24px) 0, 100% 50%, calc(100% - 24px) 100%, 0 100%)";
const ARROW_NEXT = "polygon(0 0, calc(100% - 24px) 0, 100% 50%, calc(100% - 24px) 100%, 0 100%, 24px 50%)";

interface DashboardBannerProps {
  overview: Pick<TeacherOverview, "teacher_name" | "term_label" | "stats">;
}

export function DashboardBanner({ overview }: DashboardBannerProps) {
  const { teacher_name, term_label, stats } = overview;
  const items = [
    { label: "Lớp đang dạy", value: stats.active_courses },
    { label: "Bài cần chấm", value: stats.pending_grading },
    { label: "Đạo văn", value: stats.plagiarism_cases },
  ];

  return (
    <section className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-700 via-indigo-500 to-sky-400 p-6 text-white sm:p-8 lg:px-12 lg:py-10">
      <div aria-hidden className="pointer-events-none absolute inset-y-0 left-[34%] w-28 -skew-x-[28deg] bg-white/10" />
      <div aria-hidden className="pointer-events-none absolute inset-y-0 left-[46%] w-14 -skew-x-[28deg] bg-white/10" />

      <div className="relative flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-1.5">
          <p className="text-xl font-medium sm:text-2xl">Chào mừng trở lại</p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{teacher_name}!</h1>
          <p className="pt-2 text-lg text-white/90">{term_label}</p>
        </div>

        <ul className="flex max-w-full items-stretch overflow-x-auto pr-4">
          {items.map((item, index) => (
            <li
              key={item.label}
              style={{ clipPath: index === 0 ? ARROW_FIRST : ARROW_NEXT }}
              className={cn(
                "flex min-w-36 flex-col items-center justify-center bg-white px-9 py-4 text-slate-500",
                index > 0 && "-ml-3",
              )}
            >
              <span className="text-sm">{item.label}</span>
              <span className="text-5xl font-bold leading-tight text-indigo-600">{item.value}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function DashboardBannerSkeleton() {
  return <Skeleton className="h-52 w-full rounded-2xl" />;
}
