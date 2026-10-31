"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { PendingSubmissionsTable } from "@/components/teacher/pending-submissions-table";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { getPendingSubmissions } from "@/lib/api/endpoints/dashboard";
import type { PendingSubmission } from "@/lib/types/dashboard";

type Tab = "all" | "pending" | "needs_review";

export function ProblemSubmissionsPanel({ courseId, lessonId, problemId, title = "Bài nộp của problem" }: { courseId: string; lessonId: string; problemId?: string; title?: string }) {
  const [items, setItems] = useState<PendingSubmission[]>([]);
  const [tab, setTab] = useState<Tab>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  // `cancelled` chặn response về trễ ghi đè lên dữ liệu của lần tải mới hơn.
  const reload = useCallback((isCancelled: () => boolean = () => false) => {
    setLoading(true);
    setError(null);
    return getPendingSubmissions({ filter: "all", limit: 500, course: courseId, lesson_id: Number(lessonId), ...(problemId ? { problem_id: Number(problemId) } : {}), include_graded: true })
      .then((response) => { if (!isCancelled()) setItems(response.items); })
      .catch((requestError) => { if (!isCancelled()) setError(requestError); })
      .finally(() => { if (!isCancelled()) setLoading(false); });
  }, [courseId, lessonId, problemId]);

  useEffect(() => {
    let active = true;
    const isCancelled = () => !active;
    void Promise.resolve().then(() => reload(isCancelled));
    const onUpdated = () => { void reload(isCancelled); };
    window.addEventListener("submission:updated", onUpdated);
    return () => { active = false; window.removeEventListener("submission:updated", onUpdated); };
  }, [reload]);

  const pendingItems = useMemo(() => items.filter((item) => item.status === "pending"), [items]);
  const needsReviewItems = useMemo(() => items.filter((item) => ["wrong_answer", "compile_error"].includes(item.status)), [items]);
  const searched = useMemo(() => { const query = search.trim().toLowerCase(); return query ? items.filter((item) => `${item.student_name} ${item.student_code} ${item.topic}`.toLowerCase().includes(query)) : items; }, [items, search]);
  const filtered = (tab === "all" ? searched : tab === "pending" ? pendingItems : needsReviewItems).filter((item) => !search.trim() || `${item.student_name} ${item.student_code} ${item.topic}`.toLowerCase().includes(search.trim().toLowerCase()));
  const pageSize = 20;
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const visibleRows = filtered.slice((page - 1) * pageSize, page * pageSize);
  const tabs: Array<{ value: Tab; label: string; count: number }> = [{ value: "all", label: "Tất cả", count: items.length }, { value: "pending", label: "Đang chờ", count: pendingItems.length }, { value: "needs_review", label: "Sai kết quả / lỗi biên dịch", count: needsReviewItems.length }];

  return <section id="submissions" className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm"><div><h2 className="text-lg font-bold text-[#2f226b]">{title}</h2><p className="text-sm text-muted-foreground">Tất cả bài nộp thuộc đúng lớp học phần và buổi học hiện tại. Có thể mở lại và ghi đè điểm nhiều lần.</p></div><div className="flex flex-wrap items-center gap-3"><Input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Tìm theo tên hoặc MSSV..." className="h-10 max-w-sm" />{tabs.map((item) => <button key={item.value} type="button" onClick={() => { setTab(item.value); setPage(1); }} className={`rounded-md px-3 py-1.5 text-sm font-medium ${tab === item.value ? "bg-indigo-100 text-indigo-700" : "bg-muted text-muted-foreground"}`}>{item.label} ({item.count})</button>)}</div>{loading ? <Skeleton className="h-64 w-full rounded-lg" /> : error ? <ErrorState error={error} /> : !filtered.length ? <EmptyState title="Chưa có bài nộp" description="Không có bài nộp ở bộ lọc đang chọn." /> : <><PendingSubmissionsTable rows={visibleRows} showScore showGraded returnTo={problemId ? `/teacher/courses/${courseId}/sessions/${lessonId}/problems/${problemId}` : `/teacher/courses/${courseId}/sessions/${lessonId}`} /><div className="flex items-center justify-between text-sm"><span>Trang {page}/{pageCount} · {filtered.length} bài nộp</span><div className="flex gap-2"><button type="button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)} className="rounded border px-3 py-1 disabled:opacity-50">Trước</button><button type="button" disabled={page >= pageCount} onClick={() => setPage((current) => current + 1)} className="rounded border px-3 py-1 disabled:opacity-50">Sau</button></div></div></>}</section>;
}
