import { Clock, Flag, Pencil, Plus, ClipboardList } from "lucide-react";

import { ActionMenu } from "@/components/teacher/action-menu";
import { Button } from "@/components/ui/button";
import { formatDeadline } from "@/lib/helpers/format";
import type { CourseSession } from "@/lib/types/course";
import { DateChip, SESSION_MENU, SessionTitle } from "./session-meta";
import { ProblemTable } from "./problem-table";

const PRIMARY = "bg-indigo-900 text-white hover:bg-indigo-800";

/** Buổi đang mở: khung xanh nhạt + bảng bài tập. */
export function OpenSessionCard({ session, studentCount }: { session: CourseSession; studentCount: number }) {
  return (
    <section className="overflow-hidden rounded-xl border border-indigo-100 bg-indigo-50/70 dark:border-indigo-500/20 dark:bg-indigo-500/10">
      <header className="flex flex-wrap items-start justify-between gap-4 p-5">
        <div className="space-y-3">
          <SessionTitle session={session} />
          <div className="flex flex-wrap gap-3">
            {session.opens_at && <DateChip icon={Clock} label="Mở">{formatDeadline(session.opens_at)}</DateChip>}
            <DateChip icon={Flag} label="Hạn nộp">{formatDeadline(session.deadline)}</DateChip>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm font-semibold">{session.problems.length} bài tập</span>
          <Button className={PRIMARY}><Plus className="size-4" /> Thêm bài tập</Button>
          <Button variant="ghost" size="icon" aria-label="Chỉnh sửa buổi học" className="size-9 bg-card"><Pencil className="size-4" /></Button>
          <ActionMenu label="Thao tác buổi học" items={SESSION_MENU} className="size-9 bg-card" />
        </div>
      </header>
      {session.problems.length > 0 && <ProblemTable problems={session.problems} studentCount={studentCount} />}
    </section>
  );
}

/** Buổi sắp mở: thẻ gọn với nút Mở sớm / Chỉnh sửa bài tập. */
export function UpcomingSessionCard({ session }: { session: CourseSession }) {
  return (
    <section className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card p-5 shadow-sm">
      <div className="space-y-3">
        <SessionTitle session={session} />
        <div className="flex flex-wrap gap-3">
          {session.opens_at && <DateChip icon={Clock} label="Mở">{formatDeadline(session.opens_at)}</DateChip>}
          <DateChip icon={Flag} label="Hạn nộp">{formatDeadline(session.deadline)}</DateChip>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button className="bg-amber-500 text-white hover:bg-amber-600">Mở sớm</Button>
        <Button className={PRIMARY}><Plus className="size-4" /> Chỉnh sửa bài tập</Button>
        <ActionMenu label="Thao tác buổi học" items={SESSION_MENU} />
      </div>
    </section>
  );
}

/** Buổi đã đóng: hiển thị tóm tắt tham gia + lối vào bảng điểm. */
export function ClosedSessionCard({
  session,
  studentCount,
  onViewResults,
}: {
  session: CourseSession;
  studentCount: number;
  onViewResults: () => void;
}) {
  return (
    <section className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card p-5 shadow-sm">
      <div className="space-y-2">
        <SessionTitle session={session} />
        <p className="text-sm text-muted-foreground">
          Đã kết thúc: <strong className="font-semibold text-foreground">{formatDeadline(session.deadline)}</strong>
          {session.participant_count !== null && (
            <span className="font-medium text-emerald-700 dark:text-emerald-400">
              {" "}— {session.participant_count}/{studentCount} sinh viên tham gia
            </span>
          )}
        </p>
      </div>
      <Button onClick={onViewResults} className={PRIMARY}>
        <ClipboardList className="size-4" /> Xem kết quả & Bảng điểm
      </Button>
    </section>
  );
}
