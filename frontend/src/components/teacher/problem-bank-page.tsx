"use client";

import { useEffect, useState } from "react";
import { Filter, Plus, Search } from "lucide-react";
import { toast } from "sonner";
import { getProblems, type ProblemListItem } from "@/lib/api/endpoints/problems";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorState } from "@/components/shared/page-state";
import { Skeleton } from "@/components/ui/skeleton";

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
  const pageSize = 12;

  useEffect(() => {
    let active = true;
    void getProblems({ q: query.trim() || undefined, level: level || undefined, page, page_size: pageSize }).then((response) => { if (!active) return; setError(null); setItems(response.items); setTotal(response.total); }).catch((requestError) => { if (active) setError(requestError); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [query, level, page, refreshKey]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  return <section className="min-h-[calc(100dvh-110px)] rounded-xl bg-[#f8f9ff] shadow-sm"><header className="flex flex-wrap items-center justify-between gap-3 border-b bg-card px-4 py-3 sm:px-6"><div><h1 className="text-xl font-bold text-[#2f226b] sm:text-2xl">Ngân hàng bài</h1><p className="text-sm text-muted-foreground">Danh sách bài từ backend, gồm bài dùng chung và bài thuộc các khóa học của bạn.</p></div><Button onClick={() => toast.info("Form tạo bài đã được tích hợp trong trang soạn buổi học.")} className="bg-[#34227a] text-white"><Plus className="size-4" /> Tạo bài</Button></header>
    <div className="m-4 flex flex-wrap items-center gap-3 rounded-xl bg-card p-3"><div className="relative min-w-0 flex-1 sm:min-w-64"><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} className="h-9 pl-9" placeholder="Tìm mã hoặc tên bài..." /></div><div className="flex items-center gap-2"><Filter className="size-4 text-muted-foreground" /><select value={level} onChange={(event) => { setLevel(event.target.value as typeof level); setPage(1); }} className="h-9 rounded-md border bg-background px-3 text-sm">{LEVELS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></div></div>
    {loading ? <div className="grid gap-4 px-4 pb-6 md:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }, (_, index) => <Skeleton key={index} className="h-36 rounded-xl" />)}</div> : error ? <div className="p-4"><ErrorState error={error} onRetry={() => setRefreshKey((current) => current + 1)} /></div> : <><div className="grid gap-4 px-4 pb-6 md:grid-cols-2 xl:grid-cols-3">{items.map((problem) => <ProblemCard key={problem.id} problem={problem} />)}{!items.length && <div className="col-span-full rounded-xl bg-card p-10 text-center text-sm text-muted-foreground">Không tìm thấy bài phù hợp.</div>}</div><footer className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-4 text-sm text-muted-foreground"><span>{total} bài · Trang {page}/{totalPages}</span><div className="flex gap-2"><Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>Trang trước</Button><Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)}>Trang sau</Button></div></footer></>}
  </section>;
}

function ProblemCard({ problem }: { problem: ProblemListItem }) {
  const level = problem.level === "easy" ? "Dễ" : problem.level === "hard" ? "Khó" : "Trung bình";
  return <article className="min-w-0 rounded-xl bg-card p-4 shadow-sm"><div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="font-mono text-xs text-indigo-700">{problem.code ?? `Problem #${problem.id}`}</p><h2 className="mt-1 truncate font-bold text-slate-900" title={problem.title}>{problem.title}</h2></div><span className="shrink-0 rounded px-2 py-0.5 text-xs font-semibold bg-indigo-50 text-indigo-700">{level}</span></div><div className="mt-4 flex items-center justify-between text-xs text-muted-foreground"><span>{problem.total_number_testcase} testcase</span><span>{problem.lesson_id === null ? "Ngân hàng chung" : "Đã gắn lớp"}</span></div></article>;
}
