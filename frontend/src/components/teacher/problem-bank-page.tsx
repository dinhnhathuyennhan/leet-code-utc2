"use client";

import { useEffect, useState } from "react";
import { Plus, Search, X } from "lucide-react";
import { toast } from "sonner";
import { getProblems, type ProblemListItem } from "@/lib/api/endpoints/problems";
import { createBankProblem, type ProblemCreateRequest } from "@/lib/api/endpoints/courses";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState } from "@/components/shared/page-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import { parseInputText, parseOutputText } from "@/lib/helpers/testcases";

const LEVELS = [{ value: "", label: "Tất cả mức độ" }, { value: "easy", label: "Dễ" }, { value: "medium", label: "Trung bình" }, { value: "hard", label: "Khó" }] as const;

export function ProblemBankPage() {
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState<"" | "easy" | "medium" | "hard">("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<ProblemListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedProblem, setSelectedProblem] = useState<ProblemListItem | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const pageSize = 12;
  // Chờ người dùng gõ xong mới gọi API, thay vì bắn một request cho mỗi phím.
  const debouncedQuery = useDebouncedValue(query, 300);

  useEffect(() => {
    let active = true;
    void getProblems({ q: debouncedQuery.trim() || undefined, level: level || undefined, page, page_size: pageSize }).then((response) => { if (!active) return; setError(null); setItems(response.items); setTotal(response.total); }).catch((requestError) => { if (active) setError(requestError); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [debouncedQuery, level, page, refreshKey]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  return <section className="space-y-6"><header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-sm font-medium text-indigo-700 dark:text-indigo-300">Giảng viên</p><h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Ngân hàng đề</h1><p className="mt-1 max-w-3xl text-sm text-muted-foreground">Đề nguồn và bài tập trong các buổi học của bạn.</p></div><Button onClick={() => setCreateOpen(true)} className="bg-[#352078] text-white hover:bg-[#29175f]"><Plus className="size-4" /> Tạo bài tập nguồn</Button></header>
    <div className="flex flex-wrap gap-3 rounded-xl border bg-card p-4"><div className="relative min-w-0 flex-1 sm:min-w-64"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} className="pl-9" placeholder="Tìm theo tên bài tập..." aria-label="Tìm bài tập nguồn" /></div><select value={level} onChange={(event) => { setLevel(event.target.value as typeof level); setPage(1); }} className="h-10 rounded-lg border bg-background px-3 text-sm" aria-label="Lọc độ khó">{LEVELS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></div>
    {loading ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }, (_, index) => <Skeleton key={index} className="h-36 rounded-xl" />)}</div> : error ? <ErrorState error={error} onRetry={() => setRefreshKey((current) => current + 1)} /> : <><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{items.map((problem) => <ProblemCard key={problem.id} problem={problem} onClick={() => setSelectedProblem(problem)} />)}{!items.length && <div className="col-span-full rounded-xl border bg-card p-10 text-center text-sm text-muted-foreground">Chưa có bài tập phù hợp</div>}</div><footer className="flex items-center justify-between gap-3 text-sm text-muted-foreground"><span>Tổng {total} bài tập</span><div className="flex items-center gap-2"><Button variant="outline" disabled={page === 1} onClick={() => setPage((current) => current - 1)}>Trước</Button><span>Trang {page}</span><Button variant="outline" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)}>Sau</Button></div></footer></>}
    {selectedProblem && <ProblemPreview problem={selectedProblem} onClose={() => setSelectedProblem(null)} />}
    {createOpen && <BankProblemCreateDialog onClose={() => setCreateOpen(false)} onCreated={() => { setCreateOpen(false); setRefreshKey((current) => current + 1); }} />}
  </section>;
}

function ProblemCard({ problem, onClick }: { problem: ProblemListItem; onClick: () => void }) {
  const level = problem.level === "easy" ? "Dễ" : problem.level === "hard" ? "Khó" : "Trung bình";
  return <button type="button" onClick={onClick} className="min-w-0 rounded-xl border bg-card p-5 text-left shadow-sm transition hover:border-indigo-300 hover:shadow-md"><div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="text-xs font-medium text-muted-foreground">{problem.code ?? `#${problem.id}`}</p><h2 className="mt-2 truncate font-semibold" title={problem.title}>{problem.title}</h2></div><span className="shrink-0 rounded-md bg-indigo-50 px-2 py-1 text-xs text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">{level}</span></div><p className="mt-3 text-sm text-muted-foreground">{problem.total_number_testcase} testcase · {problem.lesson_id === null ? "Đề nguồn" : "Đã gắn lớp"}</p><p className="mt-4 text-sm font-medium text-indigo-700 dark:text-indigo-300">Xem chi tiết</p></button>;
}

function ProblemPreview({ problem, onClose }: { problem: ProblemListItem; onClose: () => void }) {
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}><div className="w-full max-w-lg space-y-4 rounded-2xl bg-card p-6 shadow-xl" onClick={(event) => event.stopPropagation()}><div className="flex items-start justify-between gap-4"><div><p className="font-mono text-xs text-indigo-700">{problem.code ?? `Problem #${problem.id}`}</p><h2 className="text-xl font-bold">{problem.title}</h2></div><Button variant="ghost" size="icon" onClick={onClose}><X className="size-4" /></Button></div><div className="grid grid-cols-2 gap-3 text-sm"><p><span className="text-muted-foreground">Mức độ:</span> {problem.level}</p><p><span className="text-muted-foreground">Testcase:</span> {problem.total_number_testcase}</p><p className="col-span-2"><span className="text-muted-foreground">Nguồn:</span> {problem.lesson_id === null ? "Ngân hàng chung (lesson_id = null)" : "Bài đã gắn lesson"}</p></div><p className="text-xs text-muted-foreground">Bài trong ngân hàng được giữ nguyên nguồn. Khi thêm vào buổi học, frontend sẽ gửi id nguồn qua API attach để backend tạo bản sao riêng.</p></div></div>;
}

