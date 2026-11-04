"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, Code2, Copy, FileCheck2, Save } from "lucide-react";
import { toast } from "sonner";
import { useBreadcrumbLabels } from "@/components/shared/breadcrumb-context";
import { ErrorState } from "@/components/shared/page-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getAdminSubmission, saveAdminSubmission } from "@/lib/api/endpoints/admin-management";
import { formatDeadline } from "@/lib/helpers/datetime";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { adminKeys } from "@/lib/hooks/use-admin";
import type { AdminSubmissionDetail as Submission } from "@/lib/types/admin";
import { AdminHeading, AdminLoading, AdminMetric, ADMIN_PRIMARY, ADMIN_SELECT } from "./admin-ui";

const STATUSES: Record<string, string> = {
  accepted: "Đã chấp nhận", pending: "Đang chờ chấm", wrong_answer: "Sai kết quả", compile_error: "Lỗi biên dịch",
  processing: "Đang chấm", runtime_error: "Lỗi khi chạy", time_limit_exceeded: "Quá thời gian", internal_error: "Lỗi hệ thống chấm",
};
const jsonText = (value: unknown) => typeof value === "string" ? value : JSON.stringify(value, null, 2);

export function AdminSubmissionDetail({ id }: { id: string }) {
  const query = useQuery({ queryKey: [...adminKeys.submissions, id], queryFn: () => getAdminSubmission(id) });
  useBreadcrumbLabels(null, null, `Bài nộp #${id}`);
  if (query.isPending) return <AdminLoading />;
  if (query.error || !query.data) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  return <SubmissionWorkspace key={query.dataUpdatedAt} submission={query.data} />;
}

