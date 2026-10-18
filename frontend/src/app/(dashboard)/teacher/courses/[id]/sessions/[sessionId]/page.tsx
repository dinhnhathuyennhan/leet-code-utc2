"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  ArrowRight,
  Bell,
  Calendar,
  CheckSquare,
  Clock,
  Cpu,
  FileCode2,
  Plus,
  Send,
  Star,
  Users,
} from "lucide-react";

import { useBreadcrumbLabels } from "@/components/shared/breadcrumb-context";
import { ErrorState } from "@/components/shared/page-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { getSessionDetail } from "@/lib/api/endpoints/courses";
import type { SessionDetailData } from "@/lib/types/course";
import { SessionEditPage } from "@/components/teacher/session-edit-page";

export default function TeacherSessionDetailPage() {
  const { id: courseId, sessionId } = useParams<{ id: string; sessionId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [data, setData] = useState<SessionDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  useBreadcrumbLabels(courseId, data?.title ?? "Buổi học", searchParams.get("mode") === "edit" ? "Soạn bài tập" : null);

  useEffect(() => {
    getSessionDetail(courseId, sessionId)
      .then((res) => setData(res))
      .catch((requestError) => setError(requestError))
      .finally(() => setLoading(false));
  }, [courseId, sessionId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full rounded-2xl" />
        <div className="grid gap-5 md:grid-cols-3">
          <Skeleton className="h-28 rounded-2xl" />
          <Skeleton className="h-28 rounded-2xl" />
          <Skeleton className="h-28 rounded-2xl" />
        </div>
        <Skeleton className="h-24 w-full rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (error || !data) return <ErrorState error={error} />;
  if (searchParams.get("mode") === "edit") return <SessionEditPage courseId={courseId} sessionId={sessionId} data={data} />;

  return (
    <div className="space-y-6">
      {/* ─── Header buổi học ────────────────────────────────────────────────── */}
      <section className="flex flex-wrap items-start justify-between gap-6 rounded-2xl border bg-card p-6 shadow-xs">
        <div className="space-y-3">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-3xl">
            {data.title}
          </h1>
          <div className="flex flex-wrap items-center gap-6 text-[15px] text-muted-foreground">
            <span className="flex items-center gap-2">
              <Calendar className="size-4 text-slate-500" />
              Mở - đóng: <strong>{data.start_date} → {data.end_date}</strong>
            </span>
            <span className="flex items-center gap-2">
              <Users className="size-4 text-slate-500" />
              Sĩ số nộp: <strong>{data.submitted_students}/{data.total_students} SV</strong>
            </span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-3">
            <Button onClick={() => router.push(`/teacher/courses/${courseId}/sessions/${sessionId}?mode=edit`)} className="h-10 bg-[#2f226b] gap-1.5 font-semibold text-white hover:bg-[#251b56]">
              <Plus className="size-4" /> Thêm bài tập
            </Button>
          </div>
          <p className="text-sm font-semibold text-red-600 dark:text-red-400">
            {data.deadline_notice}
          </p>
        </div>
      </section>

      {/* ─── 3 Khối Thống kê ────────────────────────────────────────────────── */}
      <div className="grid gap-5 md:grid-cols-3">
        {/* Card 1: Tỉ lệ nộp bài */}
        <div className="rounded-2xl border bg-card p-5 shadow-xs">
          <p className="text-sm font-medium text-muted-foreground">Tỉ lệ nộp bài</p>
          <p className="my-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            {data.stats.submission_rate}%
          </p>
          <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <span className="flex size-7 items-center justify-center rounded-md bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
              <CheckSquare className="size-4" />
            </span>
            <span className="font-medium">{data.stats.completed_students}/{data.total_students} SV hoàn thành</span>
          </div>
        </div>

        {/* Card 2: Điểm TB môn học */}
        <div className="rounded-2xl border bg-card p-5 shadow-xs">
          <p className="text-sm font-medium text-muted-foreground">Điểm TB môn học</p>
          <p className="my-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            {data.stats.avg_score} <span className="text-lg font-normal text-muted-foreground">/ 10</span>
          </p>
          <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <span className="flex size-7 items-center justify-center rounded-md bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300">
              <Star className="size-4 fill-amber-500 text-amber-500" />
            </span>
            <span className="font-medium">{data.stats.score_diff}</span>
          </div>
        </div>

        {/* Card 3: Nghi vấn AST */}
        <div className="rounded-2xl border bg-card p-5 shadow-xs">
          <p className="text-sm font-medium text-muted-foreground">Nghi vấn AST</p>
          <p className="my-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            {data.stats.ast_cases} cặp sinh viên
          </p>
          <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <span className="flex size-7 items-center justify-center rounded-md bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300">
              <Cpu className="size-4" />
            </span>
            <span className="font-medium">{data.stats.ast_similarity}</span>
          </div>
        </div>
      </div>

      {/* ─── Cảnh báo hạn chót nộp bài ─────────────────────────────────────── */}
      {data.alert && data.alert.missing_students > 0 && (
      <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-amber-200 bg-[#fefce8] p-5 shadow-xs dark:border-amber-500/30 dark:bg-amber-500/10">
        <div className="flex items-center gap-4">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-red-600 text-white shadow-sm">
            <Bell className="size-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Cảnh báo hạn chót nộp bài
              </h3>
              {data.alert.problem_code && (
                <span className="rounded bg-red-100 px-2 py-0.5 font-mono text-xs font-bold text-red-700 dark:bg-red-500/20 dark:text-red-300">
                  {data.alert.problem_code}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-700 dark:text-slate-300">
              Có <strong className="font-bold text-slate-900 dark:text-slate-100">{data.alert.missing_students} sinh viên</strong> chưa nộp bài {data.alert.problem_name ?? ""}. Hạn chót đóng hệ thống tự động vào {data.alert.deadline_text ?? ""}.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button asChild variant="outline" className="h-10 bg-white font-semibold text-slate-800 shadow-xs hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-200">
            <Link href={`/teacher/submissions?course=${encodeURIComponent(data.course_code)}&lesson_id=${sessionId}`}>
            Xem danh sách {data.alert.missing_students} SV
            </Link>
          </Button>
          <Button className="h-10 bg-[#facc15] font-semibold text-amber-950 shadow-xs hover:bg-[#eab308]">
            <Send className="size-4" /> Gửi nhắc nhở
          </Button>
        </div>
      </section>
      )}

      {/* ─── Danh sách bài tập thực hành ───────────────────────────────────── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold tracking-wider text-slate-900 dark:text-slate-100 uppercase">
            DANH SÁCH BÀI TẬP THỰC HÀNH ({String(data.exercises.length).padStart(2, "0")})
          </h2>
          <Link
            href={`/teacher/submissions?course=${encodeURIComponent(data.course_code)}&lesson_id=${sessionId}`}
            className="flex items-center gap-1.5 text-sm font-semibold text-[#2f226b] hover:underline dark:text-indigo-300"
          >
            Xem tất cả bài nộp buổi này <ArrowRight className="size-4" />
          </Link>
        </div>

        <div className="space-y-3.5">
          {data.exercises.map((item) => (
            <div
              key={item.id}
              className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border bg-card p-5 shadow-xs transition hover:shadow-md"
            >
              <div className="flex items-start gap-4">
                <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-indigo-50 font-bold text-indigo-950 dark:bg-slate-800 dark:text-indigo-200">
                  {item.order}
                </span>

                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                      {item.title}
                    </h3>
                    <span className="rounded bg-indigo-50 px-2 py-0.5 font-mono text-xs font-semibold text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
                      {item.report ?? `Chưa có mã bài · ID ${item.id}`}
                    </span>
                    <span className="rounded bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300">
                      {item.level === "easy" ? "DỄ" : "TRUNG BÌNH"}
                    </span>
                  </div>

                  <p className="max-w-3xl text-sm text-muted-foreground">
                    {item.description}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 pt-1 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="size-3.5" /> {item.time_limit_seconds}s
                    </span>
                    <span className="flex items-center gap-1">
                      <FileCode2 className="size-3.5" /> {item.total_number_testcase} Test cases
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Button asChild variant="outline" className="h-10 gap-1.5 border-slate-300 font-medium text-slate-700 dark:text-slate-200">
                  <Link href={`/teacher/courses/${courseId}/sessions/${sessionId}/problems/${item.id}`}><Plus className="size-4" /> Xem chi tiết</Link>
                </Button>
                <Button asChild className="h-10 bg-[#2f226b] gap-1.5 font-semibold text-white hover:bg-[#251b56]">
                  <Link href={`/teacher/submissions?course=${encodeURIComponent(data.course_code)}&problem_id=${item.id}`}>
                  <Plus className="size-4" /> Xem {item.submitted_count} bài nộp
                  </Link>
                </Button>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