function BankProblemCreateDialog({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [title, setTitle] = useState("");
  const [functionName, setFunctionName] = useState("solution");
  const [description, setDescription] = useState("");
  const [constraints, setConstraints] = useState("");
  const [starterCode, setStarterCode] = useState("");
  const [input, setInput] = useState("");
  const [output, setOutput] = useState("0");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  async function save() {
    try {
      const parsedInput = parseInputText(input);
      const parsedOutput = parseOutputText(output);
      if (!title.trim() || !functionName.trim() || !description.trim() || !constraints.trim() || !starterCode.trim()) throw new Error("Vui lòng điền đủ các trường bắt buộc.");
      const data: ProblemCreateRequest = { title: title.trim(), function_name: functionName.trim(), description, constraints, level: "easy", time_limit_seconds: 1, starter_codes: { python: starterCode, c: starterCode, cpp: starterCode, java: starterCode }, start_datetime: "2026-01-01T00:00:00+07:00", end_datetime: "2099-12-31T23:59:00+07:00", testcases: [{ input: parsedInput, expected_output: parsedOutput, is_sample: true }] };
      setSaving(true); await createBankProblem(data); toast.success("Đã tạo bài trong ngân hàng (lesson_id = null)."); onCreated();
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Không thể tạo bài."); }
    finally { setSaving(false); }
  }
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><div className="max-h-[95dvh] w-full max-w-4xl space-y-4 overflow-y-auto rounded-2xl bg-card p-6"><div className="flex items-center justify-between"><h2 className="text-xl font-bold">Tạo bài trong ngân hàng</h2><Button variant="ghost" size="icon" onClick={onClose}><X className="size-4" /></Button></div>{error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}<label className="block text-sm font-medium">Tên bài<Input value={title} onChange={(event) => setTitle(event.target.value)} /></label><label className="block text-sm font-medium">Tên hàm<Input value={functionName} onChange={(event) => setFunctionName(event.target.value)} /></label><label className="block text-sm font-medium">Mô tả<Textarea value={description} onChange={(event) => setDescription(event.target.value)} /></label><label className="block text-sm font-medium">Ràng buộc<Textarea value={constraints} onChange={(event) => setConstraints(event.target.value)} /></label><label className="block text-sm font-medium">Starter code<textarea value={starterCode} onChange={(event) => setStarterCode(event.target.value)} className="min-h-[320px] w-full resize-y rounded-lg border bg-slate-900 p-4 font-mono text-sm leading-6 text-white" /></label><div className="grid gap-3 sm:grid-cols-2"><label className="text-sm font-medium">Testcase #1 input (ví dụ: 2, 7, 11, 15)<Textarea value={input} onChange={(event) => setInput(event.target.value)} className="min-h-32 font-mono" /></label><label className="text-sm font-medium">Testcase #1 output<Textarea value={output} onChange={(event) => setOutput(event.target.value)} className="min-h-32 font-mono" /></label></div><div className="flex justify-end gap-2"><Button variant="outline" onClick={onClose}>Hủy</Button><Button disabled={saving} onClick={() => void save()}>{saving ? "Đang tạo..." : "Tạo bài"}</Button></div></div></div>;
}
