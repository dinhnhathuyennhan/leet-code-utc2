import Link from "next/link";
import { Clock, Flag, Pencil, Plus } from "lucide-react";
import { ActionMenu } from "@/components/teacher/action-menu";
import { Button } from "@/components/ui/button";
import { formatDeadline } from "@/lib/helpers/format";
import type { CourseSession } from "@/lib/types/course";
import { cn } from "@/lib/utils";
import { DateChip, SESSION_MENU, SessionTitle } from "./session-meta";

const PRIMARY_BTN = "bg-[#2f226b] text-white hover:bg-[#251b56]";
type SessionCardProps = { session: CourseSession; courseId: string | number; selected?: boolean; onSelect?: () => void };

export function OpenSessionCard({ session, courseId, studentCount, selected = false, onSelect }: SessionCardProps & { studentCount: number }) {
  return <section onClick={onSelect} className={cn("flex cursor-pointer flex-wrap items-center justify-between gap-4 rounded-xl border p-5 shadow-sm transition-colors hover:bg-indigo-50/70 dark:border-indigo-500/20 dark:hover:bg-indigo-500/10", selected ? "border-indigo-200 bg-indigo-50/60 dark:bg-indigo-500/10" : "border-slate-200 bg-card")}>
    <div className="space-y-3"><SessionTitle session={session} /><div className="flex flex-wrap gap-3">{session.opens_at && <DateChip icon={Clock} label="Mở">{formatDeadline(session.opens_at)}</DateChip>}<DateChip icon={Flag} label="Hạn nộp">{formatDeadline(session.deadline)}</DateChip>{session.participant_count !== null && <div className="flex items-center gap-1.5 rounded-md bg-card px-2.5 py-1 text-xs font-medium text-slate-700 shadow-xs dark:bg-slate-800 dark:text-slate-300"><span className="text-muted-foreground">Sĩ số nộp bài:</span><span className="font-semibold">{session.participant_count}/{studentCount}</span></div>}</div></div>
    <div className="flex flex-wrap items-center gap-3"><span className="text-sm font-semibold text-slate-700 dark:text-slate-300">{session.problems.length} bài tập</span><Button asChild variant="outline" size="sm" className="h-9 gap-1.5 border-slate-300"><Link href={`/teacher/courses/${courseId}/sessions/${session.id}?mode=edit`} onClick={(event) => event.stopPropagation()}><Pencil className="size-4" /> Sửa buổi học</Link></Button></div>
  </section>;
}

export function UpcomingSessionCard({ session, courseId, selected = false, onSelect }: SessionCardProps) {
  return <section onClick={onSelect} className={cn("flex cursor-pointer flex-wrap items-center justify-between gap-4 rounded-xl border p-5 shadow-sm transition-colors hover:bg-indigo-50/70", selected ? "border-indigo-200 bg-indigo-50/60" : "border-slate-200 bg-card")}>
    <div className="space-y-2"><SessionTitle session={session} /><p className="text-sm text-muted-foreground">Sắp mở: <strong className="font-medium text-foreground">{formatDeadline(session.opens_at ?? session.deadline)}</strong></p></div>
    <div className="flex flex-wrap items-center gap-3"><span className="text-sm font-semibold text-slate-700 dark:text-slate-300">{session.problems.length} bài tập</span><Button size="sm" className="h-9 bg-amber-500 font-medium text-white hover:bg-amber-600">Mở sớm</Button><Button asChild size="sm" className={`h-9 gap-1.5 ${PRIMARY_BTN}`}><Link href={`/teacher/courses/${courseId}/sessions/${session.id}?mode=edit`} onClick={(event) => event.stopPropagation()}><Plus className="size-4" /> Sửa buổi học</Link></Button><ActionMenu label="Thao tác buổi học" items={SESSION_MENU} className="size-9" /></div>
  </section>;
}

export function ClosedSessionCard({ session, studentCount, selected = false, onSelect }: SessionCardProps & { studentCount: number }) {
  return <section onClick={onSelect} className={cn("flex cursor-pointer flex-wrap items-center justify-between gap-4 rounded-xl border p-5 shadow-sm transition-colors hover:bg-indigo-50/70", selected ? "border-indigo-200 bg-indigo-50/60" : "border-slate-200 bg-card")}>
    <div className="space-y-2"><SessionTitle session={session} /><p className="text-sm text-muted-foreground">Đã kết thúc: <strong className="font-medium text-foreground">{formatDeadline(session.deadline)}</strong>{session.participant_count !== null && <span className="font-medium text-emerald-700 dark:text-emerald-400"> — {session.participant_count}/{studentCount} sinh viên tham gia</span>}</p></div>
    <div className="flex flex-wrap items-center gap-3"><span className="text-sm font-semibold text-slate-700 dark:text-slate-300">{session.problems.length} bài tập</span></div>
  </section>;
}
