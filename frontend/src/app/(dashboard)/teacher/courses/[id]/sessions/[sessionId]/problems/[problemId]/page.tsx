"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft, Clock3, FileCode2, FlaskConical, Lightbulb, MemoryStick, Terminal } from "lucide-react";
import Link from "next/link";

import { ErrorState, ForbiddenState } from "@/components/shared/page-state";
import { ApiError } from "@/lib/api/error";
import { ProblemSubmissionsPanel } from "@/components/teacher/problem-submissions-panel";
import { TestcaseManager } from "@/components/teacher/testcase-manager";
import { useBreadcrumbLabels } from "@/components/shared/breadcrumb-context";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getProblemDetail } from "@/lib/api/endpoints/courses";
import type { ProblemDetailData } from "@/lib/types/course";

export default function TeacherProblemDetailPage() {
  const { id: courseId, sessionId, problemId } = useParams<{ id: string; sessionId: string; problemId: string }>();
  const [data, setData] = useState<ProblemDetailData | null>(null);
  const [error, setError] = useState<unknown>(null);

  useBreadcrumbLabels(courseId, data?.title ?? "Chi tiết bài tập");

  useEffect(() => {
    getProblemDetail(courseId, sessionId, problemId)
      .then(setData)
      .catch(setError);
  }, [courseId, sessionId, problemId]);

  if (error) return error instanceof ApiError && error.status === 403 ? <ForbiddenState /> : <ErrorState error={error} />;
  if (!data) return <ProblemDetailSkeleton />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link href={`/teacher/courses/${courseId}/sessions/${sessionId}`} className="mb-2 inline-flex items-center gap-1 text-sm font-medium text-indigo-700 hover:underline"><ArrowLeft className="size-4" /> Quay lại buổi học</Link>
          <h1 className="text-2xl font-bold text-foreground">{data.code ?? "Bài tập"}: {data.title}</h1>
          <p className="text-sm text-muted-foreground">Tên hàm: <code>{data.function_name ?? "Chưa khai báo"}</code></p>
        </div>
        <Button asChild className="bg-[#2f226b] text-white hover:bg-[#251b56]"><Link href="#submissions"><Terminal className="size-4" /> Xem bài nộp</Link></Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-4">
        <Stat icon={<Clock3 />} label="Thời gian chạy" value={`${data.time_limit_seconds}s`} />
        <Stat icon={<MemoryStick />} label="Mức độ" value={levelLabel(data.level)} />
        <Stat icon={<FlaskConical />} label="Test cases" value={String(data.total_number_testcase)} />
        <Stat icon={<FileCode2 />} label="Độ phức tạp" value={data.complexity ?? "Chưa cập nhật"} />
      </div>

      <section className="grid gap-5 lg:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.65fr)]">
        <div className="space-y-5 rounded-2xl border bg-card p-6 shadow-sm">
          <Section title="Đề bài"><p className="whitespace-pre-wrap text-sm leading-7 text-muted-foreground">{data.description}</p></Section>
          <Section title="Ràng buộc"><pre className="whitespace-pre-wrap rounded-xl bg-muted p-4 text-sm leading-6 text-foreground">{data.constraints}</pre></Section>
          {data.hint && <Section title="Gợi ý"><p className="flex gap-2 text-sm leading-6 text-muted-foreground"><Lightbulb className="mt-1 size-4 shrink-0 text-amber-500" />{data.hint}</p></Section>}
          <Section title="Mã nguồn khởi tạo cho sinh viên"><pre className="overflow-x-auto rounded-xl bg-slate-900 p-5 text-sm leading-6 text-slate-100">{data.starter_code}</pre></Section>
        </div>

        <section className="h-fit space-y-3 rounded-2xl border bg-card p-6 shadow-sm"><h2 className="font-bold text-foreground">Test cases mẫu</h2>{data.testcases.filter((testcase) => testcase.is_sample).map((testcase, index) => <div key={testcase.id} className="rounded-xl bg-muted p-4 text-sm"><p className="mb-2 font-semibold text-foreground">Test #{index + 1}</p><div className="grid gap-2"><div><p className="text-xs text-muted-foreground">Input</p><pre className="whitespace-pre-wrap rounded bg-background p-2">{testcase.input}</pre></div><div><p className="text-xs text-muted-foreground">Output mong đợi</p><pre className="whitespace-pre-wrap rounded bg-background p-2">{testcase.expected_output}</pre></div></div></div>)}</section>
      </section>
      <ProblemSubmissionsPanel courseId={courseId} lessonId={sessionId} problemId={problemId} />
      <TestcaseManager courseId={courseId} lessonId={sessionId} problemId={problemId} hasSubmissions={(data.submitted_count ?? 0) > 0} />
    </div>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return <div className="rounded-xl border bg-card p-4 shadow-sm"><div className="mb-2 flex items-center gap-2 text-indigo-700">{icon}<span className="text-xs font-medium text-muted-foreground">{label}</span></div><p className="font-bold text-foreground">{value}</p></div>;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="space-y-2"><h2 className="font-bold text-[#2f226b]">{title}</h2>{children}</section>;
}

function levelLabel(level: string) {
  return level === "easy" ? "Dễ" : level === "hard" ? "Khó" : "Trung bình";
}

function ProblemDetailSkeleton() {
  return <div className="space-y-6"><Skeleton className="h-16 w-full rounded-2xl" /><div className="grid gap-4 sm:grid-cols-4"><Skeleton className="h-24 rounded-xl" /><Skeleton className="h-24 rounded-xl" /><Skeleton className="h-24 rounded-xl" /><Skeleton className="h-24 rounded-xl" /></div><Skeleton className="h-[560px] w-full rounded-2xl" /></div>;
}
