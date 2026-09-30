import type { LucideIcon } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export interface StatItem {
  icon: LucideIcon;
  value: string;
  label: string;
  /** Nền vàng — dùng cho số liệu cần chú ý (hạn nộp). */
  highlight?: boolean;
}

export function CourseStatsBar({ items }: { items: StatItem[] }) {
  return (
    <div className="flex flex-wrap gap-2 rounded-2xl bg-indigo-50/70 p-1.5 dark:bg-slate-800/50">
      {items.map(({ icon: Icon, value, label, highlight }) => (
        <div
          key={label}
          className={cn(
            "flex min-w-40 flex-1 items-center gap-3 rounded-xl px-4 py-3 sm:flex-none sm:pr-8",
            highlight ? "bg-amber-100 dark:bg-amber-500/20" : "bg-card",
          )}
        >
          <span
            className={cn(
              "flex size-10 shrink-0 items-center justify-center rounded-lg",
              highlight ? "bg-amber-400 text-amber-950" : "bg-indigo-100 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300",
            )}
          >
            <Icon className="size-5" />
          </span>
          <div className="leading-tight">
            <p className="text-xl font-bold">{value}</p>
            <p className="text-sm text-muted-foreground">{label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export function CourseStatsBarSkeleton() {
  return (
    <div className="flex flex-wrap gap-2 rounded-2xl bg-indigo-50/70 p-1.5 dark:bg-slate-800/50">
      {[0, 1, 2].map((i) => (
        <Skeleton key={i} className="h-[4.5rem] w-full rounded-xl sm:w-52" />
      ))}
    </div>
  );
}
