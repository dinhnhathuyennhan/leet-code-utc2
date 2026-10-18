"use client";

import { useState } from "react";
import { FileArchive, Plus, Save, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { updateProblem, uploadProblemTestcases } from "@/lib/api/endpoints/courses";
import type { ProblemUpdateRequest, SessionExercise } from "@/lib/types/course";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface SessionProblemEditorProps {
  courseId: string;
  sessionId: string;
  exercise: SessionExercise;
  onSaved: (exercise: SessionExercise) => void;
}

type Draft = Pick<SessionExercise, "title" | "description" | "constraints" | "level" | "time_limit_seconds" | "starter_code"> & {
  hint: string;
  complexity: string;
  testcases: SessionExercise["testcases"];
};

function toDraft(exercise: SessionExercise): Draft {
  return { title: exercise.title, description: exercise.description, constraints: exercise.constraints, level: exercise.level, time_limit_seconds: exercise.time_limit_seconds, starter_code: exercise.starter_code, hint: exercise.hint ?? "", complexity: exercise.complexity ?? "", testcases: (exercise.testcases ?? []).map((testcase) => ({ ...testcase })) };
}

export function SessionProblemEditor({ courseId, sessionId, exercise, onSaved }: SessionProblemEditorProps) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(exercise));
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  function setField<K extends keyof Draft>(field: K, value: Draft[K]) { setDraft((current) => ({ ...current, [field]: value })); }
  function updateTestcase(index: number, field: "input" | "expected_output", value: string) {
    // SỬA: Cho phép chỉnh input/output testcase ngay trong trang sửa bài tập.
    setDraft((current) => ({ ...current, testcases: current.testcases.map((testcase, testcaseIndex) => testcaseIndex === index ? { ...testcase, [field]: value } : testcase) }));
  }
  function addTestcase() { setDraft((current) => ({ ...current, testcases: [...current.testcases, { id: -Date.now(), input: "", expected_output: "", is_sample: false }] })); }
  function removeTestcase(index: number) { setDraft((current) => ({ ...current, testcases: current.testcases.filter((_, testcaseIndex) => testcaseIndex !== index) })); }

  async function save() {
    if (!draft.title.trim()) { toast.error("Tên bài tập không được để trống."); return; }
    const payload: ProblemUpdateRequest = { title: draft.title.trim(), description: draft.description, constraints: draft.constraints, level: draft.level, hint: draft.hint || null, complexity: draft.complexity || null, time_limit_seconds: Number(draft.time_limit_seconds), starter_code: draft.starter_code, testcases: draft.testcases.map(({ input, expected_output, is_sample }) => ({ input, expected_output, is_sample })) };
    setSaving(true);
    try {
      const updated = await updateProblem(courseId, sessionId, exercise.id, payload);
      // SỬA: Đồng bộ card và form sau khi backend lưu thành công.
      onSaved({ ...exercise, ...draft, hint: draft.hint || null, complexity: draft.complexity || null, total_number_testcase: updated.total_number_testcase, testcases: updated.testcases });
      toast.success("Đã lưu nội dung bài tập.");
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể lưu bài tập."); } finally { setSaving(false); }
  }

  async function importTestcases(file: File) {
    setUploading(true);
    try {
      const updated = await uploadProblemTestcases(courseId, sessionId, exercise.id, file);
      // SỬA: Hiển thị ngay các testcase backend vừa đọc từ ZIP/JSON.
      setDraft((current) => ({ ...current, testcases: updated.testcases }));
      onSaved({ ...exercise, testcases: updated.testcases, total_number_testcase: updated.total_number_testcase });
      toast.success(`Đã nhập ${updated.testcases.length} testcase.`);
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể đọc file testcase."); } finally { setUploading(false); }
  }

  return <section className="space-y-4 rounded-xl border bg-card p-4 shadow-sm"><div className="flex items-center justify-between"><div><h2 className="font-bold text-[#2f226b]">SOẠN THẢO BÀI {exercise.order}</h2><p className="text-xs text-muted-foreground">Chỉnh nội dung theo dữ liệu bài tập đang chọn.</p></div><Button onClick={() => void save()} disabled={saving} className="bg-[#2f226b] text-white"><Save className="size-4" /> {saving ? "Đang lưu..." : "Lưu bài tập"}</Button></div>
    <label className="block space-y-1 text-xs font-semibold">Tên bài tập<Input value={draft.title} onChange={(event) => setField("title", event.target.value)} className="bg-indigo-50/70" /></label>
    <div className="grid gap-3 sm:grid-cols-3"><label className="space-y-1 text-xs font-semibold">Mức độ<select value={draft.level} onChange={(event) => setField("level", event.target.value as Draft["level"])} className="mt-1 h-9 w-full rounded-lg border bg-indigo-50/70 px-2 text-sm"><option value="easy">Dễ</option><option value="medium">Trung bình</option><option value="hard">Khó</option></select></label><label className="space-y-1 text-xs font-semibold">Giới hạn thời gian (giây)<Input type="number" value={draft.time_limit_seconds} onChange={(event) => setField("time_limit_seconds", Number(event.target.value))} className="bg-indigo-50/70" /></label><div className="space-y-1 text-xs font-semibold"><span>Điểm tối đa</span><div className="flex h-9 items-center rounded-lg bg-indigo-50/70 px-3 text-sm text-muted-foreground">Theo testcase</div></div></div>
    <label className="block space-y-1 text-xs font-semibold">Mô tả bài<Textarea value={draft.description} onChange={(event) => setField("description", event.target.value)} className="min-h-40 bg-indigo-50/70" /></label>
    <div className="grid gap-3 md:grid-cols-3"><label className="space-y-1 text-xs font-semibold">Ràng buộc<textarea value={draft.constraints} onChange={(event) => setField("constraints", event.target.value)} className="mt-1 min-h-24 w-full rounded-lg border bg-indigo-50/70 p-2 text-sm" /></label><label className="space-y-1 text-xs font-semibold">Gợi ý thuật toán<textarea value={draft.hint} onChange={(event) => setField("hint", event.target.value)} className="mt-1 min-h-24 w-full rounded-lg border bg-indigo-50/70 p-2 text-sm" /></label><label className="space-y-1 text-xs font-semibold">Độ phức tạp<textarea value={draft.complexity} onChange={(event) => setField("complexity", event.target.value)} className="mt-1 min-h-24 w-full rounded-lg border bg-indigo-50/70 p-2 text-sm" /></label></div>
    <label className="block space-y-1 text-xs font-semibold">Mã nguồn khởi tạo<textarea value={draft.starter_code} onChange={(event) => setField("starter_code", event.target.value)} className="min-h-28 w-full rounded-lg border bg-slate-900 p-3 font-mono text-xs text-white" /></label>
    <div className="space-y-3 border-t pt-4"><div className="flex items-center justify-between"><div><h3 className="font-bold text-[#2f226b]">QUẢN LÝ TEST CASE ({draft.testcases.length} TESTS)</h3><p className="text-xs text-muted-foreground">Upload file ZIP chứa JSON hoặc file JSON testcase.</p></div><div className="flex gap-2"><label className={`inline-flex cursor-pointer items-center gap-1 rounded-md border px-3 py-2 text-xs font-medium ${uploading ? "pointer-events-none opacity-60" : ""}`}><FileArchive className="size-4" /> {uploading ? "Đang đọc..." : "Chọn file ZIP/JSON"}<input type="file" accept=".zip,.json,application/zip,application/json" className="hidden" onChange={(event) => { const file = event.target.files?.[0]; if (file) void importTestcases(file); event.currentTarget.value = ""; }} /></label><Button variant="outline" size="sm" onClick={addTestcase}><Plus className="size-4" /> Thêm testcase</Button></div></div><div className="rounded-lg border-2 border-dashed border-indigo-200 bg-indigo-50 p-5 text-center text-xs text-muted-foreground" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); const file = event.dataTransfer.files[0]; if (file) void importTestcases(file); }}><FileArchive className="mx-auto mb-2 size-6 text-indigo-700" /><p className="font-semibold text-indigo-900">Kéo thả file ZIP vào đây hoặc chọn file JSON</p><p>File JSON có thể là mảng testcase hoặc object có thuộc tính <code>testcases</code>.</p></div><div className="overflow-x-auto rounded-lg border"><table className="w-full min-w-[680px] text-xs"><thead className="bg-indigo-50 text-left"><tr><th className="px-3 py-2">Test #</th><th className="px-3 py-2">Input mẫu</th><th className="px-3 py-2">Output mong đợi</th><th className="px-3 py-2">Thao tác</th></tr></thead><tbody>{draft.testcases.map((testcase, index) => <tr key={testcase.id} className="border-t"><td className="px-3 py-2 font-semibold">#{index + 1}</td><td className="px-3 py-2"><Textarea rows={3} value={testcase.input} onChange={(event) => updateTestcase(index, "input", event.target.value)} className="min-w-48 resize-y whitespace-pre font-mono" /></td><td className="px-3 py-2"><Textarea rows={3} value={testcase.expected_output} onChange={(event) => updateTestcase(index, "expected_output", event.target.value)} className="min-w-48 resize-y whitespace-pre font-mono" /></td><td className="px-3 py-2"><Button variant="ghost" size="icon" onClick={() => removeTestcase(index)} title="Xóa testcase"><Trash2 className="size-4" /></Button></td></tr>)}</tbody></table></div></div>
  </section>;
}
