"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Plus, Search, Users } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { EmptyState, ErrorState } from "@/components/shared/page-state";
import { createAdminClass, deleteAdminClass } from "@/lib/api/endpoints/admin-management";
import { listUsers } from "@/lib/api/endpoints/admin";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { adminKeys, useAdminClasses } from "@/lib/hooks/use-admin";
import { AdminConfirm, AdminDialog, AdminHeading, AdminMetric, ADMIN_PRIMARY } from "./admin-ui";

export function AdminClasses() {
  const client = useQueryClient();
  const query = useAdminClasses();
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const rows = (query.data ?? []).filter((item) => `${item.class_id} ${item.department}`.toLowerCase().includes(search.trim().toLowerCase()));
  async function remove(id: string) {
    await deleteAdminClass(id);
    await client.invalidateQueries({ queryKey: adminKeys.classes });
    toast.success("Đã xóa lớp hành chính.");
  }
  return <div className="space-y-6">
    <AdminHeading title="Lớp hành chính" description="Quản lý danh mục lớp sinh hoạt và danh sách sinh viên của từng lớp."
      actions={<Button onClick={() => setCreating(true)} className={ADMIN_PRIMARY}><Plus className="size-4" />Tạo lớp hành chính</Button>} />
    <div className="grid gap-4 sm:grid-cols-3">
      <AdminMetric label="Lớp hành chính" value={query.data?.length} icon={BookOpen} />
      <AdminMetric label="Sinh viên thuộc lớp" value={query.data?.reduce((total, item) => total + item.student_count, 0)} icon={Users} />
      <AdminMetric label="Ngành / chuyên ngành" value={query.data ? new Set(query.data.map((item) => item.department)).size : undefined} icon={BookOpen} />
    </div>
    <section className="overflow-hidden rounded-2xl border bg-card shadow-sm">
      <div className="relative m-4 max-w-md"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><Input aria-label="Tìm lớp hành chính" placeholder="Tìm mã lớp hoặc ngành..." className="pl-9" value={search} onChange={(event) => setSearch(event.target.value)} /></div>
      {query.isPending ? <p className="p-10 text-center text-sm text-muted-foreground">Đang tải lớp hành chính...</p> : query.error ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : !rows.length ? <EmptyState title="Không có lớp hành chính phù hợp" /> :
        <Table className="min-w-[680px]"><TableHeader><TableRow className="bg-[#352078] hover:bg-[#352078]">{["Mã lớp", "Hệ", "Khóa", "Ngành", "Sinh viên", "Thao tác"].map((label) => <TableHead key={label} className="text-white">{label}</TableHead>)}</TableRow></TableHeader>
          <TableBody>{rows.map((item) => <TableRow key={item.class_id}>
            <TableCell className="font-semibold">{item.class_id}</TableCell><TableCell>{item.type}</TableCell><TableCell>{item.course_number}</TableCell><TableCell>{item.department}</TableCell><TableCell>{item.student_count}</TableCell>
            <TableCell><div className="flex gap-2"><Button variant="outline" size="sm" onClick={() => setSelected(item.class_id)}>Xem sinh viên</Button>
              <AdminConfirm label="Xóa lớp" title={`Xóa lớp ${item.class_id}?`} description="Chỉ lớp không có sinh viên mới được xóa." disabled={item.student_count > 0} onConfirm={() => remove(item.class_id)} /></div></TableCell>
          </TableRow>)}</TableBody></Table>}
    </section>
    {creating && <ClassForm onClose={() => setCreating(false)} />}
    {selected && <ClassRoster classId={selected} onClose={() => setSelected(null)} />}
  </div>;
}

function ClassForm({ onClose }: { onClose: () => void }) {
  const client = useQueryClient();
  const [form, setForm] = useState({ type: "CQ", course_number: "", department: "" });
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    if (!form.type.trim() || !form.department.trim() || !Number.isInteger(Number(form.course_number)) || Number(form.course_number) <= 0) { toast.error("Vui lòng nhập hệ, ngành và khóa hợp lệ."); return; }
    setBusy(true);
    try {
      await createAdminClass({ type: form.type.trim(), department: form.department.trim().normalize("NFC"), course_number: Number(form.course_number) });
      await client.invalidateQueries({ queryKey: adminKeys.classes });
      toast.success("Đã tạo lớp hành chính."); onClose();
    } catch (error) { toast.error(getErrorMessage(error)); } finally { setBusy(false); }
  }
  return <AdminDialog open title="Tạo lớp hành chính" description="Mã lớp được ghép từ hệ, khóa và ngành." onClose={onClose} busy={busy}>
    <form onSubmit={(event) => void submit(event)} className="space-y-4">
      <fieldset disabled={busy} className="grid gap-4 sm:grid-cols-3">
        <label className="space-y-2 text-sm font-medium">Hệ đào tạo<Input value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value })} placeholder="CQ" required /></label>
        <label className="space-y-2 text-sm font-medium">Khóa<Input type="number" min={1} step={1} value={form.course_number} onChange={(event) => setForm({ ...form, course_number: event.target.value })} placeholder="67" required /></label>
        <label className="space-y-2 text-sm font-medium">Ngành<Input value={form.department} onChange={(event) => setForm({ ...form, department: event.target.value })} placeholder="CNTT" required /></label>
      </fieldset>
      <p className="rounded-lg bg-muted p-3 text-sm">Mã lớp dự kiến: <strong>{form.type.trim() || "…"}.{form.course_number || "…"}.{form.department.trim() || "…"}</strong></p>
      <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={onClose} disabled={busy}>Hủy</Button><Button type="submit" className={ADMIN_PRIMARY} disabled={busy}>{busy ? "Đang tạo..." : "Tạo lớp"}</Button></div>
    </form>
  </AdminDialog>;
}

function ClassRoster({ classId, onClose }: { classId: string; onClose: () => void }) {
  const [page, setPage] = useState(1);
  const query = useQuery({ queryKey: [...adminKeys.classes, classId, "students", page], queryFn: () => listUsers({ class_id: classId, role_id: 3, page, page_size: 20 }) });
  return <AdminDialog open title={`Sinh viên lớp ${classId}`} description="Danh sách tài khoản sinh viên thuộc lớp hành chính." onClose={onClose}>
    {query.isPending ? <p>Đang tải sinh viên...</p> : query.error ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : !query.data?.items.length ? <EmptyState title="Lớp chưa có sinh viên" /> :
      <><Table><TableHeader><TableRow><TableHead>MSSV</TableHead><TableHead>Họ tên</TableHead><TableHead>Email</TableHead></TableRow></TableHeader><TableBody>{query.data.items.map((user) => <TableRow key={user.user_id}><TableCell>{user.user_id}</TableCell><TableCell>{user.full_name}</TableCell><TableCell>{user.email}</TableCell></TableRow>)}</TableBody></Table>
        <div className="flex items-center justify-between gap-2 text-sm"><Button variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)}>Trước</Button><span>Trang {page} · Tổng {query.data.total} sinh viên</span><Button variant="outline" disabled={page * 20 >= query.data.total} onClick={() => setPage(page + 1)}>Sau</Button></div></>}
  </AdminDialog>;
}
