"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { createCourse } from "@/lib/api/endpoints/courses";
import { fromDateInput } from "@/lib/helpers/datetime";

const COVERS = [
  ["python", "/images/background-python1.jpg"], ["javascript", "/images/background-js1.jpg"],
  ["java", "/images/background-java1.jpg"], ["c", "/images/background-c.jpg"],
  ["cpp", "/images/background-c++.jpg"],
] as const;

export function CourseCreateDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ course_id: "", course_name: "", term: "HK1 2026-2027", start_date: "", end_date: "", genre: "python" });
  const [saving, setSaving] = useState(false);
  const set = (key: keyof typeof form, value: string) => setForm((current) => ({ ...current, [key]: value }));

  async function submit() {
    if (!form.course_id || !form.course_name || !form.start_date || !form.end_date) { toast.error("Vui lòng nhập đủ thông tin khóa học."); return; }
    if (form.start_date >= form.end_date) { toast.error("Ngày bắt đầu phải trước ngày kết thúc."); return; }
    setSaving(true);
    try {
      await createCourse({ course_id: form.course_id.trim(), course_name: form.course_name.trim(), term: form.term.trim(), avt_link: COVERS.find(([key]) => key === form.genre)?.[1] ?? COVERS[0][1], start_date: fromDateInput(form.start_date), end_date: fromDateInput(form.end_date, "23:59:59") });
      toast.success("Đã tạo khóa học."); setOpen(false); onCreated();
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể tạo khóa học."); } finally { setSaving(false); }
  }

  return <Dialog open={open} onOpenChange={setOpen}><DialogTrigger render={<Button className="bg-[#2f226b] text-white"><Plus className="size-4" /> Tạo khóa học</Button>} /><DialogContent className="max-w-2xl"><DialogHeader><DialogTitle>Tạo khóa học mới</DialogTitle><DialogDescription>Nhập thông tin lớp và chọn thể loại để gắn ảnh đại diện tương ứng.</DialogDescription></DialogHeader><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-semibold">Mã khóa học<Input value={form.course_id} onChange={(e) => set("course_id", e.target.value)} className="mt-1" placeholder="PY101" /></label><label className="text-sm font-semibold">Tên khóa học<Input value={form.course_name} onChange={(e) => set("course_name", e.target.value)} className="mt-1" placeholder="Lập trình Python" /></label><label className="text-sm font-semibold">Học kỳ / năm học<Input value={form.term} onChange={(e) => set("term", e.target.value)} className="mt-1" /></label><label className="text-sm font-semibold">Thể loại<select value={form.genre} onChange={(e) => set("genre", e.target.value)} className="mt-1 h-10 w-full rounded-md border bg-background px-3">{COVERS.map(([key]) => <option key={key} value={key}>{key.toUpperCase()}</option>)}</select></label><label className="text-sm font-semibold">Ngày bắt đầu<Input type="date" value={form.start_date} onChange={(e) => set("start_date", e.target.value)} className="mt-1" /></label><label className="text-sm font-semibold">Ngày kết thúc<Input type="date" value={form.end_date} onChange={(e) => set("end_date", e.target.value)} className="mt-1" /></label></div><div className="flex justify-end gap-2"><Button variant="outline" onClick={() => setOpen(false)}>Hủy</Button><Button disabled={saving} onClick={() => void submit()} className="bg-[#2f226b] text-white">{saving ? "Đang tạo..." : "Tạo khóa học"}</Button></div></DialogContent></Dialog>;
}
