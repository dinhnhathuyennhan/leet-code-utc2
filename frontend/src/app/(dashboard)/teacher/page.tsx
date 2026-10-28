"use client";

import { useEffect, useState } from "react";

import { ErrorState } from "@/components/shared/page-state";
import { DashboardBanner, DashboardBannerSkeleton } from "@/components/teacher/dashboard-banner";
import { PendingSubmissionsPanel } from "@/components/teacher/pending-submissions-panel";
import { RecentCourses, RecentCoursesSkeleton } from "@/components/teacher/recent-courses";
import { usePendingSubmissions, useTeacherOverview } from "@/lib/hooks/use-dashboard";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import type { PendingFilter } from "@/lib/types/dashboard";

const SECTION_TITLE = "text-xl font-semibold tracking-tight";

export default function TeacherDashboardPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<PendingFilter>("all");
  const debouncedSearch = useDebouncedValue(search, 300);
  const overview = useTeacherOverview();
  const { refetch: refetchOverview } = overview;
  const pending = usePendingSubmissions({ filter, search: debouncedSearch.trim() || undefined, limit: 8 });

  useEffect(() => {
    const onSubmissionUpdated = () => { void refetchOverview(); };
    window.addEventListener("submission:updated", onSubmissionUpdated);
    return () => window.removeEventListener("submission:updated", onSubmissionUpdated);
  }, [refetchOverview]);

  return (
    <div className="space-y-8">
      {overview.isPending && <DashboardBannerSkeleton />}
      {overview.error && !overview.data && <ErrorState error={overview.error} onRetry={() => void overview.refetch()} />}
      {overview.data && <DashboardBanner overview={overview.data} />}

      <section className="space-y-4">
        <h2 className={SECTION_TITLE}>Lớp học truy cập gần đây</h2>
        {overview.isPending ? <RecentCoursesSkeleton /> : overview.data && <RecentCourses courses={overview.data.recent_courses} hrefFor={(course) => `/teacher/courses/${course.code || course.id}`} />}
      </section>

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
    </div>
  );
}
