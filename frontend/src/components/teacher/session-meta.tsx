import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

import { StatusBadge } from "@/components/shared/status-badge";
import { SESSION_STATUS } from "@/lib/constants/status";
import type { CourseSession } from "@/lib/types/course";

/** Tiêu đề "Buổi N: ..." + badge trạng thái — dùng chung cho cả 3 kiểu thẻ buổi học. */
export function SessionTitle({ session }: { session: CourseSession }) {
  const status = SESSION_STATUS[session.status];
  return (
    <div className="flex flex-wrap items-center gap-3">
      <h3 className="text-xl font-semibold">Buổi {session.order}: {session.title}</h3>
      <StatusBadge label={status.label} tone={status.tone} dot />
    </div>
  );
}

/** Ô nhỏ hiển thị "Mở: 12/09 · 07:00" */
export function DateChip({ icon: Icon, label, children }: { icon: LucideIcon; label: string; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-md border bg-card px-3 py-1.5 text-sm text-muted-foreground shadow-sm">
      <Icon className="size-4 text-indigo-600" />
      {label}: <strong className="font-semibold text-foreground">{children}</strong>
    </span>
  );
}
