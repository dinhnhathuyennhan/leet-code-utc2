"use client";

import { useEffect, useMemo } from "react";
import Link from "next/link";
import { ArrowRight, Search, X } from "lucide-react";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { PendingSubmissionsTable } from "@/components/teacher/pending-submissions-table";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import type { PendingFilter, PendingSubmissionsResponse } from "@/lib/types/dashboard";
import { cn } from "@/lib/utils";

const CHIPS: { value: PendingFilter; label: string }[] = [{ value: "all", label: "Tất cả" }, { value: "pending", label: "Đang chờ" }, { value: "wrong_answer", label: "Sai kết quả" }, { value: "compile_error", label: "Lỗi biên dịch" }];

interface Props { data?: PendingSubmissionsResponse; isLoading: boolean; isFetching: boolean; error: unknown; onRetry: () => void; search: string; onSearchChange: (value: string) => void; filter: PendingFilter; onFilterChange: (value: PendingFilter) => void; }

export function PendingSubmissionsPanel({ data, isLoading, isFetching, error, onRetry, search, onSearchChange, filter, onFilterChange }: Props) {
  useEffect(() => {
    const onUpdated = () => { onRetry(); };
    window.addEventListener("submission:updated", onUpdated);
    return () => window.removeEventListener("submission:updated", onUpdated);
  }, [onRetry]);

  // `status` và `manual_score` đã có sẵn trong danh sách, không cần gọi chi tiết từng bài.
  const supportedRows = useMemo(() => (data?.items ?? []).filter((item) => ["pending", "wrong_answer", "compile_error"].includes(item.status) && item.manual_score == null), [data?.items]);
  const rows = filter === "all" ? supportedRows : supportedRows.filter((item) => item.status === filter);
  const countFor = (value: PendingFilter) => value === "all" ? supportedRows.length : supportedRows.filter((item) => item.status === value).length;

  function renderBody() {
    if (isLoading) return <Skeleton className="h-80 w-full rounded-lg" />;
    if (error && !data) return <ErrorState error={error} onRetry={onRetry} />;
    if (!rows.length) return <EmptyState title="Không có bài nộp cần xử lý" description="Thử đổi bộ lọc hoặc từ khóa khác." />;
    return <div className={cn("transition-opacity duration-200", isFetching && "opacity-60")}><PendingSubmissionsTable rows={rows} showGraded returnTo="/teacher/submissions" /></div>;
  }

  return <div className="space-y-4 rounded-xl border bg-card p-5 shadow-sm"><div className="relative sm:max-w-md"><Search aria-hidden className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => onSearchChange(event.target.value)} placeholder="Tìm theo mã SV, tên sinh viên, bài..." aria-label="Tìm bài nộp" className="h-11 bg-muted/50 pl-10" />{search && <button type="button" onClick={() => onSearchChange("")} aria-label="Xóa tìm kiếm" className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"><X className="size-4" /></button>}</div><div role="group" aria-label="Lọc bài nộp" className="flex flex-wrap gap-2">{CHIPS.map((chip) => <button key={chip.value} type="button" aria-pressed={filter === chip.value} onClick={() => onFilterChange(chip.value)} className={cn("rounded-md px-3 py-1.5 text-sm font-medium outline-none transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500", filter === chip.value ? "bg-indigo-100 text-indigo-700" : "bg-indigo-50/60 text-slate-600 hover:bg-indigo-100/70 dark:bg-slate-800 dark:text-slate-300")}>{chip.label} ({countFor(chip.value)})</button>)}</div>{renderBody()}{rows.length > 0 && <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-sm"><p className="text-muted-foreground">Hiển thị {rows.length} trên {supportedRows.length} bài nộp cần xử lý</p><Link href="/teacher/submissions" className="inline-flex items-center gap-1.5 font-semibold text-indigo-700 hover:underline">Xem tất cả <ArrowRight className="size-4" /></Link></div>}</div>;
}
