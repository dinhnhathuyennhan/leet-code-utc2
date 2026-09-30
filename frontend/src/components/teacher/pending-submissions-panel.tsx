"use client";

import Link from "next/link";
import { ArrowRight, Search } from "lucide-react";

import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { PendingSubmissionsTable } from "@/components/teacher/pending-submissions-table";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import type { PendingFilter, PendingSubmissionsResponse } from "@/lib/types/dashboard";
import { cn } from "@/lib/utils";

const CHIPS: { value: PendingFilter; label: string }[] = [
  { value: "all", label: "Tất cả" },
  { value: "late_appeal", label: "Nộp muộn / Phúc khảo" },
  { value: "similarity", label: "Độ tương đồng cao" },
  { value: "error", label: "Lỗi runtime/CE" },
];

interface PendingSubmissionsPanelProps {
  data?: PendingSubmissionsResponse;
  isLoading: boolean;
  isFetching: boolean;
  error: unknown;
  onRetry: () => void;
  search: string;
  onSearchChange: (value: string) => void;
  filter: PendingFilter;
  onFilterChange: (value: PendingFilter) => void;
}

export function PendingSubmissionsPanel(props: PendingSubmissionsPanelProps) {
  const { data, isLoading, isFetching, error, onRetry, search, onSearchChange, filter, onFilterChange } = props;

  function renderBody() {
    if (isLoading) return <Skeleton className="h-80 w-full rounded-lg" />;
    if (error && !data) return <ErrorState error={error} onRetry={onRetry} />;
    if (!data?.items.length) return <EmptyState title="Không có bài nộp cần xử lý" description="Thử đổi bộ lọc hoặc từ khoá khác." />;
    return (
      <div className={cn("transition-opacity duration-200", isFetching && "opacity-60")}>
        <PendingSubmissionsTable rows={data.items} />
      </div>
    );
  }

  return (
    <div className="space-y-4 rounded-xl border bg-card p-5 shadow-sm">
      <div className="relative sm:max-w-md">
        <Search aria-hidden className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Tìm theo mã SV, bài tập..."
          aria-label="Tìm bài nộp"
          className="h-11 bg-muted/50 pl-10"
        />
      </div>

      <div role="group" aria-label="Lọc bài nộp" className="flex flex-wrap gap-2">
        {CHIPS.map((chip) => {
          const active = filter === chip.value;
          return (
            <button
              key={chip.value}
              type="button"
              aria-pressed={active}
              onClick={() => onFilterChange(chip.value)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium outline-none transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500",
                active
                  ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-500/25 dark:text-indigo-200"
                  : "bg-indigo-50/60 text-slate-600 hover:bg-indigo-100/70 dark:bg-slate-800 dark:text-slate-300",
              )}
            >
              {chip.label}
              {data && ` (${data.counts[chip.value]})`}
            </button>
          );
        })}
      </div>

      {renderBody()}

      {data && data.items.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-sm">
          <p className="text-muted-foreground">Hiển thị {data.items.length} trên {data.total} bài nộp cần can thiệp</p>
          <Link href="/teacher/submissions" className="inline-flex items-center gap-1.5 font-semibold text-indigo-700 hover:underline dark:text-indigo-300">
            Xem tất cả <ArrowRight className="size-4" />
          </Link>
        </div>
      )}
    </div>
  );
}
