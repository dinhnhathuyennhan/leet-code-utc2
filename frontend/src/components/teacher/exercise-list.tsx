import Link from "next/link";
import { ArrowRight, Clock, Eye, FileCode2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { SessionDetailData } from "@/lib/types/course";

type Exercise = SessionDetailData["exercises"][number];

const LEVELS: Record<string, { label: string; cls: string }> = {
  easy: { label: "DỄ", cls: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300" },
  medium: { label: "TRUNG BÌNH", cls: "bg-amber-50 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300" },
  hard: { label: "KHÓ", cls: "bg-red-50 text-red-700 dark:bg-red-500/20 dark:text-red-300" },
};

type Props = {
  exercises: Exercise[];
  courseId: string;
  sessionId: string;
  editHref: string;
};

export function ExerciseList({ exercises, courseId, sessionId, editHref }: Props) {
  const submissionsOf = `/teacher/courses/${courseId}/sessions/${sessionId}#submissions`;

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
          Danh sách bài tập thực hành ({String(exercises.length).padStart(2, "0")})
        </h2>
        <Link href={submissionsOf} className="flex items-center gap-1.5 text-sm font-semibold text-[#2f226b] hover:underline dark:text-indigo-300">
          Xem tất cả bài nộp buổi này <ArrowRight className="size-4" />
        </Link>
      </div>

      {exercises.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed bg-card p-10 text-center">
          <FileCode2 className="size-8 text-muted-foreground" />
          <p className="font-semibold">Buổi học chưa có bài tập</p>
          <p className="text-sm text-muted-foreground">Thêm bài từ ngân hàng đề hoặc tạo bài mới.</p>
          <Button asChild className="bg-[#2f226b] text-white hover:bg-[#251b56]">
            <Link href={editHref}>Soạn bài tập</Link>
          </Button>
        </div>
      )}

      <div className="space-y-3.5">
        {exercises.map((item) => {
          const level = LEVELS[item.level] ?? { label: String(item.level).toUpperCase(), cls: "bg-slate-100 text-slate-700" };
          return (
            <div key={item.id} className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border bg-card p-5 shadow-xs transition hover:shadow-md">
              <div className="flex items-start gap-4">
                <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-indigo-50 font-bold text-indigo-950 dark:bg-slate-800 dark:text-indigo-200">
                  {item.order}
                </span>
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">{item.title}</h3>
                    {item.report && (
                      <span className="rounded bg-indigo-50 px-2 py-0.5 font-mono text-xs font-semibold text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
                        {item.report}
                      </span>
                    )}
                    <span className={`rounded px-2 py-0.5 text-xs font-semibold ${level.cls}`}>{level.label}</span>
                  </div>
                  <p className="line-clamp-2 max-w-3xl text-sm text-muted-foreground">{item.description}</p>
                  <div className="flex flex-wrap items-center gap-4 pt-1 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><Clock className="size-3.5" /> {item.time_limit_seconds}s</span>
                    <span className="flex items-center gap-1"><FileCode2 className="size-3.5" /> {item.total_number_testcase} test case</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Button asChild variant="outline" className="h-10 gap-1.5 border-slate-300 font-medium">
                  <Link href={`/teacher/courses/${courseId}/sessions/${sessionId}/problems/${item.id}`}>
                    <Eye className="size-4" /> Xem chi tiết
                  </Link>
                </Button>
                <Button asChild className="h-10 gap-1.5 bg-[#2f226b] font-semibold text-white hover:bg-[#251b56]">
                  <Link href={`/teacher/courses/${courseId}/sessions/${sessionId}/problems/${item.id}#submissions`}>
                    Xem {item.submitted_count} bài nộp <ArrowRight className="size-4" />
                  </Link>
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
