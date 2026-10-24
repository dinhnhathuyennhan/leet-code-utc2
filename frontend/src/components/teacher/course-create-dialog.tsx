"use client";
import { useRef, useState, type ReactNode } from "react";
import { Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { createCourse } from "@/lib/api/endpoints/courses";
import { fromDateInput } from "@/lib/helpers/datetime";
import { ApiError } from "@/lib/api/error";

const COVERS = [["python", "/images/background-python1.jpg"], ["javascript", "/images/background-js1.jpg"], ["java", "/images/background-java1.jpg"], ["c", "/images/background-c.jpg"], ["cpp", "/images/background-c++.jpg"]] as const;
const EMPTY_FORM = { course_id: "", course_name: "", term: "HK1 2026-2027", start_date: "", end_date: "", genre: "python" };
type Form = typeof EMPTY_FORM;
type FieldName = keyof Form;
type Errors = Partial<Record<FieldName, string>>;

function validate(form: Form): Errors {
  const errors: Errors = {};
  if (!form.course_id.trim()) errors.course_id = "Vui lòng nhập mã khóa học.";
  else if (form.course_id.trim().length > 50) errors.course_id = "Mã khóa học không được dài quá 50 ký tự.";
  if (!form.course_name.trim()) errors.course_name = "Vui lòng nhập tên khóa học.";
  else if (form.course_name.trim().length > 255) errors.course_name = "Tên khóa học không được dài quá 255 ký tự.";
  if (!form.term.trim()) errors.term = "Vui lòng nhập học kỳ / năm học.";
  if (!form.start_date) errors.start_date = "Vui lòng chọn ngày bắt đầu.";
  if (!form.end_date) errors.end_date = "Vui lòng chọn ngày kết thúc.";
  if (form.start_date && form.end_date && form.start_date >= form.end_date) errors.end_date = "Ngày kết thúc phải sau ngày bắt đầu.";
  return errors;
}

export function CourseCreateDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<Form>(EMPTY_FORM);
  const [errors, setErrors] = useState<Errors>({});
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const set = (key: FieldName, value: string) => { setForm((current) => ({ ...current, [key]: value })); setErrors((current) => ({ ...current, [key]: undefined, ...(key === "start_date" ? { end_date: undefined } : {}) })); };
  const reset = () => { setForm(EMPTY_FORM); setErrors({}); };
  const close = (nextOpen: boolean) => { if (!nextOpen && !savingRef.current) reset(); if (nextOpen) setErrors({}); setOpen(nextOpen); };

  async function submit() {
    if (savingRef.current) return;
    const nextErrors = validate(form); setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    savingRef.current = true; setSaving(true);
    try {
      await createCourse({ course_id: form.course_id.trim(), course_name: form.course_name.trim(), term: form.term.trim(), avt_link: COVERS.find(([key]) => key === form.genre)?.[1] ?? COVERS[0][1], start_date: fromDateInput(form.start_date), end_date: fromDateInput(form.end_date, "23:59:59") });
      toast.success("Đã tạo khóa học."); reset(); setOpen(false); onCreated();
    } catch (error) { toast.error(error instanceof ApiError && error.isNetworkError ? "Mất kết nối, biểu mẫu vẫn được giữ nguyên." : error instanceof Error ? error.message : "Không thể tạo khóa học."); }
    finally { savingRef.current = false; setSaving(false); }
  }
  const props = (key: FieldName) => ({ "aria-invalid": Boolean(errors[key]), "aria-describedby": errors[key] ? `${key}-error` : undefined });
  return <Dialog open={open} onOpenChange={close}><DialogTrigger render={<Button className="bg-[#2f226b] text-white"><Plus className="size-4" /> Tạo khóa học</Button>} /><DialogContent className="max-w-2xl"><DialogHeader><DialogTitle>Tạo khóa học mới</DialogTitle><DialogDescription>Nhập thông tin lớp và chọn thể loại ngôn ngữ.</DialogDescription></DialogHeader><div className="grid gap-4 sm:grid-cols-2">
    <Field name="course_id" label="Mã khóa học" error={errors.course_id}><Input {...props("course_id")} maxLength={50} value={form.course_id} onChange={(e) => set("course_id", e.target.value)} placeholder="PY101" /></Field>
    <Field name="course_name" label="Tên khóa học" error={errors.course_name}><Input {...props("course_name")} maxLength={255} value={form.course_name} onChange={(e) => set("course_name", e.target.value)} placeholder="Lập trình Python" /></Field>
    <Field name="term" label="Học kỳ / năm học" error={errors.term}><Input {...props("term")} value={form.term} onChange={(e) => set("term", e.target.value)} /></Field>
    <Field name="genre" label="Thể loại" error={errors.genre}><select {...props("genre")} value={form.genre} onChange={(e) => set("genre", e.target.value)} className="h-10 w-full rounded-md border bg-background px-3">{COVERS.map(([key]) => <option key={key} value={key}>{key.toUpperCase()}</option>)}</select></Field>
    <Field name="start_date" label="Ngày bắt đầu" error={errors.start_date}><Input {...props("start_date")} type="date" value={form.start_date} onChange={(e) => set("start_date", e.target.value)} /></Field>
    <Field name="end_date" label="Ngày kết thúc" error={errors.end_date}><Input {...props("end_date")} type="date" value={form.end_date} onChange={(e) => set("end_date", e.target.value)} /></Field>
  </div><div className="flex justify-end gap-2"><Button variant="outline" disabled={saving} onClick={() => close(false)}>Hủy</Button><Button disabled={saving} onClick={() => void submit()} className="bg-[#2f226b] text-white">{saving && <Loader2 className="size-4 animate-spin" />}{saving ? "Đang tạo..." : "Tạo khóa học"}</Button></div></DialogContent></Dialog>;
}
function Field({ name, label, error, children }: { name: string; label: string; error?: string; children: ReactNode }) { return <label className="text-sm font-semibold">{label}<div className="mt-1">{children}</div>{error && <p id={`${name}-error`} className="mt-1 text-xs font-normal text-red-600">{error}</p>}</label>; }
