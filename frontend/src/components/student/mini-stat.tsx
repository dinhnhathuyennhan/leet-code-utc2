import type { BookCheck } from "lucide-react";

import { cn } from "@/lib/utils";

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
