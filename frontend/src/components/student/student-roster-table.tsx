"use client";

import { Users } from "lucide-react";

import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/helpers/error-message";
import type { CourseStudent } from "@/lib/types/course";

interface StudentRosterTableProps {
  students?: CourseStudent[];
  isLoading: boolean;
  error: unknown;
  onRetry: () => void;
}

/** Bảng danh sách sinh viên cùng lớp (use-case "Xem danh sách sinh viên trong lớp"). */
export function StudentRosterTable({ students, isLoading, error, onRetry }: StudentRosterTableProps) {
  if (isLoading) return <StudentRosterSkeleton />;
  if (error) return <ErrorState error={error} onRetry={onRetry} />;
  if (!students?.length) {
    return <EmptyState icon={Users} title="Chưa có sinh viên nào" description="Danh sách sẽ hiển thị khi có sinh viên được thêm vào lớp." />;
  }

  return (
    <div className="rounded-xl border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">#</TableHead>
            <TableHead>Mã sinh viên</TableHead>
            <TableHead>Họ và tên</TableHead>
            <TableHead>Email</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students.map((student, index) => (
            <TableRow key={student.enrollment_id}>
              <TableCell className="text-muted-foreground">{index + 1}</TableCell>
              <TableCell className="font-medium">{student.student_id}</TableCell>
              <TableCell>{student.full_name || "—"}</TableCell>
              <TableCell className="text-muted-foreground">{student.email}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {error ? (
        <p className="px-3 py-2 text-xs text-red-600">{getErrorMessage(error)}</p>
      ) : null}
    </div>
  );
}

function StudentRosterSkeleton() {
  return (
    <div className="space-y-2 rounded-xl border bg-card p-3" aria-busy aria-label="Đang tải danh sách sinh viên">
      {Array.from({ length: 5 }, (_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}