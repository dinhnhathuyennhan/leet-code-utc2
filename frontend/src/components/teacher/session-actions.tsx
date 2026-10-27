"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Copy, MoreHorizontal, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { deleteLesson, duplicateLesson } from "@/lib/api/endpoints/courses";
import { formatDate } from "@/lib/helpers/format";

/** Đổi lỗi API thành câu tiếng Việt. Giả định lỗi từ wrapAxiosError có thể mang `status`. */
function toMessage(error: unknown, fallback: string) {
  const status = (error as { status?: number })?.status;
  if (status === 409) return "Buổi học còn bài tập, hãy xóa hết bài tập trước.";
  if (status === 403) return "Bạn không có quyền thực hiện thao tác này.";
  if (status === 404) return "Không tìm thấy buổi học hoặc lớp đích.";
  if (status === 422) return "Dữ liệu không hợp lệ, vui lòng kiểm tra lại ngày.";
  return fallback;
}

type Props = { courseId: string; sessionId: string; exerciseCount: number };

export function SessionActions({ courseId, sessionId, exerciseCount }: Props) {
  const router = useRouter();
  const [dialog, setDialog] = useState<"delete" | "duplicate" | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ start: "", end: "", target: "" });

  const hasExercises = exerciseCount > 0;
  const bothDates = !!form.start && !!form.end;
  const dateError = !bothDates ? "Vui lòng chọn đủ ngày" : form.start > form.end ? "Ngày mở không được sau hạn nộp" : null;

  const close = () => { if (!busy) { setDialog(null); setError(null); } };

  async function run(task: () => Promise<string>, failMsg: string) {
    setBusy(true);
    setError(null);
    try {
      const nextCourseId = await task();
      router.push(`/teacher/courses/${nextCourseId}`);
      router.refresh();
    } catch (e) {
      setError(toMessage(e, failMsg));
      setBusy(false);
    }
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="icon" className="size-10" aria-label="Thao tác khác">
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onSelect={() => setDialog("duplicate")}><Copy className="size-4" /> Nhân bản buổi học</DropdownMenuItem>
          <DropdownMenuItem className="text-red-600" onSelect={() => setDialog("delete")}><Trash2 className="size-4" /> Xóa buổi học</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Xóa */}
      <AlertDialog open={dialog === "delete"} onOpenChange={(o) => !o && close()}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{hasExercises ? "Chưa thể xóa buổi học" : "Xóa buổi học này?"}</AlertDialogTitle>
            <AlertDialogDescription>
              {hasExercises
                ? `Buổi còn ${exerciseCount} bài tập. Hãy xóa hết bài tập trước (bài đã có bài nộp không xóa được).`
                : "Hành động này không thể hoàn tác."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <AlertDialogFooter>
            <AlertDialogCancel disabled={busy}>{hasExercises ? "Đóng" : "Hủy"}</AlertDialogCancel>
            {!hasExercises && (
              <AlertDialogAction
                disabled={busy}
                className="bg-red-600 text-white hover:bg-red-700"
                onClick={() => run(async () => { await deleteLesson(courseId, sessionId); return courseId; }, "Xóa buổi học thất bại.")}
              >
                {busy ? "Đang xóa..." : "Xóa buổi học"}
              </AlertDialogAction>
            )}
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Nhân bản */}
      <Dialog open={dialog === "duplicate"} onOpenChange={(o) => !o && close()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nhân bản buổi học</DialogTitle>
            <DialogDescription>Sao chép bài tập và testcase. Bài nộp không được sao chép.</DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-2 gap-4">
            {([["start", "Ngày mở"], ["end", "Hạn nộp"]] as const).map(([key, label]) => (
              <div key={key} className="space-y-1.5">
                <Label htmlFor={`dup-${key}`}>{label}</Label>
                <Input id={`dup-${key}`} type="date" value={form[key]} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} />
                <p className="h-4 text-xs text-muted-foreground">{form[key] ? formatDate(form[key]) : ""}</p>
              </div>
            ))}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="dup-target">Lớp đích (mã lớp)</Label>
            <Input id="dup-target" maxLength={50} placeholder={`Để trống = ${courseId}`} value={form.target} onChange={(e) => setForm((f) => ({ ...f, target: e.target.value }))} />
          </div>

          {(error || (bothDates && dateError)) && <p className="text-sm text-red-600">{error ?? dateError}</p>}

          <DialogFooter>
            <Button variant="outline" disabled={busy} onClick={close}>Hủy</Button>
            <Button
              disabled={busy || !!dateError}
              onClick={() =>
                run(async () => {
                  const target = form.target.trim() || null;
                  const course = await duplicateLesson(courseId, sessionId, { new_start_date: form.start, new_end_date: form.end, target_course_id: target });
                  return course.code || target || courseId;
                }, "Nhân bản thất bại.")
              }
            >
              {busy ? "Đang nhân bản..." : "Nhân bản"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}