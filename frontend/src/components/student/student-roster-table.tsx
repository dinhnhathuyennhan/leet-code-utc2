"use client";

import { Users } from "lucide-react";

import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { useLocale } from "@/lib/i18n";
import type { CourseStudent } from "@/lib/types/course";

interface StudentRosterTableProps {
  students?: CourseStudent[];
  isLoading: boolean;
  error: unknown;
  onRetry: () => void;
}

/** Bảng danh sách sinh viên cùng lớp (use-case "Xem danh sách sinh viên trong lớp"). */
export function StudentRosterTable({ students, isLoading, error, onRetry }: StudentRosterTableProps) {
  const { t } = useLocale();
  if (isLoading) return <StudentRosterSkeleton />;
  if (error) return <ErrorState error={error} onRetry={onRetry} />;
  if (!students?.length) {
    return <EmptyState icon={Users} title={t("student.roster.empty")} description={t("student.roster.emptyDesc")} />;
  }

  return (
    <div className="overflow-hidden rounded-xl border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">STT</TableHead>
            <TableHead className="whitespace-nowrap">MSSV</TableHead>
            <TableHead className="min-w-32">Họ tên</TableHead>
            <TableHead className="min-w-40">{t("student.roster.col.email")}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students.map((student, index) => (
            <TableRow key={student.enrollment_id}>
              <TableCell className="text-muted-foreground">{index + 1}</TableCell>
              <TableCell className="whitespace-nowrap font-medium">{student.student_code || "—"}</TableCell>
              <TableCell className="min-w-32 break-words">{student.full_name || "—"}</TableCell>
              <TableCell className="min-w-40 break-all text-muted-foreground">{student.email}</TableCell>
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
  const { t } = useLocale();
  return (
    <div className="space-y-2 rounded-xl border bg-card p-3" aria-busy aria-label={t("student.roster.loading")}>
      {Array.from({ length: 5 }, (_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}