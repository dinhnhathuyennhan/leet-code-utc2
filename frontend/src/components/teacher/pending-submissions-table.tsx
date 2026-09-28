import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { JudgeKind, PendingSubmission } from "@/lib/dashboard";
import { cn } from "@/lib/utils";

const JUDGE_STYLES: Record<JudgeKind, string> = {
  wrong_answer: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300",
  similarity: "bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300",
  compile_error: "bg-sky-100 text-sky-700 dark:bg-sky-500/20 dark:text-sky-300",
};

const ACTIONS: Record<JudgeKind, { label: string; className: string }> = {
  wrong_answer: { label: "Chấm ngay", className: "bg-indigo-950 text-white hover:bg-indigo-900" },
  similarity: { label: "So sánh", className: "bg-indigo-950 text-white hover:bg-indigo-900" },
  compile_error: { label: "Xem code", className: "bg-sky-100 text-sky-700 hover:bg-sky-200 dark:bg-sky-500/20 dark:text-sky-300" },
};

export function PendingSubmissionsTable({ rows }: { rows: PendingSubmission[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table className="min-w-[44rem]">
        <TableHeader>
          <TableRow className="bg-indigo-700 hover:bg-indigo-700">
            {["Sinh viên", "Lớp / Buổi", "Trạng thái judger", "Vấn đề cần xử lý", "Thao tác"].map((title, i) => (
              <TableHead key={title} className={cn("h-12 font-semibold text-white", i === 4 && "text-center")}>
                {title}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => {
            const action = ACTIONS[row.judge_kind];
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
                  <span className={cn("inline-block rounded-md px-2.5 py-1 text-xs font-medium", JUDGE_STYLES[row.judge_kind])}>
                    {row.judge_label}
                  </span>
                </TableCell>
                <TableCell className="text-sm text-red-600 dark:text-red-400">{row.issue}</TableCell>
                <TableCell className="text-center">
                  <Button asChild size="sm" className={cn("min-w-24", action.className)}>
                    <Link href={`/teacher/submissions/${row.id}`}>{action.label}</Link>
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
