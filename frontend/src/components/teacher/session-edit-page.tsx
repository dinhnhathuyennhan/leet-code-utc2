"use client";

import { useState } from "react";
import { CalendarDays, Check, Clock3, FileCode2, FlaskConical, Save, X } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

import { updateLesson } from "@/lib/api/endpoints/courses";
import type { SessionDetailData, SessionExercise } from "@/lib/types/course";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SessionProblemEditor } from "./session-problem-editor";

export function SessionEditPage({ courseId, sessionId, data }: { courseId: string; sessionId: string; data: SessionDetailData }) {
  const router = useRouter();
  const [title, setTitle] = useState(data.title);
  const [startDate, setStartDate] = useState(data.start_date);
  const [endDate, setEndDate] = useState(data.end_date);
  const [exercises, setExercises] = useState(data.exercises);
  const [selectedId, setSelectedId] = useState(data.exercises[0]?.id ?? null);
  const [saving, setSaving] = useState(false);
  const selectedExercise = exercises.find((exercise) => exercise.id === selectedId) ?? exercises[0];

  async function saveSession() {
    if (!title.trim() || !startDate || !endDate) { toast.error("Vui lòng nhập đủ thông tin buổi học."); return; }
    setSaving(true);
    try {
      // SỬA: Lưu thông tin buổi học sau khi các bài tập đã được cập nhật riêng.
      await updateLesson(courseId, Number(sessionId), { lesson_name: title.trim(), start_date: startDate, end_date: endDate, problem_ids: exercises.map((exercise) => exercise.id) });
      toast.success("Đã lưu thay đổi buổi học.");
      router.push(`/teacher/courses/${courseId}/sessions/${sessionId}`);
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể lưu buổi học."); } finally { setSaving(false); }
  }

  function replaceExercise(updated: SessionExercise) {
    // SỬA: Cập nhật card đang hiển thị sau khi API lưu bài tập thành công.
    setExercises((current) => current.map((exercise) => exercise.id === updated.id ? updated : exercise));
  }

  return <div className="space-y-5"><header className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-xl font-bold text-slate-900">Buổi {data.order}: {title} trong {data.course_name}</h1><p className="text-xs text-muted-foreground">Mở - đóng: {startDate} → {endDate} · Sĩ số nộp: <strong>{data.submitted_students}/{data.total_students} SV</strong></p></div><div className="flex gap-2"><Button variant="outline" onClick={() => router.back()}><X className="size-4" /> Hủy bỏ</Button><Button onClick={() => void saveSession()} disabled={saving} className="bg-[#2f226b] text-white"><Save className="size-4" /> {saving ? "Đang lưu..." : "Lưu buổi học"}</Button></div></header>
    <div className="grid gap-4 md:grid-cols-4"><InfoCard icon={<FileCode2 />} label="BÀI TẬP SẴN SÀNG" value={`${exercises.length} bài`} hint="Không tính assignment" /><InfoCard icon={<FlaskConical />} label="TỔNG TEST CASES" value={`${exercises.reduce((sum, item) => sum + item.total_number_testcase, 0)} test cases`} hint="Theo các bài đã chọn" /><InfoCard icon={<Clock3 />} label="ĐIỂM TỔNG BUỔI HỌC" value="Theo testcase" hint="Database chưa có cột điểm tối đa" /><InfoCard icon={<Check />} label="SỐ NGƯỜI ĐÃ CÔNG" value={`${data.submitted_students} người thực hiện`} hint={`${data.start_date} → ${data.end_date}`} /></div>
    <div className="grid gap-5 xl:grid-cols-[270px_minmax(0,1fr)]"><aside className="h-fit space-y-4 rounded-xl border bg-card p-4 shadow-sm"><h2 className="font-bold text-[#2f226b]">CẤU HÌNH BUỔI HỌC</h2><label className="block space-y-1 text-xs font-semibold">Tên buổi học<Input value={title} onChange={(event) => setTitle(event.target.value)} className="bg-indigo-50/70" /></label><div className="grid grid-cols-2 gap-2"><label className="space-y-1 text-xs font-semibold">Thời gian mở<div className="relative"><CalendarDays className="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-indigo-600" /><Input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} className="bg-indigo-50/70 pl-7" /></div></label><label className="space-y-1 text-xs font-semibold">Hạn nộp<Input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} className="bg-indigo-50/70" /></label></div><div className="rounded-lg bg-indigo-50 p-3 text-xs text-muted-foreground">Thời gian và trạng thái được lấy từ Lesson trong database.</div><div className="rounded-lg bg-red-50 p-3 text-xs leading-5 text-red-700">Các thay đổi về thời gian sẽ áp dụng cho tất cả sinh viên sau khi lưu.</div></aside>
      <main className="space-y-5"><section className="space-y-3 rounded-xl border bg-card p-4 shadow-sm"><div className="flex items-center justify-between"><div><h2 className="font-bold text-[#2f226b]">DANH SÁCH BÀI TẬP TRONG BUỔI</h2><p className="text-xs text-muted-foreground">Bấm một bài tập để chỉnh nội dung phía dưới.</p></div><span className="rounded bg-[#2f226b] px-2 py-1 text-xs text-white">Ngân hàng đề UTC2</span></div><div className="grid gap-3 sm:grid-cols-3">{exercises.map((exercise) => <button type="button" key={exercise.id} onClick={() => setSelectedId(exercise.id)} className={`rounded-lg border p-3 text-left transition ${selectedId === exercise.id ? "border-[#2f226b] bg-[#2f226b] text-white shadow-md" : "border-indigo-200 bg-indigo-50/70 text-slate-900"}`}><p className="text-[10px] opacity-70">BÀI {exercise.order}</p><p className="font-semibold">{exercise.title}</p><p className="mt-2 text-xs opacity-70">{exercise.total_number_testcase} test cases · {exercise.level}</p><span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold"><Check className="size-3" /> Đang dùng</span></button>)}</div></section>{selectedExercise ? <SessionProblemEditor key={selectedExercise.id} courseId={courseId} sessionId={sessionId} exercise={selectedExercise} onSaved={replaceExercise} /> : <section className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">Buổi học chưa có bài tập.</section>}</main>
    </div></div>;
}

function InfoCard({ icon, label, value, hint }: { icon: React.ReactNode; label: string; value: string; hint: string }) { return <div className="rounded-xl border bg-card p-4 shadow-sm"><div className="flex items-center justify-between text-indigo-700"><span className="text-[10px] font-bold tracking-wide">{label}</span>{icon}</div><p className="mt-2 text-xl font-bold text-[#2f226b]">{value}</p><p className="text-[11px] text-muted-foreground">{hint}</p></div>; }
