"use client";

import { useRef, useState, type ReactNode } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { updateCourse } from "@/lib/api/endpoints/courses";
import { fromDateInput, toDateInput } from "@/lib/helpers/datetime";
import { ApiError } from "@/lib/api/error";
import type { CourseDetail } from "@/lib/types/course";

const COVERS = [["python", "/images/background-python1.jpg"], ["javascript", "/images/background-js1.jpg"], ["java", "/images/background-java1.jpg"], ["c", "/images/background-c.jpg"], ["cpp", "/images/background-c++.jpg"]] as const;
type FieldName = "name" | "term" | "start" | "end";
type Errors = Partial<Record<FieldName, string>>;

export function CourseEditDialog({ course, open, onOpenChange, onSaved }: { course: CourseDetail; open: boolean; onOpenChange: (open: boolean) => void; onSaved: () => void }) {
  const [name, setName] = useState(course.name);
  const [term, setTerm] = useState(`HK${course.semester} ${course.academic_year}`);
  const [start, setStart] = useState(toDateInput(course.start_date));
  const [end, setEnd] = useState(toDateInput(course.end_date));
  const [genre, setGenre] = useState(course.language);
  const [errors, setErrors] = useState<Errors>({});
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const clearError = (field: FieldName) => setErrors((current) => ({ ...current, [field]: undefined, ...(field === "start" ? { end: undefined } : {}) }));
  const inputProps = (field: FieldName) => ({ "aria-invalid": Boolean(errors[field]), "aria-describedby": errors[field] ? `${field}-error` : undefined });

  async function submit() {
    if (savingRef.current) return;
    const next: Errors = {};
    if (!name.trim()) next.name = "Vui lòng nhập tên khóa học.";
    else if (name.trim().length > 255) next.name = "Tên khóa học không được dài quá 255 ký tự.";
    if (!term.trim()) next.term = "Vui lòng nhập học kỳ / năm học.";
    if (!start) next.start = "Vui lòng chọn ngày bắt đầu.";
    if (!end) next.end = "Vui lòng chọn ngày kết thúc.";
    if (start && end && start >= end) next.end = "Ngày kết thúc phải sau ngày bắt đầu.";
    setErrors(next);
    if (Object.keys(next).length) return;
    savingRef.current = true; setSaving(true);
    try {
      await updateCourse(course.code, { course_name: name.trim(), term: term.trim(), avt_link: COVERS.find(([key]) => key === genre)?.[1] ?? COVERS[0][1], start_date: fromDateInput(start), end_date: fromDateInput(end, "23:59:59") });
      toast.success("Đã cập nhật khóa học."); setErrors({}); onOpenChange(false); onSaved();
    } catch (error) {
      toast.error(error instanceof ApiError && error.isNetworkError ? "Mất kết nối, biểu mẫu vẫn được giữ nguyên." : error instanceof Error ? error.message : "Không thể cập nhật khóa học.");
    } finally { savingRef.current = false; setSaving(false); }
  }

  return <Dialog open={open} onOpenChange={(next) => { if (!next && !savingRef.current) setErrors({}); onOpenChange(next); }}><DialogContent className="max-w-2xl"><DialogHeader><DialogTitle>Chỉnh sửa lớp học phần</DialogTitle><DialogDescription>Cập nhật thông tin khóa học, thời gian và ảnh đại diện.</DialogDescription></DialogHeader><div className="grid gap-4 sm:grid-cols-2">
    <Field name="name" label="Tên khóa học" error={errors.name}><Input {...inputProps("name")} maxLength={255} value={name} onChange={(e) => { setName(e.target.value); clearError("name"); }} /></Field>
    <Field name="term" label="Học kỳ / năm học" error={errors.term}><Input {...inputProps("term")} value={term} onChange={(e) => { setTerm(e.target.value); clearError("term"); }} /></Field>
    <Field name="genre" label="Thể loại"><select value={genre} onChange={(e) => setGenre(e.target.value as typeof genre)} className="h-10 w-full rounded-md border bg-background px-3">{COVERS.map(([key]) => <option key={key} value={key}>{key.toUpperCase()}</option>)}</select></Field>
    <Field name="start" label="Ngày bắt đầu" error={errors.start}><Input {...inputProps("start")} type="date" value={start} onChange={(e) => { setStart(e.target.value); clearError("start"); }} /></Field>
    <Field name="end" label="Ngày kết thúc" error={errors.end}><Input {...inputProps("end")} type="date" value={end} onChange={(e) => { setEnd(e.target.value); clearError("end"); }} /></Field>
  </div><div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end"><Button variant="outline" disabled={saving} onClick={() => onOpenChange(false)}>Hủy</Button><Button disabled={saving} onClick={() => void submit()} className="bg-[#2f226b] text-white">{saving && <Loader2 className="size-4 animate-spin" />}{saving ? "Đang lưu..." : "Lưu thay đổi"}</Button></div></DialogContent></Dialog>;
}

function Field({ name, label, error, children }: { name: string; label: string; error?: string; children: ReactNode }) { return <label className="text-sm font-semibold">{label}<div className="mt-1">{children}</div>{error && <p id={`${name}-error`} className="mt-1 text-xs font-normal text-red-600">{error}</p>}</label>; }
