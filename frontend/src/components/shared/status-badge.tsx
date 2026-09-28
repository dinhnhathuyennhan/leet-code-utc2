import { Badge } from "@/components/ui/badge";
import type { BadgeTone } from "@/lib/constants/status";
import { cn } from "@/lib/utils";

const TONES: Record<BadgeTone, string> = {
  indigo: "bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300",
  amber: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300",
  green: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300",
  blue: "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300",
  slate: "bg-slate-100 text-slate-600 dark:bg-slate-500/20 dark:text-slate-300",
};

interface StatusBadgeProps {
  label: string;
  tone: BadgeTone;
  /** Chấm tròn phía trước (dùng cho trạng thái buổi học). */
  dot?: boolean;
  className?: string;
}

export function StatusBadge({ label, tone, dot = false, className }: StatusBadgeProps) {
  return (
    <Badge
      variant="secondary"
      className={cn("gap-1.5 rounded-md border-0 px-2.5 py-1 text-xs font-medium hover:bg-current/10", TONES[tone], className)}
    >
      {dot && <span aria-hidden className="size-1.5 rounded-full bg-current" />}
      {label}
    </Badge>
  );
}
