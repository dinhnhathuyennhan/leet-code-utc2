"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ClipboardList, History, Search } from "lucide-react";

import { SubmissionStatusBadge } from "@/components/student/submission-status-badge";
import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/helpers/datetime";
import { scoreOutOfTen } from "@/lib/helpers/submission-status";
import { useMySubmissions } from "@/lib/hooks/use-submissions";
import { useLocale } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { StudentSubmission } from "@/lib/types/submission";

type FilterKey = "all" | "accepted" | "wrong_answer" | "compile_error" | "pending";

const FILTERS: {
  key: FilterKey;
  labelKey:
    | "filter.all"
    | "history.filter.accepted"
    | "history.filter.wrongAnswer"
    | "history.filter.compileError"
    | "history.filter.pending";
}[] = [
  { key: "all", labelKey: "filter.all" },
  { key: "accepted", labelKey: "history.filter.accepted" },
  { key: "wrong_answer", labelKey: "history.filter.wrongAnswer" },
  { key: "compile_error", labelKey: "history.filter.compileError" },
  { key: "pending", labelKey: "history.filter.pending" },
];

/**
 * Trang lịch sử nộp bài của sinh viên.
 *
 * Hiển thị danh sách bài đã nộp kèm kết quả chấm, lọc theo trạng thái và
 * tìm kiếm theo tên/mã bài. Click vào 1 dòng để xem chi tiết kết quả.
 */
export default function SubmissionHistoryPage() {
  const { t } = useLocale();
  useBreadcrumbLabel("nav.history");

  const submissionsQuery = useMySubmissions();
  const [filter, setFilter] = useState<FilterKey>("all");
  const [search, setSearch] = useState("");

  const items = useMemo(
    () => submissionsQuery.data?.items ?? [],
    [submissionsQuery.data?.items],
  );

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    return items.filter((item) => {
      if (filter !== "all" && item.status !== filter) return false;
      if (!query) return true;
      return `${item.problem_code ?? ""} ${item.problem_title} ${item.course_name} ${item.session_label}`
        .toLowerCase()
        .includes(query);
    });
  }, [items, filter, search]);

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t("history.title")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("history.desc")}
          </p>
        </div>
      </header>

      {/* ─── Toolbar ───────────────────────────────────────────────────── */}
      <section className="flex flex-col items-stretch gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:max-w-sm">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t("history.searchPlaceholder")}
            aria-label={t("history.searchLabel")}
            className="h-10 w-full rounded-full border border-border bg-background pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-[#352078] focus:outline-none focus:ring-2 focus:ring-[#352078]/20"
          />
        </div>

        <div className="flex flex-wrap items-center gap-1.5 lg:ml-auto">
          {FILTERS.map((option) => {
            const count =
              option.key === "all"
                ? (submissionsQuery.data?.counts.all ?? 0)
                : (submissionsQuery.data?.counts[option.key] ?? 0);
            const active = filter === option.key;
            return (
              <button
                key={option.key}
                type="button"
                onClick={() => setFilter(option.key)}
                aria-pressed={active}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                  active
                    ? "border-[#352078] bg-[#352078] text-white"
                    : "border-border bg-background text-muted-foreground hover:bg-muted",
                )}
              >
                {t(option.labelKey)}
                <span className={cn("tabular-nums", active ? "text-white/70" : "text-muted-foreground/70")}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </section>

      {/* ─── Danh sách ─────────────────────────────────────────────────── */}
      {submissionsQuery.isPending ? (
        <SubmissionsSkeleton />
      ) : submissionsQuery.error ? (
        <ErrorState
          error={submissionsQuery.error}
          onRetry={() => void submissionsQuery.refetch()}
        />
      ) : !items.length ? (
        <EmptyState
          icon={History}
          title={t("history.empty.title")}
          description={t("history.empty.desc")}
        />
      ) : !filtered.length ? (
        <EmptyState
          icon={ClipboardList}
          title={t("history.noMatch.title")}
          description={t("history.noMatch.desc")}
        />
      ) : (
        <ul className="divide-y overflow-hidden rounded-2xl border bg-card">
          {filtered.map((item) => (
            <SubmissionRow key={item.id} item={item} />
          ))}
        </ul>
      )}
    </div>
  );
}

/* ─── Helpers ─────────────────────────────────────────────────────────────── */

function SubmissionRow({ item }: { item: StudentSubmission }) {
  const { t } = useLocale();
  const score = scoreOutOfTen(item.passed_count, item.total_testcases);
  return (
    <li>
      <Link
        href={`/student/submissions/${item.id}`}
        className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-muted/40"
      >
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs text-muted-foreground">
              {item.problem_code ?? `${t("history.problemFallback")} ${item.problem_id}`}
            </span>
            <span className="truncate text-sm font-semibold">{item.problem_title}</span>
          </div>
          <p className="mt-0.5 truncate text-xs text-muted-foreground">
            {item.course_name} · {item.session_label} · {item.language}
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="hidden sm:inline">{formatDate(item.submitted_datetime)}</span>
          <span className="tabular-nums">
            {item.passed_count}/{item.total_testcases} {t("history.testSuffix")}
          </span>
          {score !== null && (
            <span className="font-semibold tabular-nums text-foreground">{score.toFixed(1)}/10</span>
          )}
          <SubmissionStatusBadge status={item.status} />
        </div>
      </Link>
    </li>
  );
}

function SubmissionsSkeleton() {
  const { t } = useLocale();
  return (
    <div className="space-y-2" aria-busy="true" aria-label={t("history.loading")}>
      {[1, 2, 3, 4, 5].map((item) => (
        <Skeleton key={item} className="h-16 w-full rounded-xl" />
      ))}
    </div>
  );
}
