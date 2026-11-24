"use client";

import Link from "next/link";
import { ArrowLeft, Clock3, FileCode2, FlaskConical, Lightbulb, Pencil } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ErrorState, ForbiddenState } from "@/components/shared/page-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/error";
import { getAdminBankProblem } from "@/lib/api/endpoints/admin-management";
import type { AdminProblem } from "@/lib/types/admin";
import { AdminProblemPreview } from "@/components/admin/admin-problem-preview";
import { Button } from "@/components/ui/button";

export function TeacherBankProblemDetail() {
  const { id } = useParams<{ id: string }>();
  const [problem, setProblem] = useState<AdminProblem | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    getAdminBankProblem(Number(id)).then(setProblem).catch(setError);
  }, [id]);

  if (error) return error instanceof ApiError && error.status === 403 ? <ForbiddenState /> : <ErrorState error={error} />;
  if (!problem) return <ProblemDetailSkeleton />;

  return (
    <div className="space-y-6">
      <Link href="/teacher/problem-bank" className="inline-flex items-center gap-2 text-sm font-medium text-indigo-700 hover:underline">
        <ArrowLeft className="size-4" /> Quay lại ngân hàng đề
      </Link>
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
        <p className="font-mono text-sm text-indigo-700">{problem.code ?? `Problem #${problem.id}`}</p>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{problem.title}</h1>
        <p className="text-sm text-muted-foreground">{problem.lesson_id === null ? "Đề thư viện dùng chung" : "Đề đã gắn lớp"} · {problem.total_number_testcase} testcase</p>
        </div>
        {problem.lesson_id !== null && problem.course_id && (
          <Button asChild variant="outline"><Link href={`/teacher/courses/${problem.course_id}/sessions/${problem.lesson_id}?mode=edit`}><Pencil className="size-4" /> Chỉnh sửa bài</Link></Button>
        )}
      </header>

      <div className="grid gap-3 sm:grid-cols-3">
        <Stat icon={<Clock3 />} label="Giới hạn thời gian" value={`${problem.time_limit_seconds}s`} />
        <Stat icon={<FlaskConical />} label="Mức độ" value={levelLabel(problem.level)} />
        <Stat icon={<FileCode2 />} label="Cách chấm" value={problem.function_name ? "Function-call" : "stdin/stdout"} />
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.65fr)]">
        <article className="space-y-6 rounded-2xl border bg-card p-5 shadow-sm sm:p-6">
          <Section title="Đề bài"><p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">{problem.description}</p></Section>
          <Section title="Ràng buộc"><pre className="whitespace-pre-wrap rounded-xl bg-muted p-4 text-sm leading-6">{problem.constraints}</pre></Section>
          {problem.hint && <Section title="Gợi ý"><p className="flex gap-2 text-sm leading-6 text-slate-700"><Lightbulb className="mt-1 size-4 shrink-0 text-amber-500" />{problem.hint}</p></Section>}
          <Section title="Starter code">
            <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-xl bg-slate-950 p-4 font-mono text-xs leading-6 text-slate-100">{problem.starter_codes?.python || problem.starter_code || "Chưa có starter code."}</pre>
          </Section>
        </article>
        <section className="h-fit space-y-3 rounded-2xl border bg-card p-5 shadow-sm sm:p-6">
          <h2 className="text-lg font-semibold text-slate-900">Testcase mẫu</h2>
          {problem.testcases.filter((testcase) => testcase.is_sample).map((testcase, index) => (
            <div key={testcase.id} className="space-y-3 rounded-xl bg-muted p-4 text-sm">
              <p className="font-semibold">Test #{index + 1}</p>
              <Value label="Input" value={testcase.input} />
              <Value label="Output mong đợi" value={testcase.expected_output} />
            </div>
          ))}
        </section>
      </div>
      <AdminProblemPreview problem={problem} />
      <p className="text-xs leading-5 text-muted-foreground">Đề thư viện chỉ được xem; đề đã gắn lớp của Teacher có thể chỉnh sửa trong lớp do mình phụ trách. Teacher được chạy testcase và nhận gợi ý AI sau khi chạy thử.</p>
    </div>
  );
}

function Value({ label, value }: { label: string; value: unknown }) {
  return <div><p className="mb-1 text-xs text-muted-foreground">{label}</p><pre className="whitespace-pre-wrap rounded-lg bg-background p-2 text-xs leading-5">{typeof value === "string" ? value : JSON.stringify(value, null, 2)}</pre></div>;
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return <div className="rounded-xl border bg-card p-4 shadow-sm"><div className="mb-2 flex items-center gap-2 text-indigo-700">{icon}<span className="text-xs font-medium text-muted-foreground">{label}</span></div><p className="font-semibold text-slate-900">{value}</p></div>;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="space-y-2"><h2 className="text-lg font-semibold text-[#2f226b]">{title}</h2>{children}</section>;
}

function levelLabel(level: string) { return level === "easy" ? "Dễ" : level === "hard" ? "Khó" : "Trung bình"; }

function ProblemDetailSkeleton() {
  return <div className="space-y-6"><Skeleton className="h-6 w-48" /><Skeleton className="h-20 w-3/4 rounded-xl" /><div className="grid gap-3 sm:grid-cols-3"><Skeleton className="h-20 rounded-xl" /><Skeleton className="h-20 rounded-xl" /><Skeleton className="h-20 rounded-xl" /></div><Skeleton className="h-[520px] rounded-2xl" /></div>;
}
