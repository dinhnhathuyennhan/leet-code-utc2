import { CheckSquare, Cpu, Star } from "lucide-react";
import type { ReactNode } from "react";
import type { SessionDetailData } from "@/lib/types/course";

type Props = Pick<SessionDetailData, "stats" | "total_students" | "submitted_students">;

function StatCard({ title, value, icon, note, tone }: { title: string; value: ReactNode; icon: ReactNode; note: ReactNode; tone: string }) {
  return (
    <div className="rounded-2xl border bg-card p-5 shadow-xs">
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <p className="my-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">{value}</p>
      <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
        <span className={`flex size-7 items-center justify-center rounded-md ${tone}`}>{icon}</span>
        <span className="font-medium">{note}</span>
      </div>
    </div>
  );
}

export function SessionStats({ stats, total_students, submitted_students }: Props) {
  // Chưa ai nộp thì không có điểm để tính trung bình → hiện "—" thay vì số giả.
  const hasScores = submitted_students > 0 && stats.avg_score != null;

  return (
    <div className="grid gap-5 md:grid-cols-3">
      <StatCard
        title="Tỉ lệ nộp bài"
        value={`${stats.submission_rate}%`}
        icon={<CheckSquare className="size-4" />}
        note={`${stats.completed_students}/${total_students} SV hoàn thành`}
        tone="bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300"
      />
      <StatCard
        title="Điểm TB buổi học"
        value={
          <>
            {hasScores ? stats.avg_score : "—"}
            {hasScores && <span className="text-lg font-normal text-muted-foreground"> / 10</span>}
          </>
        }
        icon={<Star className="size-4 fill-amber-500 text-amber-500" />}
        note={hasScores ? stats.score_diff : "Chưa có bài nộp để tính điểm"}
        tone="bg-amber-100 text-amber-700 dark:bg-amber-500/20"
      />
      <StatCard
        title="Nghi vấn AST"
        value={`${stats.ast_cases} cặp sinh viên`}
        icon={<Cpu className="size-4" />}
        note={stats.ast_similarity}
        tone="bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300"
      />
    </div>
  );
}