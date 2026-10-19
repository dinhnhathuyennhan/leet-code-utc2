"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Clock, Copy, FileCode2, FlaskConical, Play, Send } from "lucide-react";
import { useParams } from "next/navigation";
import { toast } from "sonner";

import { ErrorState } from "@/components/shared/page-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { getCourseById, getProblemDetail } from "@/lib/api/endpoints/courses";
import type { CourseDetail, ProblemDetailData } from "@/lib/types/course";

export default function StudentAssignmentDetailPage() {
  const { id, assignmentId } = useParams<{ id: string; assignmentId: string }>();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [problem, setProblem] = useState<ProblemDetailData | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [code, setCode] = useState("");
  const [running, setRunning] = useState(false);

  useBreadcrumbLabel(problem?.title ?? "Bài tập");

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const loadedCourse = await getCourseById(id);
        const problemId = Number(assignmentId);
        const session = loadedCourse.sessions.find((item) => item.problems.some((itemProblem) => itemProblem.id === problemId));
        if (!session) throw new Error("Không tìm thấy buổi học chứa bài tập này.");
        const loadedProblem = await getProblemDetail(id, session.id, problemId);
        if (active) {
          setCourse(loadedCourse);
          setProblem(loadedProblem);
          setCode(loadedProblem.starter_code);
        }
      } catch (requestError) {
        if (active) setError(requestError);
      }
    })();
    return () => { active = false; };
  }, [id, assignmentId]);

  if (error) return <ErrorState error={error} />;
  if (!course || !problem) return <AssignmentSkeleton />;

  const session = course.sessions.find((item) => item.id === problem.lesson_id);
  const sample = problem.testcases.filter((item) => item.is_sample);

  function runSamples() {
    setRunning(true);
    window.setTimeout(() => { setRunning(false); toast.info("Chạy thử chỉ hiển thị testcase; hệ thống judge chưa cung cấp endpoint nộp bài cho frontend."); }, 500);
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div><Link href={`/student/classes/${encodeURIComponent(id)}`} className="inline-flex items-center gap-1 text-sm text-indigo-700 hover:underline"><ArrowLeft className="size-4" /> Quay lại lớp</Link><h1 className="mt-2 text-2xl font-bold">{problem.code ?? `Bài ${problem.id}`}: {problem.title}</h1></div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground"><Badge variant="outline">{course.language}</Badge><Clock className="size-4" /> Hạn {session?.deadline ? new Date(session.deadline).toLocaleString("vi-VN") : "—"}</div>
      </header>
      <div className="grid gap-4 sm:grid-cols-4"><Stat icon={<Clock />} label="Thời gian chạy" value={`${problem.time_limit_seconds}s`} /><Stat icon={<FlaskConical />} label="Test cases" value={String(problem.total_number_testcase)} /><Stat icon={<FileCode2 />} label="Mức độ" value={problem.level} /><Stat icon={<FileCode2 />} label="Ngôn ngữ" value={course.language} /></div>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(360px,0.9fr)]">
        <article className="space-y-5 rounded-2xl border bg-card p-6"><Section title="Đề bài"><p className="whitespace-pre-wrap text-sm leading-7">{problem.description}</p></Section><Section title="Ràng buộc"><pre className="whitespace-pre-wrap rounded-lg bg-indigo-50 p-4 text-sm">{problem.constraints || "—"}</pre></Section>{problem.hint && <Section title="Gợi ý"><p className="whitespace-pre-wrap text-sm">{problem.hint}</p></Section>}<Section title="Testcase mẫu"><div className="space-y-3">{sample.length ? sample.map((testcase, index) => <div key={testcase.id} className="rounded-lg border bg-indigo-50/60 p-3 text-sm"><strong>Test #{index + 1}</strong><pre className="mt-2 whitespace-pre-wrap">Input: {testcase.input}{"\n"}Output: {testcase.expected_output}</pre></div>) : <p className="text-sm text-muted-foreground">Bài chưa có testcase mẫu.</p>}</div></Section></article>
        <section className="flex min-h-[520px] flex-col overflow-hidden rounded-2xl border bg-slate-950"><div className="flex items-center justify-between border-b border-white/10 px-4 py-3 text-xs text-slate-300"><span>Main.{course.language === "java" ? "java" : course.language}</span><button type="button" onClick={() => void navigator.clipboard?.writeText(code)} className="inline-flex items-center gap-1"><Copy className="size-3.5" /> Sao chép</button></div><textarea value={code} onChange={(event) => setCode(event.target.value)} spellCheck={false} className="min-h-0 flex-1 resize-none bg-slate-950 p-4 font-mono text-sm leading-6 text-slate-100 outline-none" /><div className="flex justify-end gap-2 border-t border-white/10 p-3"><Button variant="outline" onClick={runSamples} disabled={running}><Play className="size-4" /> {running ? "Đang chạy..." : "Chạy thử"}</Button><Button disabled title="Backend chưa cung cấp API nộp bài"><Send className="size-4" /> Nộp bài</Button></div></section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) { return <section className="space-y-2"><h2 className="font-bold text-[#2f226b]">{title}</h2>{children}</section>; }
function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) { return <div className="rounded-xl border bg-card p-4"><div className="flex items-center gap-2 text-indigo-700">{icon}<span className="text-xs text-muted-foreground">{label}</span></div><strong className="mt-2 block">{value}</strong></div>; }
function AssignmentSkeleton() { return <div className="space-y-5"><Skeleton className="h-16 w-full rounded-xl" /><div className="grid gap-4 sm:grid-cols-4">{[1, 2, 3, 4].map((item) => <Skeleton key={item} className="h-24 rounded-xl" />)}</div><Skeleton className="h-[600px] w-full rounded-2xl" /></div>; }
