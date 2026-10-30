import Link from "next/link";
import { Bell, Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { SessionDetailData } from "@/lib/types/course";
import type { SessionStatus } from "@/lib/helpers/session-status";

type Props = {
  alert: SessionDetailData["alert"];
  status: SessionStatus;
  listHref: string;
};

export function SessionDeadlineAlert({ alert, status, listHref }: Props) {
  if (!alert || alert.missing_students <= 0 || status === "upcoming") return null;
  const open = status === "open";

  return (
    <section
      className={`flex flex-wrap items-center justify-between gap-4 rounded-2xl border p-5 shadow-xs ${
        open ? "border-amber-200 bg-[#fefce8] dark:border-amber-500/30 dark:bg-amber-500/10" : "bg-card"
      }`}
    >
      <div className="flex items-center gap-4">
        <div className={`flex size-12 shrink-0 items-center justify-center rounded-xl text-white shadow-sm ${open ? "bg-red-600" : "bg-slate-500"}`}>
          <Bell className="size-6" />
        </div>
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
            {open ? "Cảnh báo hạn chót nộp bài" : "Buổi học đã đóng"}
          </h3>
          <p className="text-sm text-slate-700 dark:text-slate-300">
            <strong>{alert.missing_students} sinh viên</strong>{" "}
            {open
              ? `chưa nộp bài ${alert.problem_name ?? ""}. Hạn chót đóng hệ thống tự động vào ${alert.deadline_text ?? ""}.`
              : "không nộp bài trong thời hạn."}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button asChild variant="outline" className="h-10 bg-white font-semibold dark:bg-slate-800">
          <Link href={listHref}>Xem danh sách {alert.missing_students} SV</Link>
        </Button>
        {open && (
          // TODO: backend chưa có API gửi nhắc nhở. Khi có, bỏ `disabled` và gọi API tại onClick.
          <span title="Chưa khả dụng: hệ thống chưa hỗ trợ gửi nhắc nhở">
            <Button disabled className="pointer-events-none h-10 bg-[#facc15] font-semibold text-amber-950">
              <Send className="size-4" /> Gửi nhắc nhở
            </Button>
          </span>
        )}
      </div>
    </section>
  );
}