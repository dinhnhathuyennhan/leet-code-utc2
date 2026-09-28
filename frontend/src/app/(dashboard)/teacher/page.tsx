"use client";

import { useState } from "react";
import { Bot } from "lucide-react";

import { ErrorState } from "@/components/shared/page-state";
import { DashboardBanner, DashboardBannerSkeleton } from "@/components/teacher/dashboard-banner";
import { PendingSubmissionsPanel } from "@/components/teacher/pending-submissions-panel";
import { PlagiarismAlertList } from "@/components/teacher/plagiarism-alert-list";
import { RecentCourses, RecentCoursesSkeleton } from "@/components/teacher/recent-courses";
import { usePendingSubmissions, usePlagiarismAlerts, useTeacherOverview } from "@/lib/hooks/use-dashboard";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import type { PendingFilter } from "@/lib/types/dashboard";

const SECTION_TITLE = "text-xl font-semibold tracking-tight";

export default function TeacherDashboardPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<PendingFilter>("all");
  const debouncedSearch = useDebouncedValue(search, 300);

  // 3 query độc lập: mỗi khối tự loading/lỗi, không khối nào chặn khối khác.
  const overview = useTeacherOverview();
  const pending = usePendingSubmissions({ filter, search: debouncedSearch.trim() || undefined, limit: 5 });
  const plagiarism = usePlagiarismAlerts();

  return (
    <div className="space-y-8">
      {overview.isPending && <DashboardBannerSkeleton />}
      {overview.error && !overview.data && <ErrorState error={overview.error} onRetry={() => void overview.refetch()} />}
      {overview.data && <DashboardBanner overview={overview.data} />}

      <section className="space-y-4">
        <h2 className={SECTION_TITLE}>Lớp học truy cập gần đây</h2>
        {overview.isPending ? (
          <RecentCoursesSkeleton />
        ) : (
          overview.data && <RecentCourses courses={overview.data.recent_courses} hrefFor={(c) => `/teacher/courses/${c.id}`} />
        )}
      </section>

      <div className="grid items-start gap-8 xl:grid-cols-[minmax(0,1fr)_27rem]">
        <section className="space-y-4">
          <h2 className={SECTION_TITLE}>Bài nộp cần chấm và phúc khảo</h2>
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
        </section>

        <section className="space-y-4">
          <h2 className={`${SECTION_TITLE} flex items-center gap-2.5`}>
            <Bot className="size-6 text-indigo-700 dark:text-indigo-300" /> Cảnh báo đạo văn
          </h2>
          <PlagiarismAlertList
            alerts={plagiarism.data}
            isLoading={plagiarism.isPending}
            error={plagiarism.error}
            onRetry={() => void plagiarism.refetch()}
          />
        </section>
      </div>
    </div>
  );
}
