"use client";

import { AlertTriangle, Bug, CheckCircle2, Clock, Loader2, XCircle } from "lucide-react";

import { cn } from "@/lib/utils";
import { submissionStatusMeta } from "@/lib/helpers/submission-status";
import { useLocale } from "@/lib/i18n";
import type { StudentSubmissionStatus } from "@/lib/types/submission";

const ICONS = {
  check: CheckCircle2,
  x: XCircle,
  alert: AlertTriangle,
  clock: Clock,
  bug: Bug,
  loader: Loader2,
} as const;

/** Chip trạng thái bài nộp dùng chung cho bảng lịch sử và trang kết quả. */
export function SubmissionStatusBadge({
  status,
  className,
}: {
  status: StudentSubmissionStatus | string;
  className?: string;
}) {
  const meta = submissionStatusMeta(status);
  const { t } = useLocale();
  const Icon = ICONS[meta.icon];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-semibold",
        meta.className,
        className,
      )}
    >
      <Icon className={cn("size-3.5", meta.icon === "loader" && "animate-spin")} />
      {t(meta.labelKey)}
    </span>
  );
}
