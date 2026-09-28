import { CircleAlert, CircleCheck, Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { formatDeadline } from "@/lib/helpers/format";
import type { CourseSession } from "@/lib/types/course";

/** Banner vàng tóm tắt tiến độ của buổi đang mở. */
export function SessionAlertBanner({ session, studentCount }: { session: CourseSession; studentCount: number }) {
  const progress = session.progress;
  if (!progress) return null;

  return (
    <div className="flex flex-wrap items-start justify-between gap-4 rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm dark:border-amber-500/30 dark:bg-amber-500/10">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">
          Buổi {session.order} đang diễn ra và {progress.students_submitted}/{studentCount} sinh viên đã nộp ít nhất 1 bài
        </h3>
        <p className="flex items-center gap-2 text-sm font-medium text-emerald-700 dark:text-emerald-400">
          <CircleCheck className="size-4" /> Đã hoàn thành: {progress.completed_count} bài
        </p>
        {progress.compile_error_count > 0 && (
          <p className="flex items-center gap-2 text-sm font-medium text-amber-700 dark:text-amber-400">
            <CircleAlert className="size-4" /> Cần hỗ trợ: {progress.compile_error_count} bài gặp lỗi biên dịch
          </p>
        )}
      </div>
      <div className="flex flex-col items-end gap-2">
        <Button className="bg-amber-400 font-semibold text-amber-950 hover:bg-amber-500">
          <Send className="size-4" /> Gửi nhắc nhở
        </Button>
        <p className="text-xs text-muted-foreground">Hạn chót: {formatDeadline(session.deadline)}</p>
      </div>
    </div>
  );
}
