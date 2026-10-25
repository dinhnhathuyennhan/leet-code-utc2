import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { JudgeKind, PendingSubmission } from "@/lib/types/dashboard";
import { cn } from "@/lib/utils";

const JUDGE_STYLES: Record<JudgeKind, string> = {
  accepted: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300",
  graded: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300",
  pending: "bg-slate-100 text-slate-700 dark:bg-slate-500/20 dark:text-slate-300",
  wrong_answer: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300",
  similarity: "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300",
  compile_error: "bg-sky-100 text-sky-700 dark:bg-sky-500/20 dark:text-sky-300",
};

const ACTIONS: Record<JudgeKind, { label: string; className: string }> = {
  accepted: { label: "Xem lại", className: "bg-emerald-100 text-emerald-700 hover:bg-emerald-200" },
  graded: { label: "Xem lại", className: "bg-emerald-100 text-emerald-700 hover:bg-emerald-200" },
  pending: { label: "Chấm ngay", className: "bg-[#2f226b] text-white hover:bg-[#251b56]" },
  wrong_answer: { label: "Chấm ngay", className: "bg-[#2f226b] text-white hover:bg-[#251b56]" },
  similarity: { label: "So sánh", className: "bg-[#2f226b] text-white hover:bg-[#251b56]" },
  compile_error: { label: "Chấm ngay", className: "bg-[#2f226b] text-white hover:bg-[#251b56]" },
};

type SubmissionMeta = { status: string; manualScore: number | null };

function displayStatus(row: PendingSubmission, meta?: SubmissionMeta) {
  if (meta?.status === "accepted") return { kind: "graded" as const, label: "Đã chấp nhận" };
  if (meta?.status === "pending") return { kind: "pending" as const, label: "Đang chờ" };
  if (meta?.status === "compile_error") return { kind: "compile_error" as const, label: "Lỗi biên dịch" };
  if (meta?.status === "wrong_answer") return { kind: "wrong_answer" as const, label: "Sai kết quả" };
  if (row.judge_kind === "graded") return { kind: "graded" as const, label: "Đã chấp nhận" };
  return { kind: row.judge_kind, label: row.judge_label };
}

export function PendingSubmissionsTable({ rows, scores = {}, metadata = {}, returnTo }: { rows: PendingSubmission[]; scores?: Record<number, number | null>; metadata?: Record<number, SubmissionMeta>; returnTo?: string }) {
  const hasScores = Object.keys(scores).length > 0;
  const hasMetadata = Object.keys(metadata).length > 0;
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table className="min-w-[44rem]">
        <TableHeader>
          <TableRow className="bg-[#2f226b] hover:bg-[#2f226b]">
            {["Sinh viên", "Lớp / Buổi", "Trạng thái judger", "Vấn đề cần xử lý", ...(hasScores ? ["Điểm"] : []), ...(hasMetadata ? ["Đã chấm lại"] : []), "Thao tác"].map((title) => (
              <TableHead key={title} className={cn("h-12 font-semibold text-white", ["Điểm", "Đã chấm lại", "Thao tác"].includes(title) && "text-center")}>
                {title}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => {
            const meta = metadata[row.id];
            const status = displayStatus(row, meta);
            const action = ACTIONS[status.kind];
            return (
              <TableRow key={row.id}>
                <TableCell className="py-3">
                  <p className="font-semibold">{row.student_name}</p>
                  <p className="font-mono text-xs text-muted-foreground">{row.student_code}</p>
                </TableCell>
                <TableCell>
                  <p className="text-sm">
                    <span className="font-semibold text-indigo-900 dark:text-indigo-300">{row.course_code}</span> - {row.session_label}
                  </p>
                  <p className="text-xs text-muted-foreground">{row.topic}</p>
                </TableCell>
                <TableCell>
                  <span className={cn("inline-block rounded-md px-2.5 py-1 text-xs font-medium", JUDGE_STYLES[status.kind])}>
                    {status.label}
                  </span>
                </TableCell>
                <TableCell className="text-sm text-red-600 dark:text-red-400">{row.issue}</TableCell>
                {hasScores && <TableCell className="text-center font-semibold">{scores[row.id] == null ? "—" : scores[row.id]!.toFixed(1)}</TableCell>}
                {hasMetadata && <TableCell className="text-center">{meta?.manualScore != null ? <span className="font-semibold text-emerald-700">Có</span> : <span className="text-muted-foreground">Chưa</span>}</TableCell>}
                <TableCell className="text-center">
                  <Button asChild size="sm" className={cn("min-w-24", action.className)}>
                    <Link href={`/teacher/submissions/${row.id}${returnTo ? `?returnTo=${encodeURIComponent(returnTo)}` : ""}`}>{action.label}</Link>
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
