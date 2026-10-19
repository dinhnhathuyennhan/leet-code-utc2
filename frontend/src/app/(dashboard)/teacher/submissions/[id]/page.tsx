"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Code2,
  Save,
  XCircle,
} from "lucide-react";

import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { ErrorState } from "@/components/shared/page-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getSubmissionDetail, updateSubmission } from "@/lib/api/endpoints/dashboard";
import type { SubmissionDetail } from "@/lib/types/dashboard";

export default function SubmissionDetailPage() {
  const { id } = useParams<{ id: string }>();
  useBreadcrumbLabel(`Chấm bài #${id}`);

  const [data, setData] = useState<SubmissionDetail | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [feedback, setFeedback] = useState("");
  const [manualScore, setManualScore] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getSubmissionDetail(id)
      .then((submission) => {
        setData(submission);
        setFeedback(submission.feedback ?? "");
        setManualScore(submission.manual_score == null
          ? (submission.total_testcases ? ((submission.passed_count / submission.total_testcases) * 10).toFixed(1) : "0.0")
          : String(submission.manual_score));
      })
      .catch(setError);
  }, [id]);

  if (error) return <ErrorState error={error} />;
  if (!data) return <div className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">Đang tải bài nộp...</div>;

  async function saveSubmission(accept: boolean) {
    const parsedScore = Number(manualScore);
    if (!Number.isFinite(parsedScore) || parsedScore < 0 || parsedScore > 10) {
      setError(new Error("Điểm phải nằm trong khoảng 0 đến 10."));
      return;
    }
    try {
      const submission = await updateSubmission(id, {
        feedback,
        manual_score: parsedScore,

        ...(accept ? { status: "accepted" } : {}),
      });
      setData(submission);
      setSaved(true);
    } catch (requestError) {
      setError(requestError);
    }
  }

  const statusLabel = data.status === "compile_error" ? "Lỗi biên dịch" : data.status === "accepted" ? "Đã chấp nhận" : "Sai kết quả";

  return (
    <div className="space-y-6">
      {/* ─── Top Header ────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button asChild variant="outline" size="sm" className="gap-1.5 border-slate-300">
            <Link href="/teacher">
              <ArrowLeft className="size-4" /> Quay lại
            </Link>
          </Button>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-2xl">
              Chấm bài & Xử lý khiếu nại #{id}
            </h1>
            <p className="text-xs text-muted-foreground">
              Bài tập: {data.problem_code ?? data.problem_title} - {data.problem_title} · Lớp {data.course_code}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={() => void saveSubmission(false)}
            className="h-10 bg-[#2f226b] gap-2 font-semibold text-white shadow-sm hover:bg-[#251b56]"
          >
            <Save className="size-4" /> {saved ? "Đã lưu kết quả" : "Lưu điểm & Gửi phản hồi"}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_24rem]">
        {/* ─── Left column: Code viewer & Test cases ───────────────────────── */}
        <div className="space-y-6">
          {/* Sinh viên info card */}
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card p-4 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="flex size-10 items-center justify-center rounded-full bg-indigo-100 font-bold text-indigo-900 dark:bg-indigo-500/20 dark:text-indigo-200">
                {data.student_name.trim().charAt(0).toUpperCase() || "?"}
              </span>
              <div>
                <p className="font-semibold text-slate-900 dark:text-slate-100">{data.student_name}</p>
                <p className="text-xs text-muted-foreground">MSSV: {data.student_code} · Lớp {data.class_id ?? "Chưa phân lớp"}</p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs">
              <span className="flex items-center gap-1 rounded-md bg-amber-50 px-2.5 py-1 font-medium text-amber-800 dark:bg-amber-500/20 dark:text-amber-300">
                <Clock className="size-3.5" /> Nộp lúc {new Date(data.submitted_datetime).toLocaleString("vi-VN")}
              </span>
              <span className="rounded-md bg-red-100 px-2.5 py-1 font-semibold text-red-700 dark:bg-red-500/20 dark:text-red-300">
                {statusLabel}: {data.passed_count}/{data.total_testcases} Test Passed
              </span>
            </div>
          </div>

          {/* Source code viewer */}
          <div className="overflow-hidden rounded-xl border bg-slate-950 text-slate-100 shadow-md">
            <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/80 px-4 py-2.5">
              <div className="flex items-center gap-2">
                <Code2 className="size-4 text-sky-400" />
                <span className="font-mono text-xs text-slate-300">Bài nộp ({data.language})</span>
              </div>
              <span className="text-xs text-slate-400">{new Date(data.submitted_datetime).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" })}</span>
            </div>
            <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-slate-200">
              <code>{data.submitted_code}</code>
            </pre>
          </div>

          {/* Test cases execution status */}
          <div className="rounded-xl border bg-card p-5 shadow-xs">
            <h3 className="mb-3 text-sm font-bold text-slate-900 dark:text-slate-100">
              Kết quả chi tiết các Test Cases ({data.passed_count}/{data.total_testcases} Đúng)
            </h3>
            <div className="grid gap-2 sm:grid-cols-2">
              {data.testcases.map((testcase, index) => {
                const passed = index < data.passed_count;
                return <div key={testcase.id} className={`flex items-center justify-between rounded-lg border px-3 py-2 text-xs ${passed ? "bg-muted/30" : "border-red-200 bg-red-50/50 dark:bg-red-500/10"}`}>
                  <span className="font-medium">Test #{index + 1}</span>
                  <span className={`flex items-center gap-1 font-semibold ${passed ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}`}>
                    {passed ? <><CheckCircle2 className="size-3.5" /> Đúng</> : <><XCircle className="size-3.5" /> Sai kết quả</>}
                  </span>
                </div>;
              })}
            </div>
          </div>
        </div>

        {/* ─── Right column: Grading panel ─────────────────────────────────── */}
        <div className="space-y-6">
          <div className="space-y-4 rounded-xl border bg-card p-5 shadow-xs">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Đánh giá & Chấm điểm
            </h3>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Điểm số (Thang 10)
              </label>
              <Input
                type="number"
                step="0.5"
                max="10"
                min="0"
                value={manualScore}
                onChange={(event) => setManualScore(event.target.value)}
                className="mt-1 h-11 text-lg font-bold"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Lý do & Đơn xin cứu xét của sinh viên
              </label>
              <div className="mt-1 rounded-lg border bg-amber-50/70 p-3 text-xs text-amber-900 dark:bg-amber-500/10 dark:text-amber-200">
                <p className="font-semibold">Lý do nộp trễ:</p>
                <p className="mt-0.5">{data.feedback || "Sinh viên chưa gửi lý do hoặc phúc khảo."}</p>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Nhận xét của giảng viên
              </label>
              <Textarea
                rows={4}
                value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                className="mt-1 text-sm"
                placeholder="Nhập nhận xét gửi cho sinh viên..."
              />
            </div>

            <Button
              onClick={() => void saveSubmission(true)}
              className="w-full h-11 bg-[#2f226b] font-semibold text-white shadow-sm hover:bg-[#251b56]"
            >
              <Save className="size-4 mr-2" /> {saved ? "Đã lưu nhận xét" : "Lưu nhận xét"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
