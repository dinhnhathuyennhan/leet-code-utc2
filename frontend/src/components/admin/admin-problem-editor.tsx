"use client";

import { useState } from "react";
import { Plus, Save, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { getErrorMessage } from "@/lib/helpers/error-message";
import type { AdminProblem, AdminProblemPayload } from "@/lib/types/admin";
import { ADMIN_PRIMARY, ADMIN_SELECT } from "./admin-ui";

const LANGUAGES = ["python", "c", "cpp", "java"] as const;
function dateTimeInput(value: string) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Ho_Chi_Minh", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
  }).formatToParts(new Date(value));
  const p = Object.fromEntries(parts.map((item) => [item.type, item.value]));
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}`;
}
const withVietnamOffset = (value: string) => `${value.length === 16 ? `${value}:00` : value}+07:00`;
const encodeJson = (value: unknown) => JSON.stringify(value, null, 2) ?? "null";
const draftTests = (problem?: AdminProblem) => problem?.testcases.map((test) => ({
  input: encodeJson(test.input), expected: encodeJson(test.expected_output), sample: test.is_sample,
})) ?? [{ input: "[]", expected: "null", sample: true }];

export function AdminProblemEditor({ problem, onSave, onBusyChange, uploadTestcases, hideTestcases = false }: {
  problem?: AdminProblem;
  onSave: (data: AdminProblemPayload) => Promise<unknown>;
  onBusyChange?: (busy: boolean) => void;
  uploadTestcases?: (file: File) => Promise<AdminProblem>;
  hideTestcases?: boolean;
}) {
  const [title, setTitle] = useState(problem?.title ?? "");
  const [functionName, setFunctionName] = useState(problem?.function_name ?? "");
  const [description, setDescription] = useState(problem?.description ?? "");
  const [constraints, setConstraints] = useState(problem?.constraints ?? "");
  const [level, setLevel] = useState<AdminProblemPayload["level"]>((problem?.level as AdminProblemPayload["level"]) ?? "easy");
  const [timeLimit, setTimeLimit] = useState(problem?.time_limit_seconds ?? 1);
  const [start, setStart] = useState(problem ? dateTimeInput(problem.start_datetime) : "");
  const [end, setEnd] = useState(problem ? dateTimeInput(problem.end_datetime) : "");
  const [hint, setHint] = useState(problem?.hint ?? "");
  const [complexity, setComplexity] = useState(problem?.complexity ?? "");
  const [codes, setCodes] = useState<Record<string, string>>({ python: problem?.starter_code ?? "", c: "", cpp: "", java: "", ...problem?.starter_codes });
  const [language, setLanguage] = useState<string>("python");
  const [tests, setTests] = useState(() => draftTests(problem));
  const [busy, setBusy] = useState(false);

  function markBusy(next: boolean) { setBusy(next); onBusyChange?.(next); }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    if (!title.trim() || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(functionName.trim())) { toast.error("Nhập tên bài và tên hàm hợp lệ (chữ ASCII, số, dấu gạch dưới)."); return; }
    if (!start || !end || start >= end) { toast.error("Thời gian mở đề phải trước hạn nộp."); return; }
    const missing = LANGUAGES.find((item) => !codes[item]?.trim());
    if (missing) { setLanguage(missing); toast.error(`Vui lòng nhập mã nguồn khởi tạo cho ${missing.toUpperCase()}.`); return; }
    if (!tests.length) { toast.error("Cần ít nhất một testcase."); return; }
    let testcases: AdminProblemPayload["testcases"];
    try {
      testcases = tests.map((test, index) => {
        const input: unknown = JSON.parse(test.input);
        if (!Array.isArray(input)) throw new Error(`Input test #${index + 1} phải là mảng JSON các đối số.`);
        return { input, expected_output: JSON.parse(test.expected) as unknown, is_sample: test.sample };
      });
    } catch (error) { toast.error(error instanceof SyntaxError ? "Input/output testcase phải là JSON hợp lệ." : getErrorMessage(error)); return; }
    markBusy(true);
    try {
      await onSave({
        title: title.trim(), function_name: functionName.trim(), description: description.trim(), constraints: constraints.trim(), level,
        time_limit_seconds: timeLimit, start_datetime: withVietnamOffset(start), end_datetime: withVietnamOffset(end),
        starter_codes: Object.fromEntries(LANGUAGES.map((item) => [item, codes[item]])),
        hint: hint.trim() || null, complexity: complexity.trim() || null, testcases,
      });
    } catch (error) { toast.error(getErrorMessage(error)); } finally { markBusy(false); }
  }
  async function upload(file: File) {
    if (!uploadTestcases || busy) return;
    if (!/\.(json|zip)$/i.test(file.name) || file.size > 5 * 1024 * 1024) { toast.error("Chọn file JSON/ZIP không vượt quá 5 MB."); return; }
    markBusy(true);
    try { const result = await uploadTestcases(file); setTests(draftTests(result)); toast.success(`Đã nhập ${result.testcases.length} testcase.`); }
    catch (error) { toast.error(getErrorMessage(error)); } finally { markBusy(false); }
  }
  return <form onSubmit={(event) => void submit(event)} className="space-y-6">
    <fieldset disabled={busy} className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="space-y-2 text-sm font-medium">Tên bài tập<Input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={255} required /></label>
        <label className="space-y-2 text-sm font-medium">Tên hàm cần chấm<Input value={functionName} onChange={(event) => setFunctionName(event.target.value)} placeholder="solve" maxLength={100} required /></label>
        <label className="space-y-2 text-sm font-medium">Mức độ<select value={level} onChange={(event) => setLevel(event.target.value as typeof level)} className={`${ADMIN_SELECT} w-full`}><option value="easy">Dễ</option><option value="medium">Trung bình</option><option value="hard">Khó</option></select></label>
        <label className="space-y-2 text-sm font-medium">Giới hạn thời gian (giây)<Input type="number" min={1} step={1} value={timeLimit} onChange={(event) => setTimeLimit(Number(event.target.value))} required /></label>
        <label className="space-y-2 text-sm font-medium">Mở đề (giờ Việt Nam)<Input type="datetime-local" step={1} value={start} onChange={(event) => setStart(event.target.value)} required /></label>
        <label className="space-y-2 text-sm font-medium">Hạn nộp (giờ Việt Nam)<Input type="datetime-local" step={1} value={end} min={start} onChange={(event) => setEnd(event.target.value)} required /></label>
      </div>
      <label className="block space-y-2 text-sm font-medium">Nội dung đề bài<Textarea rows={5} value={description} onChange={(event) => setDescription(event.target.value)} required /></label>
      <label className="block space-y-2 text-sm font-medium">Ràng buộc<Textarea rows={3} value={constraints} onChange={(event) => setConstraints(event.target.value)} required /></label>
      <div className="grid gap-4 sm:grid-cols-2"><label className="space-y-2 text-sm font-medium">Gợi ý<Textarea value={hint} onChange={(event) => setHint(event.target.value)} /></label><label className="space-y-2 text-sm font-medium">Độ phức tạp<Input value={complexity} onChange={(event) => setComplexity(event.target.value)} placeholder="O(n)" /></label></div>
      <section className="space-y-3 rounded-xl border p-4">
        <h2 className="font-semibold">Mã nguồn khởi tạo</h2>
        <p className="text-xs text-muted-foreground">Cung cấp hàm {functionName || "solve"} cho cả Python, C, C++ và Java.</p>
        <div className="flex flex-wrap gap-2">{LANGUAGES.map((item) => <Button key={item} type="button" variant={language === item ? "secondary" : "outline"} size="sm" aria-pressed={language === item} onClick={() => setLanguage(item)}>{item.toUpperCase()}{codes[item]?.trim() ? " ✓" : ""}</Button>)}</div>
        <Textarea aria-label={`Mã khởi tạo ${language}`} rows={9} value={codes[language] ?? ""} onChange={(event) => setCodes({ ...codes, [language]: event.target.value })} className="bg-slate-950 font-mono text-xs text-slate-100" />
      </section>
      {!hideTestcases && <section className="space-y-4 rounded-xl border p-4">
        <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="font-semibold">Testcase ({tests.length})</h2><div className="flex gap-2">
          {uploadTestcases && <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-xs"><Upload className="size-4" />Nhập JSON/ZIP<input type="file" accept=".json,.zip" disabled={busy} className="hidden" onChange={(event) => { const file = event.target.files?.[0]; event.target.value = ""; if (file) void upload(file); }} /></label>}
          <Button type="button" variant="outline" size="sm" onClick={() => setTests([...tests, { input: "[]", expected: "null", sample: false }])}><Plus className="size-4" />Thêm test</Button>
        </div></div>
        <p className="text-xs text-muted-foreground">Input là mảng JSON các đối số, ví dụ [[1, 2, 3], 4]. Output là một giá trị JSON.</p>
        {tests.map((test, index) => <div key={index} className="space-y-3 rounded-lg bg-muted/50 p-3">
          <div className="flex items-center justify-between gap-2"><span className="text-sm font-medium">Test #{index + 1}</span><div className="flex items-center gap-3"><label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={test.sample} onChange={(event) => setTests(tests.map((item, i) => i === index ? { ...item, sample: event.target.checked } : item))} />Test mẫu</label><Button type="button" variant="ghost" size="icon" disabled={tests.length === 1} onClick={() => setTests(tests.filter((_, i) => i !== index))} aria-label={`Xóa test ${index + 1}`}><Trash2 className="size-4" /></Button></div></div>
          <div className="grid gap-3 sm:grid-cols-2"><label className="space-y-1 text-xs font-medium">Input JSON<Textarea rows={3} value={test.input} onChange={(event) => setTests(tests.map((item, i) => i === index ? { ...item, input: event.target.value } : item))} className="font-mono text-xs" /></label>
            <label className="space-y-1 text-xs font-medium">Output JSON<Textarea rows={3} value={test.expected} onChange={(event) => setTests(tests.map((item, i) => i === index ? { ...item, expected: event.target.value } : item))} className="font-mono text-xs" /></label></div>
        </div>)}
      </section>}
    </fieldset>
    <div className="flex justify-end"><Button type="submit" disabled={busy} className={ADMIN_PRIMARY}><Save className="size-4" />{busy ? "Đang xử lý..." : problem ? "Lưu bài tập" : "Tạo bài tập nguồn"}</Button></div>
  </form>;
}
