"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { BookOpen, Clock, FileText, Search } from "lucide-react";

import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDeadline } from "@/lib/helpers/datetime";
import { useCourses } from "@/lib/hooks/use-courses";
import { useLocale } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { CourseSession, ProblemRow } from "@/lib/types/course";

interface AssignmentRow {
  courseId: string;
  courseName: string;
  session: CourseSession;
  problem: ProblemRow;
}

/**
 * Trang "Bài tập" của sinh viên: gom toàn bộ bài tập của mọi lớp đang học
 * vào một danh sách để dễ tìm và nộp.
 *
 * Nguồn dữ liệu: `GET /courses` (backend đã lọc theo enrollment của sinh viên
 * và ẩn các bài chưa mở), mỗi course có `sessions[].problems[]`.
 */
export default function StudentAssignmentsPage() {
  const { t } = useLocale();
  useBreadcrumbLabel("nav.assignments");

  const coursesQuery = useCourses({});
  const [search, setSearch] = useState("");

  const assignments = useMemo<AssignmentRow[]>(() => {
    const rows: AssignmentRow[] = [];
    for (const course of coursesQuery.data?.items ?? []) {
      for (const session of course.sessions ?? []) {
        for (const problem of session.problems ?? []) {
          rows.push({
            courseId: String(course.id),
            courseName: course.name,
            session,
            problem,
          });
        }
      }
    }
    return rows;
  }, [coursesQuery.data?.items]);

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return assignments;
    return assignments.filter((row) =>
      `${row.problem.report ?? ""} ${row.problem.title} ${row.courseName} ${row.session.title}`
        .toLowerCase()
        .includes(query),
    );
  }, [assignments, search]);

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{t("student.assignments.title")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {t("student.assignments.desc")}
          </p>
        </div>
      </header>

      <div className="relative w-full sm:max-w-sm">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder={t("student.assignments.searchPlaceholder")}
          aria-label={t("student.assignments.searchLabel")}
          className="h-10 w-full rounded-full border border-border bg-background pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-[#352078] focus:outline-none focus:ring-2 focus:ring-[#352078]/20"
        />
      </div>

      {coursesQuery.isPending ? (
        <AssignmentsSkeleton />
      ) : coursesQuery.error ? (
        <ErrorState error={coursesQuery.error} onRetry={() => void coursesQuery.refetch()} />
      ) : !assignments.length ? (
        <EmptyState
          icon={BookOpen}
          title={t("student.assignments.empty.title")}
          description={t("student.assignments.empty.desc")}
        />
      ) : !filtered.length ? (
        <EmptyState
          icon={Search}
          title={t("student.assignments.noMatch.title")}
          description={t("student.assignments.noMatch.desc")}
        />
      ) : (
        <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((row) => (
            <AssignmentCard key={`${row.courseId}-${row.problem.id}`} row={row} />
          ))}
        </ul>
      )}
    </div>
  );
}

/* ─── Helpers ─────────────────────────────────────────────────────────────── */

const LEVEL_TONE: Record<string, string> = {
  easy: "bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300",
  medium: "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300",
  hard: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300",
};

function AssignmentCard({ row }: { row: AssignmentRow }) {
  const { t } = useLocale();
  const { courseId, courseName, session, problem } = row;
  const locked = session.status === "upcoming";

  return (
    <li>
      <Link
        href={`/student/classes/${encodeURIComponent(courseId)}/assignments/${problem.id}`}
        className={cn(
          "flex h-full flex-col gap-3 rounded-2xl border bg-card p-4 transition-all hover:border-[#352078]/40 hover:shadow-sm",
          locked && "pointer-events-none opacity-60",
        )}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-mono text-[11px] text-muted-foreground">
              {problem.report ?? `${t("history.problemFallback")} ${problem.id}`}
            </p>
            <h2 className="mt-0.5 truncate text-sm font-semibold">{problem.title}</h2>
          </div>
          <Badge className={cn("shrink-0 capitalize", LEVEL_TONE[problem.level] ?? LEVEL_TONE.easy)}>
            {problem.level}
          </Badge>
        </div>

        <p className="truncate text-xs text-muted-foreground">
          {courseName} · {t("student.assignments.sessionPrefix")} {session.order}: {session.title}
        </p>

        <div className="mt-auto flex items-center justify-between text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Clock className="size-3.5" />
            {session.deadline ? formatDeadline(session.deadline) : "—"}
          </span>
          <span className="inline-flex items-center gap-1">
            <FileText className="size-3.5" />
            {problem.total_number_testcase} {t("student.assignments.testCount")}
          </span>
        </div>
      </Link>
    </li>
  );
}

function AssignmentsSkeleton() {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3" aria-busy="true">
      {[1, 2, 3, 4, 5, 6].map((item) => (
        <Skeleton key={item} className="h-36 w-full rounded-2xl" />
      ))}
    </div>
  );
}
