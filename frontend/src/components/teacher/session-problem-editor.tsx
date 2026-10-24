"use client";

import { useState } from "react";
import { FileArchive, Plus, Save, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { deleteProblem, updateProblem, uploadProblemTestcases } from "@/lib/api/endpoints/courses";
import type { ProblemUpdateRequest, SessionExercise } from "@/lib/types/course";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface Props {
  courseId: string;
  sessionId: string;
  exercise: SessionExercise;
  onSaved: (exercise: SessionExercise) => void;
  onDeleted: () => void;
  lessonStartDate: string;
  lessonEndDate: string;
}

type Draft = Pick<SessionExercise, "title" | "description" | "constraints" | "level" | "time_limit_seconds" | "starter_code" | "function_name" | "start_datetime" | "end_datetime"> & { hint: string; complexity: string; starter_codes?: Record<string, string>; testcases: SessionExercise["testcases"] };

function toDateTimeLocal(value: string) {
  const parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Ho_Chi_Minh", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(value));
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}T${values.hour}:${values.minute}`;
}

function toDraft(exercise: SessionExercise, lessonStartDate: string, lessonEndDate: string): Draft {
  return { title: exercise.title, description: exercise.description, constraints: exercise.constraints, level: exercise.level, time_limit_seconds: exercise.time_limit_seconds, starter_code: exercise.starter_code, starter_codes: exercise.starter_codes, function_name: exercise.function_name, start_datetime: exercise.start_datetime ? toDateTimeLocal(exercise.start_datetime) : `${lessonStartDate}T00:00`, end_datetime: exercise.end_datetime ? toDateTimeLocal(exercise.end_datetime) : `${lessonEndDate}T23:59`, hint: exercise.hint ?? "", complexity: exercise.complexity ?? "", testcases: (exercise.testcases ?? []).map((testcase) => ({ ...testcase })) };
}

function parseTestcase(testcase: SessionExercise["testcases"][number], index: number) {
  let input: unknown;
  let expectedOutput: unknown;
  try { input = JSON.parse(testcase.input); } catch { throw new Error(`Testcase #${index + 1}: Input không phải JSON hợp lệ.`); }
  if (!Array.isArray(input)) throw new Error(`Testcase #${index + 1}: Input phải là một mảng JSON.`);
  try { expectedOutput = JSON.parse(testcase.expected_output); } catch { throw new Error(`Testcase #${index + 1}: Output không phải JSON hợp lệ.`); }
  return { input, expected_output: expectedOutput, is_sample: testcase.is_sample };
}

