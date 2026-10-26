"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { PendingSubmissionsPanel } from "@/components/teacher/pending-submissions-panel";
import { usePendingSubmissions } from "@/lib/hooks/use-dashboard";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import type { PendingFilter } from "@/lib/types/dashboard";

export default function SubmissionsPage() {
  useBreadcrumbLabel("Bài nộp cần chấm & phúc khảo");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<PendingFilter>("all");
  const searchParams = useSearchParams();
  const debouncedSearch = useDebouncedValue(search, 300);

  const pending = usePendingSubmissions({ filter, search: debouncedSearch.trim() || undefined, course: searchParams.get("course") ?? undefined, lesson_id: Number(searchParams.get("lesson_id")) || undefined, problem_id: Number(searchParams.get("problem_id")) || undefined });

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-3xl">
          Tất cả bài nộp cần can thiệp
        </h1>
        <p className="text-muted-foreground">
          Danh sách sinh viên nộp bài muộn, bài chấm sai testcase hoặc có dấu hiệu trùng lặp cao cần giảng viên xử lý.
        </p>
      </div>

      <PendingSubmissionsPanel
        data={pending.data}
        isLoading={pending.isPending}
        isFetching={pending.isFetching}
        error={pending.error}
        onRetry={() => void pending.refetch()}
        search={search}
        onSearchChange={setSearch}
        filter={filter}
        onFilterChange={setFilter}
      />
    </div>
  );
}
