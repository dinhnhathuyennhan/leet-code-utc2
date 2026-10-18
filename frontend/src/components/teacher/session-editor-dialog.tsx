"use client";

import { useMemo, useState } from "react";
import { CalendarDays, Check, Loader2, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { createLesson, updateLesson } from "@/lib/api/endpoints/courses";
import { toDateInput } from "@/lib/helpers/datetime";
import type { CourseDetail, CourseSession, LessonMutationRequest } from "@/lib/types/course";
import { toast } from "sonner";

interface SessionEditorDialogProps {
  course: CourseDetail;
  session: CourseSession | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: () => void;
}

// F4: Dùng toDateInput() thay cho slice(0, 10) để lấy đúng ngày theo giờ VN.
export function SessionEditorDialog({ course, session, open, onOpenChange, onSaved }: SessionEditorDialogProps) {
  const [title, setTitle] = useState(session?.title ?? "");
  const [startDate, setStartDate] = useState(session?.opens_at ? toDateInput(session.opens_at) : "");
  const [endDate, setEndDate] = useState(session?.deadline ? toDateInput(session.deadline) : "");
  const [selectedProblemIds, setSelectedProblemIds] = useState<number[]>(session?.problems.map((problem) => problem.id) ?? []);
  const [saving, setSaving] = useState(false);

  const availableProblems = useMemo(
    () => course.sessions.flatMap((item) => item.problems.map((problem) => ({ ...problem, sessionId: item.id }))),
    [course.sessions],
  );

  function toggleProblem(id: number) {
    setSelectedProblemIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }

  async function submit() {
    if (!title.trim() || !startDate || !endDate) {
      toast.error("Vui lòng nhập đủ tên buổi học và thời gian.");
      return;
    }
    // F5: Gửi datetime có offset +07:00 theo quy ước mới.
    const data: LessonMutationRequest = {
      lesson_name: title.trim(),
      start_date: startDate,
      end_date: endDate,
      problem_ids: selectedProblemIds,
    };
    setSaving(true);
    try {
      if (session) await updateLesson(course.code, session.id, data);
      else await createLesson(course.code, data);
      toast.success(session ? "Đã cập nhật buổi học." : "Đã tạo buổi học.");
      onOpenChange(false);
      onSaved();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Không thể lưu buổi học.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* SỬA: Mở rộng modal để form tạo buổi học có đủ không gian cho danh sách bài tập. */}
      {/* SỬA: Dùng !max-w vì DialogContent có max-w-sm mặc định và otherwise modal bị bó hẹp. */}
      <DialogContent className="!w-[min(96vw,760px)] !max-w-[760px] max-h-[calc(100dvh-1.5rem)] overflow-y-auto rounded-2xl p-0">
        <DialogHeader className="border-b bg-card px-6 py-5 text-left">
          <DialogTitle className="text-xl font-bold">{session ? "Chỉnh sửa buổi học" : "Tạo buổi học mới"}</DialogTitle>
          <DialogDescription>{course.name} — {course.code} · Học kỳ {course.semester} — {course.academic_year.replace("-", " - ")}</DialogDescription>
        </DialogHeader>

        <div className="space-y-6 px-6 py-5 sm:px-8">
          <div className="grid gap-4 sm:grid-cols-[120px_1fr]">
            <label className="space-y-2 text-sm font-semibold">Thứ tự buổi
              <Input value={session?.order ?? (course.sessions.length + 1)} disabled className="bg-slate-50 text-center" />
            </label>
            <label className="space-y-2 text-sm font-semibold">Tiêu đề buổi học <span className="text-red-500">*</span>
              <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Ví dụ: Kỹ thuật đệ quy và Quay lui" className="bg-indigo-50/60" />
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-2 text-sm font-semibold">Thời gian mở <span className="text-red-500">*</span>
              <div className="relative"><CalendarDays className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-indigo-600" /><Input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} className="bg-indigo-50/60 pl-9" /></div>
            </label>
            <label className="space-y-2 text-sm font-semibold">Hạn nộp bài <span className="text-red-500">*</span>
              <div className="relative"><CalendarDays className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-indigo-600" /><Input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} className="bg-indigo-50/60 pl-9" /></div>
            </label>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <ToggleRow label="Cho phép xem test case sau khi nộp" defaultOn />
            <ToggleRow label="Giới hạn số lần nộp bài" defaultOn={false} />
            <ToggleRow label="Không chấp nhận bài sau 23:59:00" defaultOn />
            <ToggleRow label="Cho phép sinh viên tự nhập input kiểm tra" defaultOn />
          </div>

          <section className="space-y-3">
            <div className="flex items-center justify-between"><div><h3 className="font-bold">Danh sách bài tập dự kiến <span className="rounded bg-violet-100 px-2 py-0.5 text-xs text-violet-800">{selectedProblemIds.length} bài</span></h3><p className="text-xs text-muted-foreground">Chọn bài tập từ ngân hàng hiện có.</p></div><Button variant="outline" size="sm"><Plus className="size-4" /> Thêm từ ngân hàng bài tập</Button></div>
            <div className="max-h-[30vh] space-y-2 overflow-y-auto rounded-xl bg-indigo-50/70 p-3 sm:max-h-[360px]">
              {availableProblems.length ? availableProblems.map((problem) => {
                const selected = selectedProblemIds.includes(problem.id);
                return <button type="button" key={`${problem.sessionId}-${problem.id}`} onClick={() => toggleProblem(problem.id)} className={`flex w-full items-center justify-between rounded-lg border px-3 py-3 text-left transition ${selected ? "border-indigo-300 bg-white" : "border-transparent bg-white/60 opacity-60"}`}><span><span className="mr-2 rounded bg-indigo-100 px-1.5 py-0.5 text-xs font-mono text-indigo-800">{problem.report ?? `Bài ${problem.id}`}</span><strong>{problem.title}</strong><span className="ml-2 text-xs text-muted-foreground">{problem.total_number_testcase} test cases</span></span>{selected ? <Check className="size-4 text-emerald-600" /> : <Trash2 className="size-4 text-slate-400" />}</button>;
              }) : <p className="py-6 text-center text-sm text-muted-foreground">Chưa có bài tập trong ngân hàng.</p>}
            </div>
          </section>
        </div>

        <DialogFooter className="px-6 py-4"><Button variant="outline" onClick={() => onOpenChange(false)}>Huỷ bỏ</Button><Button onClick={() => void submit()} disabled={saving} className="bg-[#2f226b] text-white hover:bg-[#251b56]"><>{saving ? <Loader2 className="animate-spin" /> : <Plus />}</> {session ? "Lưu thay đổi" : "Công bố buổi học"}</Button></DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ToggleRow({ label, defaultOn }: { label: string; defaultOn: boolean }) {
  const [on, setOn] = useState(defaultOn);
  return <button type="button" onClick={() => setOn((current) => !current)} className="flex items-center justify-between rounded-lg bg-indigo-50/70 px-3 py-2 text-left text-xs font-medium"><span>{label}</span><span className={`relative h-5 w-9 rounded-full transition ${on ? "bg-indigo-700" : "bg-slate-300"}`}><span className={`absolute top-0.5 size-4 rounded-full bg-white transition ${on ? "left-4" : "left-0.5"}`} /></span></button>;
}
