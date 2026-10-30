"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpenCheck, Plus, Search } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { createAdminProblem, deleteAdminBankProblem, getAdminProblems } from "@/lib/api/endpoints/admin-management";
import { useDebouncedValue } from "@/lib/hooks/use-debounced-value";
import { adminKeys } from "@/lib/hooks/use-admin";
import { AdminProblemEditor } from "./admin-problem-editor";
import { AdminDialog, AdminHeading, ADMIN_PRIMARY, ADMIN_SELECT } from "./admin-ui";

export const adminLevelLabel = (level: string) => level === "easy" ? "Dễ" : level === "hard" ? "Khó" : "Trung bình";

export function AdminProblemBank() {
  const client = useQueryClient();
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState("");
  const [page, setPage] = useState(1);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const debounced = useDebouncedValue(search, 300);
  const query = useQuery({
    queryKey: [...adminKeys.problems, debounced, level, page],
    queryFn: () => getAdminProblems({ q: debounced.trim() || undefined, level: level || undefined, page, page_size: 20 }),
  });
  return <div className="space-y-6">
    <AdminHeading title="Ngân hàng đề" description="Đề nguồn và bài tập trong các buổi học. Gắn bài vào buổi học để tạo bản sao phục vụ giảng dạy."
      actions={<Button onClick={() => setCreating(true)} className={ADMIN_PRIMARY}><Plus className="size-4" />Tạo bài tập nguồn</Button>} />
    <div className="flex flex-wrap gap-3 rounded-xl border bg-card p-4"><div className="relative min-w-0 flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} className="pl-9" placeholder="Tìm theo tên bài tập..." aria-label="Tìm bài tập nguồn" /></div>
      <select className={ADMIN_SELECT} value={level} onChange={(event) => { setLevel(event.target.value); setPage(1); }} aria-label="Lọc độ khó"><option value="">Tất cả độ khó</option><option value="easy">Dễ</option><option value="medium">Trung bình</option><option value="hard">Khó</option></select></div>
    {query.isPending ? <p className="p-10 text-center text-sm text-muted-foreground">Đang tải ngân hàng đề...</p> : query.error ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : !query.data?.items.length ? <EmptyState icon={BookOpenCheck} title="Chưa có bài tập phù hợp" /> : <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{query.data.items.map((problem) => <article key={problem.id} className="space-y-3 rounded-xl border bg-card p-5 shadow-sm">
        <div className="flex justify-between gap-2"><p className="text-xs font-medium text-muted-foreground">{problem.code || `#${problem.id}`}</p><span className="rounded-md bg-indigo-50 px-2 py-1 text-xs text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">{adminLevelLabel(problem.level)}</span></div>
        <h2 className="font-semibold">{problem.title}</h2><p className="text-sm text-muted-foreground">{problem.total_number_testcase} testcase · {problem.lesson_id === null ? "Đề nguồn" : `Thuộc buổi #${problem.lesson_id}`}</p>
        <div className="flex gap-2"><Button asChild size="sm" variant="outline"><a href={`/admin/problem-bank/${problem.id}`}>Xem chi tiết</a></Button>{problem.lesson_id === null && <Button size="sm" variant="ghost" onClick={async () => { if (!window.confirm("Xóa đề nguồn này?")) return; try { await deleteAdminBankProblem(problem.id); await client.invalidateQueries({ queryKey: adminKeys.problems }); toast.success("Đã xóa đề nguồn."); } catch (error) { toast.error(String(error)); } }}>Xóa</Button>}</div>
      </article>)}</div>
      <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground"><span>Tổng {query.data.total} bài tập</span><div className="flex items-center gap-2"><Button variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)}>Trước</Button><span>Trang {page}</span><Button variant="outline" disabled={page * 20 >= query.data.total} onClick={() => setPage(page + 1)}>Sau</Button></div></div>
    </>}
    {creating && <AdminDialog open title="Tạo bài tập nguồn" description="Điền nội dung đề, mã khởi tạo và testcase cho bốn ngôn ngữ." onClose={() => setCreating(false)} busy={busy}>
      <AdminProblemEditor onBusyChange={setBusy} onSave={async (payload) => {
        await createAdminProblem(payload);
        void client.invalidateQueries({ queryKey: adminKeys.problems });
        toast.success("Đã tạo bài tập nguồn."); setCreating(false);
      }} />
    </AdminDialog>}
  </div>;
}
