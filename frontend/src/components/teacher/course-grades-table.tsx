"use client";

import { useMemo, useState } from "react";
import { Download, Search } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { updateSubmission } from "@/lib/api/endpoints/dashboard";
import { downloadCsv } from "@/lib/helpers/download";
import type { GradeRow, GradeScoreValue, GradeSessionColumn } from "@/lib/types/course";
import { normalizeGradeScore } from "./grade-cell";

type OverrideEntry = { value: number; feedback: string };
type OverrideMap = Record<string, OverrideEntry>;

function keyOf(studentId: string, sessionId: string | number, problemId: string | number) { return `${studentId}:${sessionId}:${problemId}`; }
function scoreFor(score: GradeScoreValue | undefined, key: string, overrides: OverrideMap) { return overrides[key]?.value ?? normalizeGradeScore(score) ?? 0; }
function average(values: Array<number | null>) { return values.length ? values.reduce<number>((sum, value) => sum + (value ?? 0), 0) / values.length : 0; }
function sessionScore(scores: GradeScoreValue[], session: GradeSessionColumn, studentId: string, overrides: OverrideMap) { return average(session.problems.map((problem, index) => scoreFor(scores[index], keyOf(studentId, session.id, problem.id), overrides))); }
function overallScore(row: GradeRow, sessions: GradeSessionColumn[], overrides: OverrideMap) { return sessions.length ? average(sessions.map((session) => sessionScore(row.session_scores?.[String(session.id)] ?? [], session, row.student_id, overrides))) : 0; }
function hasSubmitted(score: GradeScoreValue | undefined) { return score !== null && score !== undefined && (typeof score === "object" ? score.submitted === true : true); }
function isMissing(score: GradeScoreValue | undefined, override: OverrideEntry | undefined) { return override === undefined && !hasSubmitted(score); }

