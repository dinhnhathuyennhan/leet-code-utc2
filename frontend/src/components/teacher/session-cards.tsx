"use client";

import { useState } from "react";
import Link from "next/link";
import { Clock, Flag, Loader2, Pencil, Plus } from "lucide-react";
import { toast } from "sonner";

import { SessionActions } from "@/components/teacher/session-actions";
import { Button } from "@/components/ui/button";
import { updateLesson } from "@/lib/api/endpoints/courses";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { toDateInput } from "@/lib/helpers/datetime";
import { formatDeadline } from "@/lib/helpers/format";
import type { CourseSession } from "@/lib/types/course";
import { cn } from "@/lib/utils";
import { DateChip, SessionTitle } from "./session-meta";

const PRIMARY_BTN = "bg-[#2f226b] text-white hover:bg-[#251b56]";
type SessionCardProps = { session: CourseSession; courseId: string | number; selected?: boolean; onSelect?: () => void };

export function OpenSessionCard({ session, courseId, studentCount, selected = false, onSelect }: SessionCardProps & { studentCount: number }) {
  return <section onClick={onSelect} className={cn("flex cursor-pointer flex-wrap items-center justify-between gap-4 rounded-xl border p-5 shadow-sm transition-colors hover:bg-indigo-50/70 dark:border-indigo-500/20 dark:hover:bg-indigo-500/10", selected ? "border-indigo-200 bg-indigo-50/60 dark:bg-indigo-500/10" : "border-slate-200 bg-card")}>
    <div className="space-y-3"><SessionTitle session={session} /><div className="flex flex-wrap gap-3">{session.opens_at && <DateChip icon={Clock} label="Mở">{formatDeadline(session.opens_at)}</DateChip>}<DateChip icon={Flag} label="Hạn nộp">{formatDeadline(session.deadline)}</DateChip>{session.participant_count !== null && <div className="flex items-center gap-1.5 rounded-md bg-card px-2.5 py-1 text-xs font-medium text-slate-700 shadow-xs dark:bg-slate-800 dark:text-slate-300"><span className="text-muted-foreground">Sĩ số nộp bài:</span><span className="font-semibold">{session.participant_count}/{studentCount}</span></div>}</div></div>
    <div className="flex flex-wrap items-center gap-3"><span className="text-sm font-semibold text-slate-700 dark:text-slate-300">{session.problems.length} bài tập</span><Button asChild variant="outline" size="sm" className="h-9 gap-1.5 border-slate-300"><Link href={`/teacher/courses/${courseId}/sessions/${session.id}?mode=edit`} onClick={(event) => event.stopPropagation()}><Pencil className="size-4" /> Sửa buổi học</Link></Button></div>
  </section>;
}

/** "Mở sớm": dời ngày mở của buổi học về hôm nay (giữ nguyên hạn nộp). */
function OpenEarlyButton({ session, courseId, onChanged }: { session: CourseSession; courseId: string | number; onChanged?: () => void }) {
  const [busy, setBusy] = useState(false);
  async function openNow() {
    setBusy(true);
    try {
      await updateLesson(String(courseId), session.id, {
        lesson_name: session.title,
        start_date: toDateInput(new Date()),
        end_date: toDateInput(session.deadline),
        problem_ids: [],
      });
      toast.success(`Đã mở buổi ${session.order}.`);
      onChanged?.();
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }
  return <Button size="sm" disabled={busy} onClick={(event) => { event.stopPropagation(); void openNow(); }} className="h-9 bg-amber-500 font-medium text-white hover:bg-amber-600">{busy && <Loader2 className="size-4 animate-spin" />}Mở sớm</Button>;
}

export function UpcomingSessionCard({ session, courseId, selected = false, onSelect, onChanged }: SessionCardProps & { onChanged?: () => void }) {
  return <section onClick={onSelect} className={cn("flex cursor-pointer flex-wrap items-center justify-between gap-4 rounded-xl border p-5 shadow-sm transition-colors hover:bg-indigo-50/70", selected ? "border-indigo-200 bg-indigo-50/60" : "border-slate-200 bg-card")}>
    <div className="space-y-2"><SessionTitle session={session} /><p className="text-sm text-muted-foreground">Sắp mở: <strong className="font-medium text-foreground">{formatDeadline(session.opens_at ?? session.deadline)}</strong></p></div>
    <div className="flex flex-wrap items-center gap-3"><span className="text-sm font-semibold text-slate-700 dark:text-slate-300">{session.problems.length} bài tập</span><OpenEarlyButton session={session} courseId={courseId} onChanged={onChanged} /><Button asChild size="sm" className={`h-9 gap-1.5 ${PRIMARY_BTN}`}><Link href={`/teacher/courses/${courseId}/sessions/${session.id}?mode=edit`} onClick={(event) => event.stopPropagation()}><Plus className="size-4" /> Sửa buổi học</Link></Button><div onClick={(event) => event.stopPropagation()}><SessionActions courseId={String(courseId)} sessionId={String(session.id)} exerciseCount={session.problems.length} onDone={onChanged} /></div></div>
  </section>;
}

export function ClosedSessionCard({ session, studentCount, selected = false, onSelect }: SessionCardProps & { studentCount: number }) {
  return <section onClick={onSelect} className={cn("flex cursor-pointer flex-wrap items-center justify-between gap-4 rounded-xl border p-5 shadow-sm transition-colors hover:bg-indigo-50/70", selected ? "border-indigo-200 bg-indigo-50/60" : "border-slate-200 bg-card")}>
    <div className="space-y-2"><SessionTitle session={session} /><p className="text-sm text-muted-foreground">Đã kết thúc: <strong className="font-medium text-foreground">{formatDeadline(session.deadline)}</strong>{session.participant_count !== null && <span className="font-medium text-emerald-700 dark:text-emerald-400"> — {session.participant_count}/{studentCount} sinh viên tham gia</span>}</p></div>
    <div className="flex flex-wrap items-center gap-3"><span className="text-sm font-semibold text-slate-700 dark:text-slate-300">{session.problems.length} bài tập</span></div>
  </section>;
}
