"use client";

import { useEffect, useState } from "react";
import { Loader2, Play, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { previewAdminProblem, reviewAdminPreview } from "@/lib/api/endpoints/admin-management";
import { getErrorMessage } from "@/lib/helpers/error-message";
import type { AdminAIReview, AdminPreviewResult, AdminProblem } from "@/lib/types/admin";
import { ADMIN_PRIMARY, ADMIN_SELECT } from "./admin-ui";

const formatValue = (value: unknown) => typeof value === "string" ? value : JSON.stringify(value, null, 2) ?? "null";
const statusLabel: Record<string, string> = {
  accepted: "Đạt", wrong_answer: "Sai kết quả", compile_error: "Lỗi biên dịch", runtime_error: "Lỗi khi chạy",
  time_limit_exceeded: "Quá thời gian", internal_error: "Lỗi máy chấm",
};

function AIReviewLoading({ seconds }: { seconds: number }) {
  return <div role="status" aria-busy="true" className="overflow-hidden rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50 via-background to-sky-50 p-5 shadow-sm dark:border-indigo-500/30 dark:from-indigo-500/10 dark:to-sky-500/10 sm:p-6">
    <div className="flex items-start gap-4">
      <div className="relative flex size-12 shrink-0 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
        <span aria-hidden="true" className="absolute inset-0 rounded-2xl border border-indigo-400/50 motion-safe:animate-ping motion-reduce:hidden" />
        <Sparkles className="relative size-6" aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h4 className="font-semibold text-indigo-950 dark:text-indigo-100">AI đang phân tích lời giải</h4>
          <span aria-hidden="true" className="rounded-full bg-white/80 px-3 py-1 text-xs tabular-nums text-indigo-700 dark:bg-white/10 dark:text-indigo-200">{seconds}s</span>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{seconds < 45 ? "Đang xem xét độ phức tạp và tìm hướng cải thiện phù hợp..." : "Phân tích đang tiếp tục, vui lòng đợi thêm một chút..."}</p>
      </div>
    </div>
    <div aria-hidden="true" className="mt-6 space-y-4 rounded-xl border border-indigo-100 bg-background/80 p-4 dark:border-indigo-500/20">
      <Skeleton className="h-4 w-2/3 bg-indigo-100 motion-reduce:animate-none dark:bg-indigo-500/20" />
      <div className="grid gap-3 sm:grid-cols-2">
        <Skeleton className="h-14 rounded-lg bg-indigo-100/80 motion-reduce:animate-none dark:bg-indigo-500/15" />
        <Skeleton className="h-14 rounded-lg bg-indigo-100/80 motion-reduce:animate-none dark:bg-indigo-500/15" />
      </div>
      <Skeleton className="h-4 w-full bg-indigo-100 motion-reduce:animate-none dark:bg-indigo-500/20" />
      <Skeleton className="h-4 w-4/5 bg-indigo-100 motion-reduce:animate-none dark:bg-indigo-500/20" />
    </div>
    <span className="sr-only">Đang chờ AI review hoàn tất.</span>
  </div>;
}

export function AdminProblemPreview({ problem }: { problem: AdminProblem }) {
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(problem.starter_codes?.python || problem.starter_code || "");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AdminPreviewResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [review, setReview] = useState<AdminAIReview | null>(null);
  const [reviewBusy, setReviewBusy] = useState(false);
  const [reviewSeconds, setReviewSeconds] = useState(0);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const languages = problem.function_name ? ["python", "javascript"] : ["python", "javascript", "c", "cpp", "java"];

  useEffect(() => {
    if (!reviewBusy) return;
    const timer = window.setInterval(() => setReviewSeconds((seconds) => seconds + 1), 1000);
    return () => window.clearInterval(timer);
  }, [reviewBusy]);

  async function run(event: React.FormEvent) {
    event.preventDefault();
    if (busy || !code.trim()) return;
    setBusy(true); setResult(null); setError(null); setReview(null); setReviewError(null);
    try { setResult(await previewAdminProblem(problem.id, { language, code })); }
    catch (cause) { const message = getErrorMessage(cause); setError(message); toast.error(message); }
    finally { setBusy(false); }
  }
  async function requestReview() {
    if (reviewBusy || !result?.review_token) return;
    setReviewSeconds(0); setReviewBusy(true); setReview(null); setReviewError(null);
    try { setReview(await reviewAdminPreview(problem.id, { language, code, preview_token: result.review_token })); }
    catch (cause) { const message = getErrorMessage(cause); setReviewError(message); toast.error(message); }
    finally { setReviewBusy(false); }
  }
  return <section className="space-y-5 rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
    <div><h2 className="font-bold">Chạy thử lời giải</h2><p className="mt-1 text-sm text-muted-foreground">Chạy mã với toàn bộ testcase hiện tại, kể cả testcase ẩn. Thao tác này không tạo bài nộp hoặc thay đổi điểm sinh viên.</p></div>
    <form onSubmit={(event) => void run(event)} className="space-y-4">
      <label className="block space-y-2 text-sm font-medium">Ngôn ngữ<select className={`${ADMIN_SELECT} w-full`} value={language} disabled={busy || reviewBusy} onChange={(event) => { const next = event.target.value; setLanguage(next); setCode(problem.starter_codes?.[next] || (next === "python" ? problem.starter_code : "")); setResult(null); setReview(null); setReviewError(null); }}>
        {languages.map((item) => <option key={item} value={item}>{item === "cpp" ? "C++" : item === "javascript" ? "JavaScript" : item.toUpperCase()}</option>)}
      </select></label>
      <label className="block space-y-2 text-sm font-medium">Mã lời giải<Textarea rows={14} maxLength={65536} value={code} onChange={(event) => { setCode(event.target.value); setResult(null); setReview(null); setReviewError(null); }} disabled={busy || reviewBusy} className="font-mono text-xs" placeholder="Viết mã lời giải đầy đủ ở đây..." /></label>
      <Button type="submit" disabled={busy || !code.trim() || !problem.testcases.length} className={ADMIN_PRIMARY}><Play className="size-4" />{busy ? "Đang chấm thử..." : "Chạy tất cả testcase"}</Button>
    </form>
    {error && <p role="alert" className="text-sm text-rose-600">{error}</p>}
    {result && <div className="space-y-4" aria-live="polite">
      <p className={`rounded-lg p-3 text-sm font-semibold ${result.status === "accepted" ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300" : "bg-rose-50 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300"}`}>
        {statusLabel[result.status] ?? result.status} · {result.cases.filter((item) => item.status === "accepted").length}/{result.cases.length} testcase đạt
      </p>
      {result.compile_output && <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-rose-50 p-3 font-mono text-xs dark:bg-rose-500/10">{result.compile_output}</pre>}
      {result.cases.map((item) => <details key={item.index} className="rounded-lg border p-3"><summary className="cursor-pointer text-sm font-medium">Test #{item.index} · {statusLabel[item.status] ?? item.status}{item.time != null ? ` · ${item.time}s` : ""}</summary><div className="mt-3 grid gap-3 text-xs sm:grid-cols-3">
        <div><p className="mb-1 text-muted-foreground">Input</p><pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-muted p-3">{formatValue(item.input)}</pre></div>
        <div><p className="mb-1 text-muted-foreground">Mong đợi</p><pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-muted p-3">{formatValue(item.expected_output)}</pre></div>
        <div><p className="mb-1 text-muted-foreground">Thực tế</p><pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-muted p-3">{formatValue(item.actual_output)}</pre></div>
      </div>{item.stderr && <pre className="mt-3 overflow-auto whitespace-pre-wrap rounded bg-rose-50 p-3 text-xs dark:bg-rose-500/10">{item.stderr}</pre>}</details>)}
    </div>}
    {result?.review_token && <div className="space-y-4 border-t pt-5">
      <div><h3 className="font-semibold">AI review</h3><p className="text-sm text-muted-foreground">Đánh giá độ phức tạp và gợi ý tối ưu cho lời giải vừa được Judge0 chấm. Kết quả AI mang tính tham khảo.</p></div>
      <Button type="button" variant="outline" disabled={reviewBusy || busy || code.length > 15000} onClick={() => void requestReview()}>{reviewBusy ? <Loader2 className="size-4 motion-safe:animate-spin" /> : <Sparkles className="size-4" />}{reviewBusy ? "Đang phân tích..." : "Phân tích bằng AI"}</Button>
      {code.length > 15000 && <p className="text-sm text-amber-700">AI review hỗ trợ tối đa 15.000 ký tự mã nguồn.</p>}
      {reviewBusy && <AIReviewLoading seconds={reviewSeconds} />}
      {reviewError && <p role="alert" className="text-sm text-rose-600">{reviewError}</p>}
      {review && <div className="space-y-3 rounded-xl border bg-muted/30 p-4 text-sm" aria-live="polite">
        <p className="font-medium">{review.summary}</p>
        <p>Thời gian: <strong>{review.time_complexity}</strong> · Bộ nhớ: <strong>{review.space_complexity}</strong></p>
        <p className="whitespace-pre-wrap">{review.complexity_explanation}</p>
        {review.issues.length > 0 && <div><h4 className="font-semibold">Vấn đề cần lưu ý</h4><ul className="list-disc space-y-1 pl-5">{review.issues.map((issue, index) => <li key={index}>{issue}</li>)}</ul></div>}
        <div><h4 className="font-semibold">{review.optimization.is_optimizable ? "Hướng cải thiện độ phức tạp" : "Nhận xét về tối ưu"}</h4><p className="whitespace-pre-wrap">{review.optimization.suggestion}</p>{review.optimization.is_optimizable && <p className="mt-1 text-muted-foreground">Dự kiến sau cải thiện: thời gian {review.optimization.expected_time_complexity} · bộ nhớ {review.optimization.expected_space_complexity}</p>}</div>
      </div>}
    </div>}
  </section>;
}
