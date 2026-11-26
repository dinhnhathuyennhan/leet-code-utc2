import { useState, type ReactNode } from "react";
import { CalendarCheck, Loader2, Pencil, Plus, Trash2, UserCheck } from "lucide-react";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/helpers/format";
import { formatUpdatedAt } from "@/lib/helpers/datetime";
import type { CourseDetail } from "@/lib/types/course";

function MetaItem({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <div className="flex items-center gap-2 text-muted-foreground [&_strong]:font-semibold [&_strong]:text-foreground">
      {icon}
      <span>{children}</span>
    </div>
  );
}

interface CourseHeaderCardProps {
  course: CourseDetail;
  onCreateSession?: () => void;
  onEditCourse?: () => void;
  /** Có thì hiện nút "Xoá lớp"; ném lỗi (vd 409 đã có bài nộp) để hiện thông báo. */
  onDeleteCourse?: () => Promise<void>;
}

export function CourseHeaderCard({ course, onCreateSession, onEditCourse, onDeleteCourse }: CourseHeaderCardProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function confirmDelete() {
    if (!onDeleteCourse || deleting) return;
    setDeleting(true);
    try {
      await onDeleteCourse();
      setConfirmOpen(false);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Không thể xoá lớp học.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <section className="relative flex flex-wrap items-start justify-between gap-6 overflow-hidden rounded-2xl border bg-card p-6 pl-8 shadow-sm">
      <span aria-hidden className="absolute inset-y-6 left-0 w-1.5 rounded-r-full bg-[#2f226b]" />

      <div className="min-w-0 space-y-4">
        <h1 className="max-w-full truncate text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-3xl" title={`${course.name} — ${course.code}`}>
          {course.name} — {course.code}
        </h1>
        <div>
          <span className="inline-block rounded-md bg-[#3b2a82] px-3.5 py-1 text-sm font-medium text-white shadow-sm">
            Học kỳ {course.semester} ({course.academic_year.replace("-", " - ")})
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-x-8 gap-y-2 text-[15px]">
          <MetaItem icon={<CalendarCheck className="size-4 text-slate-500" />}>
            Ngày bắt đầu: <strong>{formatDate(course.start_date)}</strong>
          </MetaItem>
          <MetaItem icon={<CalendarCheck className="size-4 text-slate-500" />}>
            Ngày kết thúc: <strong>{formatDate(course.end_date)}</strong>
          </MetaItem>
          <MetaItem icon={<UserCheck className="size-4 text-slate-500" />}>
            Sĩ số: <strong>{course.student_count} sinh viên</strong>
          </MetaItem>
          {course.updated_at && formatUpdatedAt(course.updated_at) && <MetaItem icon={<CalendarCheck className="size-4 text-slate-500" />}>
            Cập nhật lúc: <strong>{formatUpdatedAt(course.updated_at)}</strong>
          </MetaItem>}
        </div>
      </div>

      <div className="flex w-full flex-col gap-3 sm:w-auto sm:shrink-0">
        {onCreateSession && (
          <Button
            onClick={onCreateSession}
            className="h-11 bg-[#2f226b] px-6 text-[15px] font-semibold text-white shadow-sm hover:bg-[#251b56]"
          >
            <Plus className="size-5" /> Tạo buổi học
          </Button>
        )}
        {onEditCourse && (
          <Button
            onClick={onEditCourse}
            variant="outline"
            className="h-11 border-[#2f226b] px-6 text-[15px] font-semibold text-[#2f226b] hover:bg-indigo-50 dark:border-indigo-400 dark:text-indigo-300 dark:hover:bg-slate-800"
          >
            <Pencil className="size-4" /> Chỉnh sửa lớp
          </Button>
        )}
        {onDeleteCourse && (
          <Button
            onClick={() => setConfirmOpen(true)}
            variant="outline"
            className="h-11 border-red-300 px-6 text-[15px] font-semibold text-red-600 hover:bg-red-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10"
          >
            <Trash2 className="size-4" /> Xoá lớp
          </Button>
        )}
      </div>

      <AlertDialog open={confirmOpen} onOpenChange={(open) => !deleting && setConfirmOpen(open)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xoá lớp học phần {course.code}?</AlertDialogTitle>
            <AlertDialogDescription>
              Toàn bộ buổi học, bài tập trong lớp, testcase và danh sách sinh viên của lớp sẽ bị xoá vĩnh
              viễn. Lớp đã có bài nộp của sinh viên thì không thể xoá.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Hủy</AlertDialogCancel>
            <AlertDialogAction
              disabled={deleting}
              onClick={(event) => {
                event.preventDefault();
                void confirmDelete();
              }}
            >
              {deleting && <Loader2 className="size-4 animate-spin" />} Xoá lớp
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}
