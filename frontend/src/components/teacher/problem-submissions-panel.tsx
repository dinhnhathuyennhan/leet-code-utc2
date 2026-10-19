"use client";

import { useEffect, useMemo, useState } from "react";

import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { PendingSubmissionsTable } from "@/components/teacher/pending-submissions-table";
import { Skeleton } from "@/components/ui/skeleton";
import { getPendingSubmissions } from "@/lib/api/endpoints/dashboard";
import type { PendingSubmission } from "@/lib/types/dashboard";

type Tab = "all" | "graded" | "ungraded";

export function ProblemSubmissionsPanel({ courseId, lessonId, problemId }: { courseId: string; lessonId: string; problemId: string }) {
  const [items, setItems] = useState<PendingSubmission[]>([]);
  const [counts, setCounts] = useState({ all: 0, graded: 0, ungraded: 0 });
  const [tab, setTab] = useState<Tab>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    let active = true;
    void getPendingSubmissions({ filter: "all", limit: 500, course: courseId, lesson_id: Number(lessonId), problem_id: Number(problemId), include_graded: true })
      .then((response) => {
        if (!active) return;
        setItems(response.items);
        setCounts({ all: response.counts.all ?? response.items.length, graded: response.counts.graded ?? response.items.filter((item) => item.judge_kind === "graded").length, ungraded: response.items.filter((item) => item.judge_kind !== "graded").length });
      })
      .catch((requestError) => { if (active) setError(requestError); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [courseId, lessonId, problemId]);

  const filtered = useMemo(() => tab === "all" ? items : items.filter((item) => tab === "graded" ? item.judge_kind === "graded" : item.judge_kind !== "graded"), [items, tab]);
  const tabs: Array<{ value: Tab; label: string; count: number }> = [{ value: "all", label: "Tất cả", count: counts.all }, { value: "graded", label: "Đã chấm", count: counts.graded }, { value: "ungraded", label: "Chưa chấm", count: counts.ungraded }];

  return <section className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm"><div><h2 className="text-lg font-bold text-[#2f226b]">Bài nộp của problem</h2><p className="text-sm text-muted-foreground">Chỉ hiển thị bài nộp thuộc đúng lớp, buổi học và problem hiện tại.</p></div><div className="flex flex-wrap gap-2">{tabs.map((item) => <button key={item.value} type="button" onClick={() => setTab(item.value)} className={`rounded-md px-3 py-1.5 text-sm font-medium ${tab === item.value ? "bg-indigo-100 text-indigo-700" : "bg-muted text-muted-foreground"}`}>{item.label} ({item.count})</button>)}</div>{loading ? <Skeleton className="h-64 w-full rounded-lg" /> : error ? <ErrorState error={error} /> : !filtered.length ? <EmptyState title="Chưa có bài nộp" description="Problem này chưa có bài nộp ở tab đang chọn." /> : <PendingSubmissionsTable rows={filtered} />}</section>;
}
