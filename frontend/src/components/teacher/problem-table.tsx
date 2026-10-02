import Link from "next/link";

import { ActionMenu } from "@/components/teacher/action-menu";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ProblemRow } from "@/lib/types/course";

const HEAD = "h-12 text-xs font-semibold uppercase tracking-wide text-indigo-900 dark:text-indigo-200";

// TODO: menu này chưa có thiết kế — các mục tạm, chưa nối hành động.
const PROBLEM_MENU = [
  { label: "Chỉnh sửa bài tập" },
  { label: "Xem đề bài" },
  { label: "Gỡ khỏi buổi học", destructive: true },
];

export function ProblemTable({ problems, studentCount }: { problems: ProblemRow[]; studentCount: number }) {
  return (
    <div className="overflow-x-auto border-t bg-card">
      <Table className="min-w-[46rem]">
        <TableHeader>
          <TableRow className="bg-indigo-100/70 hover:bg-indigo-100/70 dark:bg-indigo-500/15">
            <TableHead className={`${HEAD} pl-5`}>Mã & tên bài tập</TableHead>
            <TableHead className={`${HEAD} text-center`}>Giới hạn (Time/Mem)</TableHead>
            <TableHead className={`${HEAD} text-center`}>Tiến độ nộp</TableHead>
            <TableHead className={`${HEAD} text-center`}>Tỷ lệ đạt</TableHead>
            <TableHead className={`${HEAD} pr-5 text-center`}>Thao tác</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {problems.map((problem) => (
            <TableRow key={problem.id}>
              <TableCell className="py-4 pl-5">
                <div className="flex items-center gap-3">
                  <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-indigo-50 text-sm font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    {problem.order}
                  </span>
                  <div className="min-w-0">
                    <p className="font-semibold">{problem.title}</p>
                    <p className="text-sm text-muted-foreground">{problem.code} · {problem.topic}</p>
                  </div>
                </div>
              </TableCell>
              <TableCell className="text-center text-sm text-muted-foreground">
                {problem.time_limit_s.toFixed(1)}s · {problem.memory_limit_mb}MB
              </TableCell>
              <TableCell className="text-center font-semibold">{problem.submitted_count}/{studentCount}</TableCell>
              <TableCell className="text-center text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                {problem.accepted_rate.toFixed(1)}% AC
              </TableCell>
              <TableCell className="pr-5">
                <div className="flex items-center justify-center gap-2">
                  <Button asChild size="sm" variant="secondary" className="bg-indigo-50 font-semibold hover:bg-indigo-100 dark:bg-slate-800">
                    <Link href={`/teacher/submissions?problem=${problem.id}`}>Xem bài nộp</Link>
                  </Button>
                  <ActionMenu label={`Thao tác bài ${problem.code}`} items={PROBLEM_MENU} className="size-8 text-slate-600" />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