export function SessionProblemEditor({ courseId, sessionId, exercise, onSaved, onDeleted, lessonStartDate, lessonEndDate }: Props) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(exercise, lessonStartDate, lessonEndDate));
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const hasSubmissions = exercise.submitted_count > 0;

  function setField<K extends keyof Draft>(field: K, value: Draft[K]) { setDraft((current) => ({ ...current, [field]: value })); }
  function updateTestcase(index: number, field: "input" | "expected_output", value: string) {
    if (!hasSubmissions) setDraft((current) => ({ ...current, testcases: current.testcases.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item) }));
  }
  function addTestcase() { if (!hasSubmissions) setDraft((current) => ({ ...current, testcases: [...current.testcases, { id: -Date.now(), input: "[]", expected_output: "0", is_sample: false }] })); }
  function removeTestcase(index: number) { if (!hasSubmissions) setDraft((current) => ({ ...current, testcases: current.testcases.filter((_, itemIndex) => itemIndex !== index) })); }

  async function save() {
    const nextErrors: string[] = [];
    if (!draft.title.trim()) nextErrors.push("Tên bài tập không được để trống.");
    if (!draft.function_name?.trim()) nextErrors.push("Tên hàm không được để trống.");
    if (!draft.start_datetime || !draft.end_datetime || new Date(draft.start_datetime) >= new Date(draft.end_datetime)) nextErrors.push("Giờ đóng/nộp phải sau giờ mở.");
    let testcases: ProblemUpdateRequest["testcases"] = undefined;
    if (!hasSubmissions) { try { testcases = draft.testcases.map(parseTestcase); } catch (error) { nextErrors.push(error instanceof Error ? error.message : "Testcase không hợp lệ."); } }
    setErrors(nextErrors);
    if (nextErrors.length) return;
    const functionChanged = draft.function_name?.trim() !== (exercise.function_name ?? "");
    const payload: ProblemUpdateRequest = { title: draft.title.trim(), description: draft.description, constraints: draft.constraints, level: draft.level, hint: draft.hint || null, complexity: draft.complexity || null, time_limit_seconds: Number(draft.time_limit_seconds), ...(functionChanged ? { function_name: draft.function_name?.trim(), starter_codes: draft.starter_codes ?? { python: draft.starter_code, c: draft.starter_code, cpp: draft.starter_code, java: draft.starter_code } } : {}), start_datetime: `${draft.start_datetime}:00+07:00`, end_datetime: `${draft.end_datetime}:00+07:00`, starter_code: draft.starter_code, ...(hasSubmissions ? {} : { testcases }) };
    setSaving(true);
    try {
      const updated = await updateProblem(courseId, sessionId, exercise.id, payload);
      onSaved({ ...exercise, ...draft, hint: draft.hint || null, complexity: draft.complexity || null, total_number_testcase: updated.total_number_testcase, testcases: updated.testcases });
      toast.success("Đã lưu nội dung bài tập.");
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể lưu bài tập."); }
    finally { setSaving(false); }
  }

  async function importTestcases(file: File) {
    if (hasSubmissions) { toast.error("Bài đã có submission, không thể sửa testcase."); return; }
    setUploading(true);
    try {
      if (file.type === "application/json" || file.name.toLowerCase().endsWith(".json")) {
        const parsed = JSON.parse(await file.text()) as unknown;
        const items = Array.isArray(parsed) ? parsed : (parsed as { testcases?: unknown })?.testcases;
        if (!Array.isArray(items) || items.length === 0) throw new Error("File phải chứa ít nhất một testcase.");
        items.forEach((item, index) => { const value = item as { input?: unknown; expected_output?: unknown }; if (!Array.isArray(value.input)) throw new Error(`Testcase #${index + 1}: Input phải là một mảng JSON.`); if (value.expected_output === undefined) throw new Error(`Testcase #${index + 1}: Thiếu expected_output.`); });
      }
      const updated = await uploadProblemTestcases(courseId, sessionId, exercise.id, file);
      setDraft((current) => ({ ...current, testcases: updated.testcases }));
      onSaved({ ...exercise, testcases: updated.testcases, total_number_testcase: updated.total_number_testcase });
      toast.success(`Đã nhập ${updated.testcases.length} testcase.`);
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể đọc file testcase."); }
    finally { setUploading(false); }
  }

  async function removeProblem() {
    if (!window.confirm("Xóa bài tập này khỏi buổi học? Chỉ bài chưa có bài nộp mới được xóa.")) return;
    try { await deleteProblem(courseId, sessionId, exercise.id); onDeleted(); toast.success("Đã xóa bài tập."); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Không thể xóa bài tập."); }
  }

  return <section className="space-y-4 rounded-xl border bg-card p-4 shadow-sm">
    <div className="flex items-center justify-between"><div><h2 className="font-bold text-[#2f226b]">SOẠN THẢO BÀI {exercise.order}</h2><p className="text-xs text-muted-foreground">Chỉnh nội dung theo dữ liệu bài tập đang chọn.</p></div><div className="flex gap-2"><Button variant="outline" onClick={() => void removeProblem()} className="text-red-600"><Trash2 className="size-4" /> Xóa bài</Button><Button onClick={() => void save()} disabled={saving} className="bg-[#2f226b] text-white"><Save className="size-4" /> {saving ? "Đang lưu..." : "Lưu bài tập"}</Button></div></div>
    {errors.length > 0 && <div role="alert" className="space-y-1 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{errors.map((error) => <p key={error}>{error}</p>)}</div>}
    <label className="block space-y-1 text-xs font-semibold">Tên bài tập<Input value={draft.title} onChange={(event) => setField("title", event.target.value)} className="bg-indigo-50/70" /></label>
    <label className="block space-y-1 text-xs font-semibold">Tên hàm<Input value={draft.function_name ?? ""} onChange={(event) => setField("function_name", event.target.value)} className="bg-indigo-50/70" /><span className="font-normal text-muted-foreground">Tên hàm được runner dùng để chấm bài.</span></label>
    <div className="grid gap-3 sm:grid-cols-3"><label className="space-y-1 text-xs font-semibold">Mức độ<select value={draft.level} onChange={(event) => setField("level", event.target.value as Draft["level"])} className="mt-1 h-9 w-full rounded-lg border bg-indigo-50/70 px-2 text-sm"><option value="easy">Dễ</option><option value="medium">Trung bình</option><option value="hard">Khó</option></select></label><label className="space-y-1 text-xs font-semibold">Giới hạn thời gian (giây)<Input disabled={hasSubmissions} type="number" value={draft.time_limit_seconds} onChange={(event) => setField("time_limit_seconds", Number(event.target.value))} className="bg-indigo-50/70" /></label><div className="space-y-1 text-xs font-semibold"><span>Điểm tối đa</span><div className="flex h-9 items-center rounded-lg bg-indigo-50/70 px-3 text-sm text-muted-foreground">Theo testcase</div></div></div>
    <div className="grid gap-3 sm:grid-cols-2"><label className="space-y-1 text-xs font-semibold">Mở bài<Input disabled={hasSubmissions} type="datetime-local" value={draft.start_datetime} onChange={(event) => setField("start_datetime", event.target.value)} className="bg-indigo-50/70" /></label><label className="space-y-1 text-xs font-semibold">Đóng/nộp bài<Input type="datetime-local" value={draft.end_datetime} onChange={(event) => setField("end_datetime", event.target.value)} className="bg-indigo-50/70" /></label></div>
    <label className="block space-y-1 text-xs font-semibold">Mô tả bài<Textarea value={draft.description} onChange={(event) => setField("description", event.target.value)} className="min-h-40 bg-indigo-50/70" /></label>
    <div className="grid gap-3 md:grid-cols-3"><label className="space-y-1 text-xs font-semibold">Ràng buộc<textarea value={draft.constraints} onChange={(event) => setField("constraints", event.target.value)} className="mt-1 min-h-24 w-full rounded-lg border bg-indigo-50/70 p-2 text-sm" /></label><label className="space-y-1 text-xs font-semibold">Gợi ý thuật toán<textarea value={draft.hint} onChange={(event) => setField("hint", event.target.value)} className="mt-1 min-h-24 w-full rounded-lg border bg-indigo-50/70 p-2 text-sm" /></label><label className="space-y-1 text-xs font-semibold">Độ phức tạp<textarea value={draft.complexity} onChange={(event) => setField("complexity", event.target.value)} className="mt-1 min-h-24 w-full rounded-lg border bg-indigo-50/70 p-2 text-sm" /></label></div>
    <label className="block space-y-1 text-xs font-semibold">Mã nguồn khởi tạo<textarea disabled={hasSubmissions} value={draft.starter_code} onChange={(event) => setField("starter_code", event.target.value)} className="min-h-28 rounded-lg border bg-slate-900 p-3 font-mono text-xs text-white" /></label>
    {hasSubmissions && <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">Bài đã có submission: không thể sửa testcase, tên hàm, mã khởi tạo hoặc giới hạn chấm.</p>}
    <div className="space-y-3 border-t pt-4"><div className="flex items-center justify-between"><div><h3 className="font-bold text-[#2f226b]">QUẢN LÝ TEST CASE ({draft.testcases.length} TESTS)</h3><p className="text-xs text-muted-foreground">Upload file ZIP chứa JSON hoặc file JSON testcase.</p></div><div className="flex gap-2"><label className={`inline-flex cursor-pointer items-center gap-1 rounded-md border px-3 py-2 text-xs font-medium ${uploading || hasSubmissions ? "pointer-events-none opacity-60" : ""}`}><FileArchive className="size-4" /> {uploading ? "Đang đọc..." : "Chọn file ZIP/JSON"}<input disabled={uploading || hasSubmissions} type="file" accept=".zip,.json,application/zip,application/json" className="hidden" onChange={(event) => { const file = event.target.files?.[0]; if (file) void importTestcases(file); event.currentTarget.value = ""; }} /></label><Button disabled={hasSubmissions} variant="outline" size="sm" onClick={addTestcase}><Plus className="size-4" /> Thêm testcase</Button></div></div><div className="rounded-lg border-2 border-dashed border-indigo-200 bg-indigo-50 p-5 text-center text-xs text-muted-foreground" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); const file = event.dataTransfer.files[0]; if (file && !hasSubmissions) void importTestcases(file); }}><FileArchive className="mx-auto mb-2 size-6 text-indigo-700" /><p className="font-semibold text-indigo-900">Kéo thả file ZIP vào đây hoặc chọn file JSON</p><p>File JSON có thể là mảng testcase hoặc object có thuộc tính <code>testcases</code>.</p></div><div className="overflow-x-auto rounded-lg border"><table className="w-full min-w-[680px] text-xs"><thead className="bg-indigo-50 text-left"><tr><th className="px-3 py-2">Test #</th><th className="px-3 py-2">Input mẫu</th><th className="px-3 py-2">Output mong đợi</th><th className="px-3 py-2">Thao tác</th></tr></thead><tbody>{draft.testcases.map((testcase, index) => <tr key={testcase.id} className="border-t"><td className="px-3 py-2 font-semibold">#{index + 1}</td><td className="px-3 py-2"><Textarea disabled={hasSubmissions} rows={3} value={testcase.input} onChange={(event) => updateTestcase(index, "input", event.target.value)} className="min-w-48 resize-y whitespace-pre font-mono" /></td><td className="px-3 py-2"><Textarea disabled={hasSubmissions} rows={3} value={testcase.expected_output} onChange={(event) => updateTestcase(index, "expected_output", event.target.value)} className="min-w-48 resize-y whitespace-pre font-mono" /></td><td className="px-3 py-2"><Button disabled={hasSubmissions} variant="ghost" size="icon" onClick={() => removeTestcase(index)} title="Xóa testcase"><Trash2 className="size-4" /></Button></td></tr>)}</tbody></table></div></div>
  </section>;
}
