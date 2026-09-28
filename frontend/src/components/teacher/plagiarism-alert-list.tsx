import Link from "next/link";
import { ArrowRight, FileSearch, TriangleAlert } from "lucide-react";

import { ErrorState } from "@/components/shared/page-state";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { PlagiarismAlert } from "@/lib/dashboard";

interface PlagiarismAlertListProps {
  alerts?: PlagiarismAlert[];
  isLoading: boolean;
  error: unknown;
  onRetry: () => void;
}

function AlertCard({ alert }: { alert: PlagiarismAlert }) {
  return (
    <li className="overflow-hidden rounded-md border border-red-200 border-t-[6px] border-t-red-700 bg-card dark:border-red-500/30">
      <div className="space-y-2 p-4">
        <div className="flex items-center justify-between gap-2">
          <span className="rounded bg-red-100 px-2.5 py-1 text-sm font-semibold text-red-700 dark:bg-red-500/20 dark:text-red-300">
            Chống gian lận
          </span>
          <span className="text-sm font-bold text-red-700 dark:text-red-300">{alert.problem_code}</span>
        </div>
        <ul className="list-disc space-y-1 pl-5 text-sm marker:text-slate-400">
          <li className="font-medium">{alert.student_names.join(" & ")}</li>
          <li className="text-muted-foreground">{alert.reason}</li>
        </ul>
      </div>
      <div className="flex items-center justify-between gap-2 bg-red-50 px-4 py-2 dark:bg-red-500/10">
        <p className="flex items-center gap-1.5 text-sm font-semibold text-red-600 dark:text-red-300">
          <TriangleAlert className="size-4" /> Trùng lặp {alert.similarity}%
        </p>
        <Button asChild size="sm" variant="outline" className="h-7 border-red-200 bg-card text-xs font-semibold">
          <Link href={`/teacher/plagiarism/${alert.id}`}>
            Đối chiếu code <FileSearch className="size-3.5" />
          </Link>
        </Button>
      </div>
    </li>
  );
}

export function PlagiarismAlertList({ alerts, isLoading, error, onRetry }: PlagiarismAlertListProps) {
  function renderBody() {
    if (isLoading) return <Skeleton className="h-96 w-full rounded-md" />;
    if (error && !alerts) return <ErrorState error={error} onRetry={onRetry} />;
    if (!alerts?.length) return <p className="py-10 text-center text-sm text-muted-foreground">Chưa phát hiện trường hợp nghi vấn.</p>;
    return (
      <ul className="max-h-[38rem] space-y-4 overflow-y-auto pr-1">
        {alerts.map((alert) => <AlertCard key={alert.id} alert={alert} />)}
      </ul>
    );
  }

  return (
    <div className="space-y-4 rounded-xl border bg-card p-5 shadow-sm">
      {renderBody()}
      <div className="flex justify-end">
        <Link href="/teacher/plagiarism" className="inline-flex items-center gap-1.5 text-sm font-semibold text-indigo-700 hover:underline dark:text-indigo-300">
          Xem tất cả <ArrowRight className="size-4" />
        </Link>
      </div>
    </div>
  );
}
