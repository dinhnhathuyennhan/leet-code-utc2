import Link from "next/link";
import { Clock, Eye, Flag, Pencil, Plus } from "lucide-react";

import { ActionMenu } from "@/components/teacher/action-menu";
import { Button } from "@/components/ui/button";
import { formatDeadline } from "@/lib/helpers/format";
import type { CourseSession } from "@/lib/types/course";
import { cn } from "@/lib/utils";
import { DateChip, SESSION_MENU, SessionTitle } from "./session-meta";

const PRIMARY_BTN = "bg-[#2f226b] text-white hover:bg-[#251b56]";

/** Buổi đang mở: Khung xanh nhạt, nút Vào xem chi tiết chuyển hướng sang trang buổi học */
export function OpenSessionCard({
  session,
  courseId,
  selected = false,
  onSelect,
}: {
  session: CourseSession;
  courseId: string | number;
  selected?: boolean;
  onSelect?: () => void;
}) {
  return (
    <section onClick={onSelect} className={cn("flex cursor-pointer flex-wrap items-center justify-between gap-4 rounded-xl border p-5 shadow-sm transition-colors hover:bg-indigo-50/70 dark:border-indigo-500/20 dark:hover:bg-indigo-500/10", selected ? "border-indigo-200 bg-indigo-50/60 dark:bg-indigo-500/10" : "border-slate-200 bg-card")}>
      <div className="space-y-3">
        <SessionTitle session={session} />
        <div className="flex flex-wrap gap-3">
          {session.opens_at && (
            <DateChip icon={Clock} label="Mở">
              {formatDeadline(session.opens_at)}
            </DateChip>
          )}
          <DateChip icon={Flag} label="Hạn nộp">
            {formatDeadline(session.deadline)}
          </DateChip>
          {session.participant_count !== null && (
            <div className="flex items-center gap-1.5 rounded-md bg-card px-2.5 py-1 text-xs font-medium text-slate-700 shadow-xs dark:bg-slate-800 dark:text-slate-300">
              <span className="text-muted-foreground">Sĩ số nộp bài:</span>
              <span className="font-semibold">{session.participant_count}/45</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          {session.problems.length > 0 ? `${session.problems.length} bài tập` : "3 bài tập"}
        </span>
        <Button asChild variant="outline" size="sm" className="h-9 gap-1.5 border-slate-300"><Link href={`/teacher/courses/${courseId}/sessions/${session.id}?mode=edit`} onClick={(event) => event.stopPropagation()}><Pencil className="size-4" /> Sửa buổi học</Link></Button>
        <Button asChild size="sm" className={`h-9 gap-1.5 ${PRIMARY_BTN}`}>
          <Link href={`/teacher/courses/${courseId}/sessions/${session.id}`}>
            <Plus className="size-4" /> Vào xem chi tiết
          </Link>
        </Button>
        <Button variant="outline" size="icon" className="size-9 border-slate-300" aria-label="Xem trước">
          <Eye className="size-4" />
        </Button>
      </div>
    </section>
  );
}

/** Buổi sắp mở: thẻ gọn với nút Mở sớm / Sửa buổi học. */
export function UpcomingSessionCard({ session, courseId, selected = false, onSelect }: { session: CourseSession; courseId: string | number; selected?: boolean; onSelect?: () => void }) {
  return (
    <section onClick={onSelect} className={cn("flex cursor-pointer flex-wrap items-center justify-between gap-4 rounded-xl border p-5 shadow-sm transition-colors hover:bg-indigo-50/70", selected ? "border-indigo-200 bg-indigo-50/60" : "border-slate-200 bg-card")}>
      <div className="space-y-2">
        <SessionTitle session={session} />
        <p className="text-sm text-muted-foreground">
          Đã kết thúc: <strong className="font-medium text-foreground">{formatDeadline(session.deadline)}</strong>
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button size="sm" className="h-9 bg-amber-500 font-medium text-white hover:bg-amber-600">
          Mở sớm
        </Button>
        <Button asChild size="sm" className={`h-9 gap-1.5 ${PRIMARY_BTN}`}><Link href={`/teacher/courses/${courseId}/sessions/${session.id}?mode=edit`} onClick={(event) => event.stopPropagation()}><Plus className="size-4" /> Sửa buổi học</Link></Button>
        <ActionMenu label="Thao tác buổi học" items={SESSION_MENU} className="size-9" />
      </div>
    </section>
  );
}

/** Buổi đã đóng: hiển thị tóm tắt tham gia + lối vào bảng điểm. */
export function ClosedSessionCard({
  session,
  courseId,
  studentCount,
  onViewResults,
  selected = false,
  onSelect,
}: {
  session: CourseSession;
  courseId: string | number;
  studentCount: number;
  onViewResults: () => void;
  selected?: boolean;
  onSelect?: () => void;
}) {
  return (
    <section onClick={onSelect} className={cn("flex cursor-pointer flex-wrap items-center justify-between gap-4 rounded-xl border p-5 shadow-sm transition-colors hover:bg-indigo-50/70", selected ? "border-indigo-200 bg-indigo-50/60" : "border-slate-200 bg-card")}>
      <div className="space-y-2">
        <SessionTitle session={session} />
        <p className="text-sm text-muted-foreground">
          Đã kết thúc:{" "}
          <strong className="font-medium text-foreground">{formatDeadline(session.deadline)}</strong>
          {session.participant_count !== null && (
            <span className="font-medium text-emerald-700 dark:text-emerald-400">
              {" "}— {session.participant_count}/{studentCount} sinh viên tham gia
            </span>
          )}
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={onViewResults} size="sm" className="h-9 gap-1.5 bg-blue-100 text-slate-800 hover:bg-blue-200">
          <Plus className="size-4" /> Xem kết quả & Bảng điểm
        </Button>
        <Button asChild size="sm" className={`h-9 gap-1.5 ${PRIMARY_BTN}`}>
          <Link href={`/teacher/courses/${courseId}/sessions/${session.id}`} onClick={(event) => event.stopPropagation()}>
            <Plus className="size-4" /> Vào xem chi tiết
          </Link>
        </Button>
        <Button variant="outline" size="icon" className="size-9 border-slate-300" aria-label="Xem trước"><Eye className="size-4" /></Button>
      </div>
    </section>
  );
}
