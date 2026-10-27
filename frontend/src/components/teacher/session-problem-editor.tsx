"use client";

import { useRef, useState } from "react";
import { Download, FileArchive, Plus, Save, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { deleteProblem, updateProblem } from "@/lib/api/endpoints/courses";
import { downloadTestcases, previewTestcases } from "@/lib/api/endpoints/testcases";
import type { ProblemUpdateRequest, SessionExercise } from "@/lib/types/course";
import { displayInput, displayOutput, parseDraftTestcases, readTestcaseFile, type DraftTestcase, type TestcaseValidationErrors } from "@/lib/helpers/testcases";
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

type Draft = Pick<SessionExercise, "title" | "description" | "constraints" | "level" | "time_limit_seconds" | "starter_code" | "function_name" | "start_datetime" | "end_datetime"> & {
  hint: string;
  complexity: string;
  starter_codes?: Record<string, string>;
  testcases: DraftTestcase[];
};

function toDateTimeLocal(value: string) {
  const parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Ho_Chi_Minh", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(value));
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}T${values.hour}:${values.minute}`;
}

function toDraft(exercise: SessionExercise, lessonStartDate: string, lessonEndDate: string): Draft {
  return {
    title: exercise.title,
    description: exercise.description,
    constraints: exercise.constraints,
    level: exercise.level,
    time_limit_seconds: exercise.time_limit_seconds,
    starter_code: exercise.starter_code,
    starter_codes: exercise.starter_codes,
    function_name: exercise.function_name,
    start_datetime: exercise.start_datetime ? toDateTimeLocal(exercise.start_datetime) : `${lessonStartDate}T00:00`,
    end_datetime: exercise.end_datetime ? toDateTimeLocal(exercise.end_datetime) : `${lessonEndDate}T23:59`,
    hint: exercise.hint ?? "",
    complexity: exercise.complexity ?? "",
    testcases: (exercise.testcases ?? []).map((testcase) => ({ id: testcase.id, input: displayInput(testcase.input), expected_output: displayOutput(testcase.expected_output), is_sample: testcase.is_sample, inputValue: Array.isArray(testcase.input) ? testcase.input : undefined, outputValue: testcase.expected_output })),
  };
}

export function SessionProblemEditor({ courseId, sessionId, exercise, onSaved, onDeleted, lessonStartDate, lessonEndDate }: Props) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(exercise, lessonStartDate, lessonEndDate));
  const [saving, setSaving] = useState(false);
  const [readingFile, setReadingFile] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [testcaseErrors, setTestcaseErrors] = useState<TestcaseValidationErrors>({});
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [importPreview, setImportPreview] = useState<{ items: DraftTestcase[]; errors: string[]; warnings: string[] } | null>(null);
  const inputRefs = useRef<Record<number, HTMLTextAreaElement | null>>({});
  const outputRefs = useRef<Record<number, HTMLTextAreaElement | null>>({});
  const hasSubmissions = exercise.submitted_count > 0;

  function setField<K extends keyof Draft>(field: K, value: Draft[K]) { setDraft((current) => ({ ...current, [field]: value })); }

  function updateTestcase(index: number, field: "input" | "expected_output", value: string) {
    if (hasSubmissions) return;
    setDraft((current) => ({ ...current, testcases: current.testcases.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value, ...(field === "input" ? { inputValue: undefined } : { outputValue: undefined }) } : item) }));
    setTestcaseErrors((current) => ({ ...current, [index]: { ...current[index], [field === "input" ? "input" : "output"]: undefined } }));
  }

  function addTestcase() {
    if (hasSubmissions) return;
    setDraft((current) => ({ ...current, testcases: [...current.testcases, { id: -Date.now(), input: "[]", expected_output: "0", is_sample: false }] }));
  }

  function removeTestcase(index: number) {
    if (hasSubmissions) return;
    setDraft((current) => current.testcases.length === 1
      ? { ...current, testcases: [{ ...current.testcases[0], input: "", expected_output: "" }] }
      : { ...current, testcases: current.testcases.filter((_, itemIndex) => itemIndex !== index) });
    setSelectedIds((current) => current.filter((id) => id !== draft.testcases[index]?.id));
    if (draft.testcases.length === 1) setTestcaseErrors({ 0: { input: "Không thể để bài tập không có testcase. Hãy nhập lại testcase hoặc thêm testcase mới." } });
  }

  function setSelectedSample(value: boolean) {
    if (hasSubmissions || !selectedIds.length) return;
    setDraft((current) => ({ ...current, testcases: current.testcases.map((item) => selectedIds.includes(item.id) ? { ...item, is_sample: value } : item) }));
    setSelectedIds([]);
  }

  function focusFirstTestcaseError(nextErrors: TestcaseValidationErrors) {
    const index = Number(Object.keys(nextErrors)[0]);
    if (!Number.isFinite(index)) return;
    window.setTimeout(() => (nextErrors[index]?.input ? inputRefs.current[index] : outputRefs.current[index])?.focus(), 0);
  }

  async function save() {
    const nextErrors: string[] = [];
    if (!draft.title.trim()) nextErrors.push("Tên bài tập không được để trống.");
    // Bài cũ chưa từng khai báo tên hàm vẫn phải sửa được nội dung; chỉ chặn việc xoá trắng tên hàm đã có.
    if (exercise.function_name?.trim() && !draft.function_name?.trim()) nextErrors.push("Tên hàm không được để trống.");
    if (!draft.start_datetime || !draft.end_datetime || new Date(draft.start_datetime) >= new Date(draft.end_datetime)) nextErrors.push("Giờ đóng/nộp phải sau giờ mở.");
    let testcases: ProblemUpdateRequest["testcases"];
    if (!hasSubmissions) {
      const validation = parseDraftTestcases(draft.testcases);
      setTestcaseErrors(validation.errors);
      if (Object.keys(validation.errors).length) { setErrors(["Vui lòng sửa các testcase đang báo lỗi trước khi lưu bài tập."]); focusFirstTestcaseError(validation.errors); return; }
      testcases = validation.parsed;
    }
    setErrors(nextErrors);
    if (nextErrors.length) return;
    const functionChanged = draft.function_name?.trim() !== (exercise.function_name ?? "");
    // Backend bắt starter_codes phải đủ 4 ngôn ngữ, nên bù những ngôn ngữ còn thiếu bằng mã đang có.
    const starterCodes = { python: draft.starter_code, c: draft.starter_code, cpp: draft.starter_code, java: draft.starter_code, ...(draft.starter_codes ?? {}) };
    const payload: ProblemUpdateRequest = {
      title: draft.title.trim(), description: draft.description, constraints: draft.constraints, level: draft.level,
      hint: draft.hint || null, complexity: draft.complexity || null,
      start_datetime: `${draft.start_datetime}:00+07:00`, end_datetime: `${draft.end_datetime}:00+07:00`,
      // Các trường ảnh hưởng tới việc chấm chỉ được gửi khi bài chưa có bài nộp.
      ...(hasSubmissions ? {} : {
        time_limit_seconds: Number(draft.time_limit_seconds),
        starter_code: draft.starter_code,
        testcases,
        ...(functionChanged ? { function_name: draft.function_name?.trim(), starter_codes: starterCodes } : {}),
      }),
    };
    setSaving(true);
    try {
      const updated = await updateProblem(courseId, sessionId, exercise.id, payload);
      onSaved({ ...exercise, ...draft, hint: draft.hint || null, complexity: draft.complexity || null, total_number_testcase: updated.total_number_testcase, testcases: updated.testcases });
      setImportPreview(null);
      toast.success("Đã lưu nội dung bài tập.");
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể lưu bài tập."); }
    finally { setSaving(false); }
  }

  async function importTestcases(file: File) {
    if (hasSubmissions) { toast.error("Bài đã có bài nộp nên không thể nhập hoặc sửa testcase."); return; }
    setReadingFile(true);
    try {
      const result = await readTestcaseFile(file);
      if (result.errors.length) { setImportPreview({ items: result.items, errors: result.errors, warnings: [] }); return; }
      const remote = await previewTestcases({ courseId, lessonId: sessionId, problemId: exercise.id }, result.raw);
      const remoteErrors = remote.errors.map((item) => `Dòng ${item.index}, field testcase: ${item.message}`);
      const preview = { items: result.items, errors: remoteErrors, warnings: remote.warnings.map((item) => item.message) };
      setImportPreview(preview);
      if (!preview.errors.length && remote.valid) {
        setDraft((current) => ({ ...current, testcases: result.items }));
        setTestcaseErrors({});
        toast.success("Đã nạp testcase vào bản nháp. Hãy bấm Lưu bài tập để cập nhật database.");
      }
    } catch (error) { setImportPreview({ items: [], errors: [error instanceof Error ? error.message : "Không thể kiểm tra file testcase."], warnings: [] }); }
    finally { setReadingFile(false); }
  }

  async function exportTestcases(format: "json" | "zip") {
    if (!window.confirm("File export bao gồm cả testcase ẩn. Hãy chắc chắn bạn không chia sẻ file này cho người không có quyền.")) return;
    try {
      const blob = await downloadTestcases({ courseId, lessonId: sessionId, problemId: exercise.id }, format);
      const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = `testcases_${exercise.id}.${format}`; anchor.click(); URL.revokeObjectURL(url);
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể tải testcase."); }
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
    <label className="block space-y-1 text-xs font-semibold">Tên hàm<Input disabled={hasSubmissions} value={draft.function_name ?? ""} onChange={(event) => setField("function_name", event.target.value)} className="bg-indigo-50/70" /><span className="font-normal text-muted-foreground">Tên hàm được runner dùng để chấm bài.</span></label>
    <div className="grid gap-3 sm:grid-cols-3"><label className="space-y-1 text-xs font-semibold">Mức độ<select value={draft.level} onChange={(event) => setField("level", event.target.value as Draft["level"])} className="mt-1 h-9 w-full rounded-lg border bg-indigo-50/70 px-2 text-sm"><option value="easy">Dễ</option><option value="medium">Trung bình</option><option value="hard">Khó</option></select></label><label className="space-y-1 text-xs font-semibold">Giới hạn thời gian (giây)<Input disabled={hasSubmissions} type="number" value={draft.time_limit_seconds} onChange={(event) => setField("time_limit_seconds", Number(event.target.value))} className="bg-indigo-50/70" /></label><div className="space-y-1 text-xs font-semibold"><span>Điểm tối đa</span><div className="flex h-9 items-center rounded-lg bg-indigo-50/70 px-3 text-sm text-muted-foreground">Theo testcase</div></div></div>
    <div className="grid gap-3 sm:grid-cols-2"><label className="space-y-1 text-xs font-semibold">Mở bài<Input disabled={hasSubmissions} type="datetime-local" value={draft.start_datetime} onChange={(event) => setField("start_datetime", event.target.value)} className="bg-indigo-50/70" /></label><label className="space-y-1 text-xs font-semibold">Đóng/nộp bài<Input type="datetime-local" value={draft.end_datetime} onChange={(event) => setField("end_datetime", event.target.value)} className="bg-indigo-50/70" /></label></div>
    <label className="block space-y-1 text-xs font-semibold">Mô tả bài<Textarea value={draft.description} onChange={(event) => setField("description", event.target.value)} className="min-h-40 bg-indigo-50/70" /></label>
    <div className="grid gap-3 md:grid-cols-3"><label className="space-y-1 text-xs font-semibold">Ràng buộc<textarea value={draft.constraints} onChange={(event) => setField("constraints", event.target.value)} className="mt-1 min-h-24 w-full rounded-lg border bg-indigo-50/70 p-2 text-sm" /></label><label className="space-y-1 text-xs font-semibold">Gợi ý thuật toán<textarea value={draft.hint} onChange={(event) => setField("hint", event.target.value)} className="mt-1 min-h-24 w-full rounded-lg border bg-indigo-50/70 p-2 text-sm" /></label><label className="space-y-1 text-xs font-semibold">Độ phức tạp<textarea value={draft.complexity} onChange={(event) => setField("complexity", event.target.value)} className="mt-1 min-h-24 w-full rounded-lg border bg-indigo-50/70 p-2 text-sm" /></label></div>
    <label className="block space-y-1 text-xs font-semibold">Mã nguồn khởi tạo<textarea disabled={hasSubmissions} value={draft.starter_code} onChange={(event) => setField("starter_code", event.target.value)} className="min-h-[320px] w-full resize-y rounded-lg border bg-slate-900 p-4 font-mono text-sm leading-6 text-white" /></label>
    {hasSubmissions && <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">Bài đã có bài nộp: không thể thêm, sửa, xóa hoặc đánh dấu mẫu testcase; cũng không thể sửa tên hàm, mã khởi tạo hay giới hạn chấm.</p>}
    <div className="space-y-3 border-t pt-4">
      <div className="flex flex-wrap items-center justify-between gap-2"><div><h3 className="font-bold text-[#2f226b]">QUẢN LÝ TESTCASE ({draft.testcases.length} TESTS)</h3><p className="text-xs text-muted-foreground">Mọi thay đổi testcase chỉ được gửi khi bấm Lưu bài tập.</p></div><div className="flex flex-wrap gap-2"><label className={`inline-flex cursor-pointer items-center gap-1 rounded-md border px-3 py-2 text-xs font-medium ${readingFile || hasSubmissions ? "pointer-events-none opacity-60" : ""}`}><FileArchive className="size-4" /> {readingFile ? "Đang đọc..." : "Import ZIP/JSON"}<input disabled={readingFile || hasSubmissions} type="file" accept=".zip,.json,application/zip,application/json" className="hidden" onChange={(event) => { const file = event.target.files?.[0]; if (file) void importTestcases(file); event.currentTarget.value = ""; }} /></label><Button disabled={hasSubmissions} variant="outline" size="sm" onClick={addTestcase}><Plus className="size-4" /> Thêm testcase</Button><Button disabled={!draft.testcases.length} variant="outline" size="sm" onClick={() => void exportTestcases("json")}><Download className="size-4" /> Export JSON</Button><Button disabled={!draft.testcases.length} variant="outline" size="sm" onClick={() => void exportTestcases("zip")}><FileArchive className="size-4" /> Export ZIP</Button></div></div>
      <div className="rounded-lg border-2 border-dashed border-indigo-200 bg-indigo-50 p-4 text-center text-xs text-muted-foreground" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); const file = event.dataTransfer.files[0]; if (file && !hasSubmissions) void importTestcases(file); }}><FileArchive className="mx-auto mb-1 size-6 text-indigo-700" /><p className="font-semibold text-indigo-900">Kéo thả file ZIP vào đây hoặc chọn file JSON</p><p>File JSON là mảng testcase hoặc object có thuộc tính <code>testcases</code>.</p></div>
      {importPreview && <div className={`space-y-2 rounded-lg border p-3 text-xs ${importPreview.errors.length ? "border-red-200 bg-red-50 text-red-700" : "border-emerald-200 bg-emerald-50 text-emerald-800"}`}><p className="font-semibold">Preview payload import: {importPreview.items.length} testcase</p>{importPreview.errors.map((error) => <p key={error}>• {error}</p>)}{importPreview.warnings.map((warning) => <p key={warning}>• Cảnh báo: {warning}</p>)}{!importPreview.errors.length && <p>Payload hợp lệ. Danh sách đã thay thế bản nháp hiện tại; bấm Lưu bài tập để lưu database.</p>}{importPreview.items.slice(0, 5).map((item, index) => <pre key={item.id} className="overflow-x-auto rounded bg-white/70 p-2">Dòng {index + 1}: {item.input || "(trống)"} → {item.expected_output || "(trống)"} · {item.is_sample ? "mẫu" : "ẩn"}</pre>)}</div>}
      {selectedIds.length > 0 && <div className="flex flex-wrap items-center gap-2 rounded-lg bg-indigo-50 p-2 text-xs"><span>Đã chọn {selectedIds.length} testcase</span><Button disabled={hasSubmissions} size="sm" onClick={() => setSelectedSample(true)}>Đánh dấu mẫu</Button><Button disabled={hasSubmissions} size="sm" variant="outline" onClick={() => setSelectedSample(false)}>Đánh dấu ẩn</Button></div>}
      <div className="overflow-x-auto rounded-lg border"><table className="w-full min-w-[780px] text-xs"><thead className="bg-indigo-50 text-left"><tr><th className="px-3 py-2">Chọn</th><th className="px-3 py-2">Test #</th><th className="px-3 py-2">Input testcase</th><th className="px-3 py-2">Output mong đợi</th><th className="px-3 py-2">Mẫu</th><th className="px-3 py-2">Thao tác</th></tr></thead><tbody>{draft.testcases.map((testcase, index) => { const fieldError = testcaseErrors[index]; return <tr key={testcase.id} className="border-t align-top"><td className="px-3 py-2"><input disabled={hasSubmissions} type="checkbox" checked={selectedIds.includes(testcase.id)} onChange={(event) => setSelectedIds((current) => event.target.checked ? [...current, testcase.id] : current.filter((id) => id !== testcase.id))} aria-label={`Chọn testcase ${index + 1}`} /></td><td className="px-3 py-2 font-semibold">#{index + 1}</td><td className="px-3 py-2"><Textarea ref={(element) => { inputRefs.current[index] = element; }} aria-invalid={Boolean(fieldError?.input)} disabled={hasSubmissions} rows={3} value={testcase.input} onChange={(event) => updateTestcase(index, "input", event.target.value)} className={`min-w-48 resize-y whitespace-pre font-mono ${fieldError?.input ? "border-red-500" : ""}`} />{fieldError?.input && <p className="mt-1 text-red-600">{fieldError.input}</p>}</td><td className="px-3 py-2"><Textarea ref={(element) => { outputRefs.current[index] = element; }} aria-invalid={Boolean(fieldError?.output)} disabled={hasSubmissions} rows={3} value={testcase.expected_output} onChange={(event) => updateTestcase(index, "expected_output", event.target.value)} className={`min-w-48 resize-y whitespace-pre font-mono ${fieldError?.output ? "border-red-500" : ""}`} />{fieldError?.output && <p className="mt-1 text-red-600">{fieldError.output}</p>}</td><td className="px-3 py-2"><input disabled={hasSubmissions} type="checkbox" checked={testcase.is_sample} onChange={(event) => setDraft((current) => ({ ...current, testcases: current.testcases.map((item, itemIndex) => itemIndex === index ? { ...item, is_sample: event.target.checked } : item) }))} aria-label={`Testcase ${index + 1} là mẫu`} /></td><td className="px-3 py-2"><Button disabled={hasSubmissions} variant="ghost" size="icon" onClick={() => removeTestcase(index)} title={hasSubmissions ? "Không thể xóa vì bài đã có bài nộp" : "Xóa testcase"}><Trash2 className="size-4" /></Button></td></tr>; })}</tbody></table></div>
    </div>
  </section>;
}
