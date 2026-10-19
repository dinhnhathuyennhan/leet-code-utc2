"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, Code2, FileText, Lock, PlayCircle } from "lucide-react";

import type { CourseDetail, GradeScoreValue } from "@/lib/types/course";
import { formatDate } from "@/lib/helpers/format";
import { cn } from "@/lib/utils";

type SessionStatus = "open" | "closed" | "upcoming";
type AssignmentStatus = "not_started" | "submitted" | "graded";

function scoreOf(value: GradeScoreValue | undefined): number | null {
  return value == null ? null : typeof value === "number" ? value : value.value;
}

function statusOf(value: GradeScoreValue | undefined): AssignmentStatus {
  if (value && typeof value === "object" && value.submitted && scoreOf(value) === null) return "submitted";
  return scoreOf(value) === null ? "not_started" : "graded";
}

const STATUS: Record<AssignmentStatus, { label: string; className: string }> = {
  not_started: { label: "Chưa làm", className: "bg-slate-100 text-slate-700" },
  submitted: { label: "Đã nộp", className: "bg-sky-100 text-sky-800" },
  graded: { label: "Đã chấm", className: "bg-emerald-100 text-emerald-800" },
};

const SESSION: Record<SessionStatus, { label: string; className: string }> = {
  open: { label: "Đang mở", className: "bg-emerald-500" },
  closed: { label: "Đã đóng", className: "bg-slate-400" },
  upcoming: { label: "Sắp mở", className: "bg-amber-500" },
};

export function StudentCourseInfoPanel({ course }: { course: CourseDetail }) {
  const firstOpen = course.sessions.find((session) => session.status === "open")?.id ?? course.sessions[0]?.id;
  const [openId, setOpenId] = useState<number | undefined>(firstOpen);
  const gradeRow = course.grades?.[0];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm font-semibold"><Code2 className="size-4 text-[#352078]" />Danh sách buổi học &amp; bài tập</div>
      {course.sessions.map((session) => {
        const meta = SESSION[session.status];
        const scores = gradeRow?.session_scores?.[String(session.id)] ?? [];
        return (
          <section key={session.id} className="overflow-hidden rounded-xl border bg-card">
            <button type="button" onClick={() => setOpenId((current) => current === session.id ? undefined : session.id)} className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left hover:bg-muted/40">
              <span className="flex items-center gap-3"><span className={cn("size-2.5 rounded-full", meta.className)} /><span><strong className="block text-sm">Buổi {session.order}: {session.title}</strong><span className="text-xs text-muted-foreground">{session.status === "upcoming" ? `Mở ${formatDate(session.opens_at ?? session.deadline)}` : `Hạn ${formatDate(session.deadline)}`}</span></span></span>
              <span className="flex items-center gap-3 text-xs text-muted-foreground"><span className="hidden sm:inline">{meta.label}</span><ChevronDown className={cn("size-4 transition-transform", openId === session.id && "rotate-180")} /></span>
            </button>
            {openId === session.id && <div className="border-t px-3 pb-2">
              {!session.problems.length ? <p className="py-4 text-sm text-muted-foreground">Buổi này chưa có bài tập hoặc chưa mở.</p> : <table className="w-full text-sm"><thead><tr className="text-xs text-muted-foreground"><th className="py-2 text-left">Mã bài</th><th className="py-2 text-left">Tên bài</th><th className="py-2 text-left">Trạng thái</th><th className="py-2 text-right">Điểm</th><th /></tr></thead><tbody>{session.problems.map((problem, index) => { const value = scores[index]; const status = statusOf(value); const badge = STATUS[status]; const locked = session.status === "upcoming"; return <tr key={problem.id} className="border-t"><td className="py-3 font-mono text-xs">{problem.report ?? `Bài ${problem.id}`}</td><td className="py-3">{problem.title}</td><td className="py-3"><span className={cn("rounded-md px-2 py-0.5 text-xs", badge.className)}>{badge.label}</span></td><td className="py-3 text-right">{scoreOf(value)?.toFixed(1) ?? "—"}/10</td><td className="py-3 text-right">{locked ? <Lock className="ml-auto size-4 text-muted-foreground" /> : <Link href={`/student/classes/${encodeURIComponent(course.code)}/assignments/${problem.id}`} className="inline-flex items-center gap-1 rounded-md bg-[#352078] px-2.5 py-1.5 text-xs text-white">{status === "not_started" ? <PlayCircle className="size-3.5" /> : <FileText className="size-3.5" />}{status === "not_started" ? "Làm bài" : "Xem bài"}</Link>}</td></tr>; })}</tbody></table>}
            </div>}
          </section>
        );
      })}
      {!course.sessions.length && <p className="text-sm text-muted-foreground">Chưa có buổi học nào.</p>}
    </div>
  );
}
