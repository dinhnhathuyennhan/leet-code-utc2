"use client";

import { useState } from "react";
import { Plus, Save } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { addAdminTestcase, deleteAdminTestcase, updateAdminTestcase } from "@/lib/api/endpoints/admin-management";
import { getErrorMessage } from "@/lib/helpers/error-message";
import type { AdminProblem, AdminTestcase, AdminTestcasePayload } from "@/lib/types/admin";
import { AdminConfirm, ADMIN_PRIMARY } from "./admin-ui";

const asText = (value: unknown, raw: boolean) => raw && typeof value === "string" ? value : JSON.stringify(value, null, 2) ?? "null";

function TestcaseForm({ problem, testcase, onClose, onChanged }: {
  problem: AdminProblem; testcase?: AdminTestcase; onClose: () => void; onChanged: () => Promise<void>;
}) {
  const format = problem.function_name ? "json_args" : "stdin";
  const [input, setInput] = useState(testcase ? asText(testcase.input, format === "stdin") : format === "stdin" ? "" : "[]");
  const [output, setOutput] = useState(testcase ? asText(testcase.expected_output, format === "stdin") : format === "stdin" ? "" : "null");
  const [sample, setSample] = useState(testcase?.is_sample ?? false);
  const [busy, setBusy] = useState(false);

  async function save(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    let payload: AdminTestcasePayload;
    try {
      if (format === "stdin") {
        payload = { input, expected_output: output, is_sample: sample, input_type: "stdin", expected_output_type: "stdout" };
      } else {
        const parsedInput: unknown = JSON.parse(input);
        if (!Array.isArray(parsedInput)) throw new Error("Input JSON phải là mảng các tham số của hàm.");
        payload = { input: parsedInput, expected_output: JSON.parse(output) as unknown, is_sample: sample, input_type: "json_args", expected_output_type: "json" };
      }
    } catch (error) { toast.error(error instanceof SyntaxError ? "Input và output phải là JSON hợp lệ." : getErrorMessage(error)); return; }
    setBusy(true);
    try {
      if (testcase) await updateAdminTestcase(problem.id, testcase.id, payload);
      else await addAdminTestcase(problem.id, payload);
      await onChanged();
      toast.success(testcase ? "Đã cập nhật testcase." : "Đã thêm testcase.");
      onClose();
    } catch (error) { toast.error(getErrorMessage(error)); } finally { setBusy(false); }
  }
  return <form onSubmit={(event) => void save(event)} className="space-y-4 rounded-xl border bg-muted/30 p-4">
    <p className="text-xs text-muted-foreground">{problem.function_name ? `Hàm ${problem.function_name} được chấm với input JSON.` : "Đề này được chấm qua stdin/stdout."}</p>
    <div className="grid gap-4 sm:grid-cols-2">
      <label className="block space-y-2 text-sm font-medium">{format === "stdin" ? "Input (stdin)" : "Input JSON (mảng tham số)"}<Textarea rows={5} className="font-mono text-xs" value={input} onChange={(event) => setInput(event.target.value)} disabled={busy} /></label>
      <label className="block space-y-2 text-sm font-medium">{format === "stdin" ? "Output mong đợi (stdout)" : "Output JSON mong đợi"}<Textarea rows={5} className="font-mono text-xs" value={output} onChange={(event) => setOutput(event.target.value)} disabled={busy} /></label>
    </div>
    <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={sample} onChange={(event) => setSample(event.target.checked)} disabled={busy} />Testcase mẫu (sinh viên có thể xem)</label>
    <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={onClose} disabled={busy}>Hủy</Button><Button type="submit" disabled={busy} className={ADMIN_PRIMARY}><Save className="size-4" />{busy ? "Đang lưu..." : "Lưu testcase"}</Button></div>
  </form>;
}

export function AdminProblemTestcases({ problem, onChanged }: { problem: AdminProblem; onChanged: () => Promise<void> }) {
  const [editing, setEditing] = useState<number | "new" | null>(null);
  return <section className="space-y-4 rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-bold">Testcase ({problem.testcases.length})</h2><p className="text-xs text-muted-foreground">Các thay đổi được lưu ngay. Khi đã có bài nộp, backend sẽ khóa sửa testcase để giữ kết quả chấm cũ.</p></div><Button variant="outline" onClick={() => setEditing("new")} disabled={editing !== null}><Plus className="size-4" />Thêm testcase</Button></div>
    {editing === "new" && <TestcaseForm problem={problem} onClose={() => setEditing(null)} onChanged={onChanged} />}
    {problem.testcases.map((testcase, index) => <div key={testcase.id} className="space-y-3 rounded-xl border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-semibold">Test #{index + 1} · {testcase.input_type === "stdin" ? "stdin/stdout" : "JSON"} {testcase.is_sample ? "· Mẫu" : "· Ẩn"}</p><div className="flex gap-2"><Button variant="outline" size="sm" disabled={editing !== null} onClick={() => setEditing(testcase.id)}>Sửa</Button><AdminConfirm label="Xóa" title="Xóa testcase?" description="Testcase này sẽ bị xóa vĩnh viễn. Bài tập phải còn ít nhất một testcase." disabled={editing !== null || problem.testcases.length <= 1} onConfirm={async () => { await deleteAdminTestcase(problem.id, testcase.id); await onChanged(); toast.success("Đã xóa testcase."); }} /></div></div>
      {editing === testcase.id ? <TestcaseForm problem={problem} testcase={testcase} onClose={() => setEditing(null)} onChanged={onChanged} /> : <div className="grid gap-3 text-xs sm:grid-cols-2"><div><p className="mb-1 text-muted-foreground">Input</p><pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-muted p-3">{asText(testcase.input, testcase.input_type === "stdin")}</pre></div><div><p className="mb-1 text-muted-foreground">Output mong đợi</p><pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-muted p-3">{asText(testcase.expected_output, testcase.expected_output_type === "stdout")}</pre></div></div>}
    </div>)}
  </section>;
}