function SubmissionWorkspace({ submission }: { submission: Submission }) {
  const client = useQueryClient();
  const [feedback, setFeedback] = useState(submission.feedback ?? "");
  const [status, setStatus] = useState(submission.status);
  const [score, setScore] = useState(submission.manual_score == null ? "" : String(submission.manual_score));
  const [saving, setSaving] = useState(false);
  const automatic = submission.total_testcases > 0 ? ((submission.passed_count / submission.total_testcases) * 10).toFixed(1) : "—";
  async function save(event: React.FormEvent) {
    event.preventDefault();
    const manualScore = score.trim() === "" ? null : Number(score);
    if (manualScore !== null && (!Number.isFinite(manualScore) || manualScore < 0 || manualScore > 10)) { toast.error("Điểm phải nằm trong khoảng 0 đến 10."); return; }
    setSaving(true);
    try {
      await saveAdminSubmission(String(submission.id), { feedback: feedback.trim(), status, manual_score: manualScore });
      await client.invalidateQueries({ queryKey: adminKeys.all });
      toast.success("Đã lưu đánh giá bài nộp.");
    } catch (error) { toast.error(getErrorMessage(error)); } finally { setSaving(false); }
  }
  async function copyCode() {
    try { await navigator.clipboard.writeText(submission.submitted_code); toast.success("Đã sao chép mã nguồn."); }
    catch { toast.error("Không thể sao chép. Hãy chọn mã nguồn và sao chép thủ công."); }
  }
  return <div className="space-y-6">
    <Link href="/admin/submissions" className="inline-flex items-center gap-2 text-sm text-indigo-700 dark:text-indigo-300"><ArrowLeft className="size-4" />Quay lại danh sách bài nộp</Link>
    <AdminHeading title={`Đánh giá bài nộp #${submission.id}`} description={`${submission.course_code} · ${submission.session_label} · ${submission.problem_title}`} />
    <div className="grid gap-4 sm:grid-cols-3">
      <AdminMetric label="Trạng thái" value={STATUSES[submission.status] ?? submission.status} icon={FileCheck2} />
      <AdminMetric label="Testcase đạt" value={`${submission.passed_count}/${submission.total_testcases}`} icon={CheckCircle2} />
      <AdminMetric label="Điểm tự động (thang 10)" value={automatic} icon={Code2} />
    </div>
    <section className="space-y-3 rounded-2xl border bg-card p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="font-bold">Đề bài</h2><span className="rounded-md bg-indigo-50 px-2 py-1 text-xs text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">{submission.problem_level}</span></div>
      <p className="whitespace-pre-wrap text-sm leading-6">{submission.problem_description}</p>
      <div className="grid gap-3 text-sm sm:grid-cols-3"><p><span className="text-muted-foreground">Hàm:</span> {submission.problem_function_name ?? "—"}</p><p><span className="text-muted-foreground">Mã đề:</span> {submission.problem_code ?? "—"}</p><p><span className="text-muted-foreground">Mã bài nộp:</span> #{submission.id}</p></div>
      <div><p className="mb-1 text-xs font-medium text-muted-foreground">Ràng buộc</p><p className="whitespace-pre-wrap text-sm">{submission.problem_constraints || "—"}</p></div>
    </section>
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(300px,1fr)]">
      <div className="min-w-0 space-y-5">
        <section className="flex flex-wrap justify-between gap-3 rounded-xl border bg-card p-5">
          <div><h2 className="font-semibold">{submission.student_name}</h2><p className="mt-1 text-sm text-muted-foreground">{submission.student_code} · {submission.class_id ?? "Chưa phân lớp"}</p></div>
          <p className="text-sm text-muted-foreground">Nộp lúc {formatDeadline(submission.submitted_datetime)} · {submission.language}</p>
        </section>
        <section className="overflow-hidden rounded-xl border bg-slate-950 text-slate-100">
          <div className="flex items-center justify-between gap-3 border-b border-slate-800 px-4 py-3"><h2 className="text-sm font-semibold">Mã nguồn bài nộp</h2><Button variant="ghost" size="sm" onClick={() => void copyCode()}><Copy className="size-4" />Sao chép</Button></div>
          <pre className="max-h-[65vh] overflow-auto p-5 font-mono text-xs leading-6"><code>{submission.submitted_code}</code></pre>
        </section>
        {submission.compile_output && <section className="rounded-xl border border-rose-200 bg-rose-50 p-5 dark:bg-rose-500/10"><h2 className="mb-3 font-semibold text-rose-700 dark:text-rose-300">Thông báo biên dịch</h2><pre className="max-h-72 overflow-auto whitespace-pre-wrap text-xs">{submission.compile_output}</pre></section>}
        <section className="space-y-3 rounded-xl border bg-card p-5">
          <h2 className="font-semibold">Dữ liệu testcase ({submission.testcases.length})</h2>
          <p className="text-xs text-muted-foreground">Kết quả tổng hợp: {submission.passed_count}/{submission.total_testcases} testcase đạt.</p>
          {submission.testcases.map((testcase, index) => <details key={testcase.id} className="rounded-lg border p-3"><summary className="cursor-pointer text-sm font-medium">Test #{index + 1} {testcase.is_sample && "· Mẫu"}</summary><div className="mt-3 grid gap-3 sm:grid-cols-2">
            <div><p className="mb-1 text-xs text-muted-foreground">Input</p><pre className="max-h-48 overflow-auto rounded bg-muted p-3 text-xs">{jsonText(testcase.input)}</pre></div>
            <div><p className="mb-1 text-xs text-muted-foreground">Kết quả mong đợi</p><pre className="max-h-48 overflow-auto rounded bg-muted p-3 text-xs">{jsonText(testcase.expected_output)}</pre></div>
          </div></details>)}
        </section>
      </div>
      <form onSubmit={(event) => void save(event)} className="h-fit space-y-5 rounded-2xl border bg-card p-5 shadow-sm">
        <h2 className="font-bold">Đánh giá & nhận xét</h2>
        <label className="block space-y-2 text-sm font-medium">Trạng thái<select value={status} onChange={(event) => setStatus(event.target.value)} className={`${ADMIN_SELECT} w-full`} disabled={saving}>{Object.entries(STATUSES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label className="block space-y-2 text-sm font-medium">Điểm chốt (0–10)<Input type="number" min={0} max={10} step="0.1" value={score} onChange={(event) => setScore(event.target.value)} placeholder={automatic} disabled={saving} /></label>
        <p className="text-xs text-muted-foreground">Để trống điểm chốt để sử dụng kết quả chấm tự động.</p>
        <label className="block space-y-2 text-sm font-medium">Nhận xét<Textarea rows={7} maxLength={10000} value={feedback} onChange={(event) => setFeedback(event.target.value)} disabled={saving} placeholder="Nhập nhận xét về bài làm..." /></label>
        <Button type="submit" disabled={saving} className={`${ADMIN_PRIMARY} w-full`}><Save className="size-4" />{saving ? "Đang lưu..." : "Lưu đánh giá"}</Button>
      </form>
    </div>
  </div>;
}
