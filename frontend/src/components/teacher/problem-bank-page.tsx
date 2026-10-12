"use client";

import { useMemo, useState } from "react";
import { Pencil, Plus, Search, Trash2, UserPlus } from "lucide-react";
import { toast } from "sonner";

import { MOCK_MY_PROBLEMS, MOCK_PUBLIC_PROBLEMS, type MockProblemBankItem } from "@/lib/mock/problem-bank";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type ProblemBankTab = "public" | "mine";

const levelClassName: Record<MockProblemBankItem["level"], string> = {
  DỄ: "bg-emerald-100 text-emerald-700",
  "TRUNG BÌNH": "bg-amber-100 text-amber-700",
  KHÓ: "bg-violet-100 text-violet-700",
};

export function ProblemBankPage() {
  const [activeTab, setActiveTab] = useState<ProblemBankTab>("public");
  const [query, setQuery] = useState("");
  const [myProblems, setMyProblems] = useState(MOCK_MY_PROBLEMS);
  const problems = activeTab === "public" ? MOCK_PUBLIC_PROBLEMS : myProblems;
  const filteredProblems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return problems;
    return problems.filter((problem) => `${problem.code} ${problem.title} ${problem.description}`.toLowerCase().includes(normalizedQuery));
  }, [problems, query]);

  function showMockAction(message: string) {
    // MOCKUP: Không gọi API khi nghiệp vụ ngân hàng đề chưa được triển khai.
    toast.info(message);
  }

  function removeMockProblem(id: string) {
    // MOCKUP: Chỉ xóa khỏi state cục bộ để mô phỏng thao tác trên tab của tôi.
    setMyProblems((current) => current.filter((problem) => problem.id !== id));
    toast.success("Đã xóa đề khỏi danh sách mockup.");
  }

  return <section className="min-h-[calc(100dvh-110px)] rounded-xl bg-[#f8f9ff] p-0 shadow-sm">
    <div className="flex items-center justify-between border-b bg-card px-4"><div className="flex gap-8"><TabButton active={activeTab === "public"} onClick={() => setActiveTab("public")}>Ngân hàng đề UTC2</TabButton><TabButton active={activeTab === "mine"} onClick={() => setActiveTab("mine")}>Ngân hàng của tôi {activeTab === "mine" && <span className="rounded bg-[#34227a] px-1.5 py-0.5 text-[10px] text-white">{myProblems.length}</span>}</TabButton></div><span className="text-xs text-muted-foreground">Cập nhật lúc: 14:30 hôm nay</span></div>
    <div className="m-4 rounded-xl bg-card p-3"><div className="flex flex-wrap items-center justify-between gap-3"><div className="relative w-full max-w-sm"><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input value={query} onChange={(event) => setQuery(event.target.value)} className="h-9 border-0 bg-[#f8f9ff] pl-9 shadow-none" placeholder="Nhập mã bài tập, tên bài cần tìm..." /></div><Button disabled={activeTab === "public"} onClick={() => showMockAction("Mở form thêm bài tập mockup.")} className="bg-[#34227a] text-white disabled:bg-slate-200 disabled:text-white"><UserPlus className="size-4" /> Thêm bài tập</Button></div></div>
    <div className="grid gap-4 px-4 pb-6 md:grid-cols-2 xl:grid-cols-3">{filteredProblems.map((problem) => <ProblemCard key={problem.id} problem={problem} editable={activeTab === "mine"} onEdit={() => showMockAction(`Mở form sửa ${problem.code}.`)} onDelete={() => removeMockProblem(problem.id)} />)}{filteredProblems.length === 0 && <div className="col-span-full rounded-xl bg-card p-10 text-center text-sm text-muted-foreground">Không tìm thấy bài tập phù hợp.</div>}</div>
  </section>;
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return <button type="button" onClick={onClick} className={`flex items-center gap-1.5 border-b-2 px-4 py-3 text-sm font-medium transition ${active ? "border-indigo-600 text-indigo-700" : "border-transparent text-slate-600 hover:text-indigo-700"}`}>{children}</button>;
}

function ProblemCard({ problem, editable, onEdit, onDelete }: { problem: MockProblemBankItem; editable: boolean; onEdit: () => void; onDelete: () => void }) {
  return <article className="group min-h-[128px] rounded-xl bg-card p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"><div className="flex items-start justify-between gap-3"><div><p className="font-mono text-[11px] font-semibold text-indigo-900">{problem.code}</p><h2 className="mt-1 text-sm font-bold text-indigo-950">{problem.title} <span className={`ml-1 rounded px-1.5 py-0.5 text-[10px] font-semibold ${levelClassName[problem.level]}`}>{problem.level}</span></h2></div>{editable && <div className="flex gap-2"><Button variant="ghost" size="icon" className="size-8 bg-[#34227a] text-white hover:bg-indigo-900" onClick={onEdit} aria-label={`Sửa ${problem.title}`}><Pencil className="size-4" /></Button><Button variant="ghost" size="icon" className="size-8 bg-[#34227a] text-white hover:bg-red-700" onClick={onDelete} aria-label={`Xóa ${problem.title}`}><Trash2 className="size-4" /></Button></div>}</div><p className="mt-3 text-xs leading-5 text-slate-600">{problem.description}</p>{!editable && <Button variant="ghost" size="sm" className="mt-2 h-7 px-0 text-xs text-indigo-700" onClick={() => toast.info("Đã chọn đề mockup.")}><Plus className="size-3" /> Chọn vào buổi học</Button>}</article>;
}
