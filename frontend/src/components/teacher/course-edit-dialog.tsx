"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { updateCourse } from "@/lib/api/endpoints/courses";
import { fromDateInput, toDateInput } from "@/lib/helpers/datetime";
import type { CourseDetail } from "@/lib/types/course";

const COVERS = [["python", "/images/background-python1.jpg"], ["javascript", "/images/background-js1.jpg"], ["java", "/images/background-java1.jpg"], ["c", "/images/background-c.jpg"], ["cpp", "/images/background-c++.jpg"]] as const;

export function CourseEditDialog({ course, open, onOpenChange, onSaved }: { course: CourseDetail; open: boolean; onOpenChange: (open: boolean) => void; onSaved: () => void }) {
  const [name, setName] = useState(course.name);
  const [term, setTerm] = useState(`HK${course.semester} ${course.academic_year}`);
  const [start, setStart] = useState(toDateInput(course.start_date));
  const [end, setEnd] = useState(toDateInput(course.end_date));
  const [genre, setGenre] = useState(course.language);
  const [saving, setSaving] = useState(false);
  async function submit() {
    if (!name.trim()) { toast.error("Vui lòng nhập tên khóa học."); return; }
    if (name.trim().length > 255) { toast.error("Tên khóa học không được dài quá 255 ký tự."); return; }
    if (!term.trim()) { toast.error("Vui lòng nhập học kỳ / năm học."); return; }
    if (!start) { toast.error("Vui lòng chọn ngày bắt đầu."); return; }
    if (!end) { toast.error("Vui lòng chọn ngày kết thúc."); return; }
    if (start >= end) { toast.error("Ngày kết thúc phải sau ngày bắt đầu."); return; }
    setSaving(true);
    try { await updateCourse(course.code, { course_name: name.trim(), term: term.trim(), avt_link: COVERS.find(([key]) => key === genre)?.[1] ?? COVERS[0][1], start_date: fromDateInput(start), end_date: fromDateInput(end, "23:59:59") }); toast.success("Đã cập nhật khóa học."); onOpenChange(false); onSaved(); } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể cập nhật khóa học."); } finally { setSaving(false); }
  }
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogHeader><DialogTitle>Chỉnh sửa lớp học phần</DialogTitle><DialogDescription>Cập nhật thông tin khóa học, thời gian và ảnh đại diện.</DialogDescription></DialogHeader><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-semibold">Tên khóa học<Input maxLength={255} value={name} onChange={(e) => setName(e.target.value)} className="mt-1" /></label><label className="text-sm font-semibold">Học kỳ / năm học<Input value={term} onChange={(e) => setTerm(e.target.value)} className="mt-1" /></label><label className="text-sm font-semibold">Thể loại<select value={genre} onChange={(e) => setGenre(e.target.value as typeof genre)} className="mt-1 h-10 w-full rounded-md border bg-background px-3">{COVERS.map(([key]) => <option key={key} value={key}>{key.toUpperCase()}</option>)}</select></label><label className="text-sm font-semibold">Ngày bắt đầu<Input type="date" value={start} onChange={(e) => setStart(e.target.value)} className="mt-1" /></label><label className="text-sm font-semibold">Ngày kết thúc<Input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className="mt-1" /></label></div><div className="flex justify-end gap-2"><Button variant="outline" onClick={() => onOpenChange(false)}>Hủy</Button><Button disabled={saving} onClick={() => void submit()} className="bg-[#2f226b] text-white">{saving ? "Đang lưu..." : "Lưu thay đổi"}</Button></div></DialogContent></Dialog>;
}