export function CourseGradesTable({ rows, sessions, onUpdated }: { rows: GradeRow[]; sessions: GradeSessionColumn[]; onUpdated?: () => void }) {
  const [query, setQuery] = useState("");
  const [overrides, setOverrides] = useState<OverrideMap>({});
  const [selected, setSelected] = useState<{ key: string; value: number; feedback: string; submissionId: number | null; label: string } | null>(null);
  const [input, setInput] = useState("");
  const [feedback, setFeedback] = useState("");
  const filteredRows = useMemo(() => query.trim() ? rows.filter((row) => `${row.student_id} ${row.full_name} ${row.class_id ?? ""}`.toLowerCase().includes(query.toLowerCase())) : rows, [rows, query]);

  function openCell(row: GradeRow, session: GradeSessionColumn, problemIndex: number) {
    const problem = session.problems[problemIndex];
    const key = keyOf(row.student_id, session.id, problem.id);
    const source = row.session_scores?.[String(session.id)]?.[problemIndex];
    const serverEntry = source && typeof source === "object" && source.manual_score != null ? { value: source.manual_score, feedback: source.feedback ?? "" } : undefined;
    const entry = overrides[key] ?? serverEntry;
    const value = scoreFor(row.session_scores?.[String(session.id)]?.[problemIndex], key, overrides) ?? 0;
    const submissionId = source && typeof source === "object" ? source.submission_id ?? null : null;
    setSelected({ key, value, feedback: entry?.feedback ?? "", submissionId, label: `${row.full_name} · ${problem.code}` });
    setInput(String(value));
    setFeedback(entry?.feedback ?? "");
  }

  async function saveOverride() {
    if (!selected) return;
    const value = Number(input);
    if (!Number.isFinite(value) || value < 0 || value > 10) { toast.error("Điểm phải nằm trong khoảng 0 đến 10."); return; }
    try {
      if (selected.submissionId) await updateSubmission(selected.submissionId, { manual_score: value, feedback });
      const next = { ...overrides, [selected.key]: { value, feedback } };
      setOverrides(next);
      setSelected(null);
      onUpdated?.();
      toast.success("Đã lưu điểm ghi đè và nhận xét.");
    } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể lưu điểm ghi đè."); }
  }

  const headers = ["STT", "MSSV", "Họ tên", "Lớp", ...sessions.flatMap((session) => [...session.problems.map((problem) => `Buổi ${session.order}: ${problem.code}`), `Buổi ${session.order}: TỔNG`]), "ĐIỂM TỔNG"];
  const exportRows = filteredRows.map((row, index) => [index + 1, row.student_id, row.full_name, row.class_id ?? "—", ...sessions.flatMap((session) => { const scores = row.session_scores?.[String(session.id)] ?? []; return [...session.problems.map((problem, problemIndex) => { const key = keyOf(row.student_id, session.id, problem.id); const value = scoreFor(scores[problemIndex], key, overrides) ?? 0; return `${value.toFixed(1)}${overrides[key] ? "*" : ""}`; }), sessionScore(scores, session, row.student_id, overrides).toFixed(1)]; }), overallScore(row, sessions, overrides).toFixed(1)]);

  return <section className="space-y-4 rounded-xl bg-card p-4 shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3"><div className="relative w-full max-w-xs"><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={query} onChange={(event) => setQuery(event.target.value)} className="h-9 pl-9" placeholder="Nhập MSSV, họ tên, lớp..." /></div><Button variant="outline" onClick={() => downloadCsv("bang-diem.xls", [headers, ...exportRows])}><Download className="size-4" /> Xuất bảng điểm</Button></div><div className="overflow-x-auto rounded-lg"><table className="min-w-[1180px] w-full border-separate border-spacing-0 text-xs"><thead><tr className="bg-indigo-100"><th colSpan={4} className="px-4 py-3 text-left">THÔNG TIN SINH VIÊN</th>{sessions.map((session) => <th key={session.id} colSpan={session.problems.length + 1} className="border-l px-2 py-3 text-center">Buổi {session.order}: {session.title}</th>)}<th className="bg-[#36237b] px-3 py-3 text-white">ĐIỂM TỔNG</th></tr><tr className="bg-indigo-50"><th colSpan={4} /><>{sessions.flatMap((session) => [...session.problems.map((problem) => <th key={`${session.id}-${problem.id}`} className="border-l px-3 py-2">{problem.code}</th>), <th key={`${session.id}-total`} className="border-l px-3 py-2">TỔNG</th>])}</><th /></tr></thead><tbody>{filteredRows.map((row, index) => { const rowHasSubmission = sessions.some((session) => (row.session_scores?.[String(session.id)] ?? []).some(hasSubmitted)); return <tr key={row.student_id} className={`border-t ${!rowHasSubmission ? "bg-red-50" : ""}`}><td className="px-3 py-3">{index + 1}</td><td className="px-3 py-3 font-semibold">{row.student_id}</td><td className="px-3 py-3">{row.full_name}</td><td className="px-3 py-3">{row.class_id ?? "—"}</td>{sessions.flatMap((session) => { const scores = row.session_scores?.[String(session.id)] ?? []; return [...session.problems.map((problem, problemIndex) => { const key = keyOf(row.student_id, session.id, problem.id); const missing = isMissing(scores[problemIndex], overrides[key]); const value = scoreFor(scores[problemIndex], key, overrides); return <td key={key} className={`px-3 py-3 text-center ${missing ? "bg-red-100 text-red-700" : ""}`}><button type="button" onClick={() => openCell(row, session, problemIndex)} className="rounded px-2 py-1 font-semibold hover:bg-indigo-100">{value.toFixed(1)}{overrides[key] ? "*" : ""}</button></td>; }), <td key={`${row.student_id}-${session.id}-total`} className="bg-indigo-50 px-3 py-3 text-center font-bold">{sessionScore(scores, session, row.student_id, overrides).toFixed(1)}</td>]; })}<td className="bg-indigo-50 px-3 py-3 text-center font-bold">{overallScore(row, sessions, overrides).toFixed(1)}</td></tr>; })}</tbody></table></div>{selected && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" onClick={() => setSelected(null)}><div className="w-full max-w-sm space-y-4 rounded-xl bg-card p-5 shadow-xl" onClick={(event) => event.stopPropagation()}><div><h2 className="font-semibold">Ghi đè điểm</h2><p className="mt-1 text-sm text-muted-foreground">{selected.label}</p></div><label className="block text-sm font-medium">Điểm<Input type="number" min={0} max={10} step={0.1} value={input} onChange={(event) => setInput(event.target.value)} className="mt-1" /></label><label className="block text-sm font-medium">Nhận xét<Textarea value={feedback} onChange={(event) => setFeedback(event.target.value)} className="mt-1" placeholder="Nhập nhận xét cho sinh viên..." /></label><div className="flex justify-end gap-2"><Button variant="outline" onClick={() => setSelected(null)}>Huỷ</Button><Button onClick={saveOverride} className="bg-[#2f226b] text-white">Lưu điểm *</Button></div></div></div>}</section>;
}
