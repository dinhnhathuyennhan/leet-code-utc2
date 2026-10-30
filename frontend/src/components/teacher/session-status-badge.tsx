import type { SessionStatus } from "@/lib/helpers/session-status";

const MAP: Record<SessionStatus, { label: string; cls: string }> = {
  upcoming: { label: "Sắp mở", cls: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300" },
  open: { label: "Đang mở", cls: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300" },
  closed: { label: "Đã đóng", cls: "bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300" },
};

export function SessionStatusBadge({ status }: { status: SessionStatus }) {
  const { label, cls } = MAP[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${cls}`}>
      <span className="size-1.5 rounded-full bg-current" /> {label}
    </span>
  );
}