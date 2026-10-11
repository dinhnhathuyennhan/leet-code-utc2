"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Copy, Download, KeyRound, Plus, Search, Upload, Users, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiError } from "@/lib/api/error";
import { createStudent, createTeacher, resetUserPassword } from "@/lib/api/endpoints/admin";
import type { AccountResponse, Role } from "@/lib/api/types";

type AccountRow = AccountResponse & { status: "active" | "must-change"; version: string; createdAt: string };

const ACCOUNT_EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@st\.utc2\.edu\.vn$/i;
const ACCOUNT_EMAIL_MESSAGE = "Email phải có đuôi @st.utc2.edu.vn.";

const DEMO_ACCOUNTS: AccountRow[] = [
  { user_id: "21112012", full_name: "Nguyễn Văn An", email: "21112012@sv.utc2.edu.vn", role_id: 3, date_of_birth: "2004-11-21", class_id: "CQ.64.CNTT", status: "active", version: "v2", createdAt: "10/09/2023" },
  { user_id: "21112002", full_name: "Trần Bảo Bình", email: "21112002@sv.utc2.edu.vn", role_id: 3, date_of_birth: "2004-06-20", class_id: "CQ.64.CNTT", status: "must-change", version: "v1", createdAt: "15/08/2024" },
  { user_id: "21112004", full_name: "Lê Hoàng Quân", email: "21112004@sv.utc2.edu.vn", role_id: 3, date_of_birth: "2004-03-12", class_id: "CQ.64.KTPM", status: "active", version: "v1", createdAt: "20/08/2024" },
  { user_id: "21112007", full_name: "Phạm Đức Duy", email: "21112007@sv.utc2.edu.vn", role_id: 3, date_of_birth: "2004-01-06", class_id: "CQ.64.CNTT", status: "must-change", version: "v1", createdAt: "20/08/2024" },
  { user_id: "gv001", full_name: "Trần Hoàng Nam", email: "nam.tran@utc2.edu.vn", role_id: 2, date_of_birth: "1988-01-01", status: "active", version: "v3", createdAt: "21/08/2024" },
];

function roleLabel(roleId: Role): string {
  return roleId === 2 ? "Giảng viên" : roleId === 3 ? "Sinh viên" : "Admin";
}

function AccountModal({ onClose, onCreated }: { onClose: () => void; onCreated: (account: AccountResponse) => void }) {
  const [roleId, setRoleId] = useState<2 | 3>(3);
  const [form, setForm] = useState({ user_id: "", full_name: "", date_of_birth: "2005-01-01", email: "", class_id: "" });
  const [emailError, setEmailError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function update(name: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
    if (name === "email") setEmailError("");
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!ACCOUNT_EMAIL_PATTERN.test(form.email)) {
      setEmailError(ACCOUNT_EMAIL_MESSAGE);
      return;
    }
    setIsSubmitting(true);
    try {
      const account = roleId === 2
        ? await createTeacher({ user_id: form.user_id, full_name: form.full_name, date_of_birth: form.date_of_birth, email: form.email })
        : await createStudent({ ...form });
      onCreated(account);
      toast.success(`Đã cấp tài khoản ${roleLabel(roleId).toLowerCase()}`);
      onClose();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Không thể tạo tài khoản.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm">
      <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div><p className="text-lg font-bold text-slate-900 dark:text-white">Cấp phát tài khoản</p><p className="text-sm text-slate-500">Mật khẩu tạm sẽ được sinh tự động từ ngày sinh.</p></div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Đóng"><X className="size-5" /></Button>
        </div>
        <div className="mb-5 grid grid-cols-2 gap-2 rounded-xl bg-slate-100 p-1 dark:bg-slate-800">
          {[{ id: 3 as const, label: "Sinh viên" }, { id: 2 as const, label: "Giảng viên" }].map((item) => (
            <button key={item.id} type="button" onClick={() => setRoleId(item.id)} className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${roleId === item.id ? "bg-white text-indigo-800 shadow-sm dark:bg-slate-700 dark:text-white" : "text-slate-500"}`}>{item.label}</button>
          ))}
        </div>
        <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
          <div className="grid gap-1.5"><Label htmlFor="account-user-id">Mã tài khoản</Label><Input id="account-user-id" value={form.user_id} onChange={(e) => update("user_id", e.target.value)} required /></div>
          <div className="grid gap-1.5"><Label htmlFor="account-name">Họ và tên</Label><Input id="account-name" value={form.full_name} onChange={(e) => update("full_name", e.target.value)} required /></div>
          <div className="grid gap-1.5"><Label htmlFor="account-dob">Ngày sinh</Label><Input id="account-dob" type="date" value={form.date_of_birth} onChange={(e) => update("date_of_birth", e.target.value)} required /></div>
          <div className="grid gap-1.5"><Label htmlFor="account-email">Email UTC2</Label><Input id="account-email" type="email" value={form.email} onChange={(e) => update("email", e.target.value)} onInvalid={() => setEmailError(ACCOUNT_EMAIL_MESSAGE)} pattern="[a-zA-Z0-9._%+-]+@st[.]utc2[.]edu[.]vn" title={ACCOUNT_EMAIL_MESSAGE} placeholder="ten@st.utc2.edu.vn" aria-invalid={Boolean(emailError)} aria-describedby={emailError ? "account-email-error" : undefined} required />{emailError && <p id="account-email-error" role="alert" className="text-xs text-red-600">{emailError}</p>}</div>
          {roleId === 3 && <div className="grid gap-1.5 sm:col-span-2"><Label htmlFor="account-class">Mã lớp hành chính</Label><Input id="account-class" placeholder="VD: CQ.64.CNTT" value={form.class_id} onChange={(e) => update("class_id", e.target.value)} required /></div>}
          <div className="flex justify-end gap-2 pt-2 sm:col-span-2"><Button type="button" variant="outline" onClick={onClose}>Hủy</Button><Button type="submit" disabled={isSubmitting} className="bg-[#352078] hover:bg-[#29175f]"><Plus className="size-4" />{isSubmitting ? "Đang tạo..." : "Cấp phát tài khoản"}</Button></div>
        </form>
      </div>
    </div>
  );
}

function ResetPasswordModal({ account, onClose }: { account: AccountRow; onClose: () => void }) {
  const [password, setPassword] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function reset() {
    setIsSubmitting(true);
    try {
      const result = await resetUserPassword(account.user_id);
      setPassword(result.temporary_password);
      toast.success("Đặt lại mật khẩu thành công");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.detail : "Không thể đặt lại mật khẩu.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function copyPassword() {
    if (!password) return;
    await navigator.clipboard.writeText(password);
    toast.success("Đã sao chép mật khẩu tạm");
  }

  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-sm"><div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900"><div className="flex items-start justify-between"><div><p className="text-lg font-bold">Đặt lại mật khẩu</p><p className="text-sm text-slate-500">{account.full_name} · {account.user_id}</p></div><Button variant="ghost" size="icon" onClick={onClose} aria-label="Đóng"><X className="size-5" /></Button></div>{password ? <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Mật khẩu tạm, chỉ hiển thị một lần</p><div className="mt-3 flex items-center gap-2"><code className="flex-1 rounded-lg bg-white px-3 py-2 text-lg font-bold text-slate-900">{password}</code><Button type="button" variant="outline" size="icon" onClick={() => void copyPassword()} aria-label="Sao chép"><Copy className="size-4" /></Button></div></div> : <p className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">Tất cả phiên đăng nhập cũ của tài khoản sẽ bị vô hiệu hóa.</p>}<div className="mt-6 flex justify-end gap-2"><Button variant="outline" onClick={onClose}>{password ? "Đóng" : "Hủy"}</Button>{!password && <Button onClick={() => void reset()} disabled={isSubmitting} className="bg-[#352078] hover:bg-[#29175f]"><KeyRound className="size-4" />{isSubmitting ? "Đang xử lý..." : "Xác nhận đặt lại"}</Button>}</div></div></div>;
}

export function AccountManagement() {
  const [accounts, setAccounts] = useState(DEMO_ACCOUNTS);
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<"all" | "student" | "teacher">("all");
  const [accountModalOpen, setAccountModalOpen] = useState(false);
  const [resetAccount, setResetAccount] = useState<AccountRow | null>(null);
  const filteredAccounts = useMemo(() => accounts.filter((account) => {
    const matchesQuery = `${account.full_name} ${account.user_id} ${account.email}`.toLowerCase().includes(query.toLowerCase());
    const matchesRole = roleFilter === "all" || (roleFilter === "student" ? account.role_id === 3 : account.role_id === 2);
    return matchesQuery && matchesRole;
  }), [accounts, query, roleFilter]);

  function addAccount(account: AccountResponse) {
    setAccounts((current) => [{ ...account, status: "must-change", version: "v1", createdAt: new Date().toLocaleDateString("vi-VN") }, ...current]);
  }

  return <div className="space-y-6"><div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end"><div><p className="text-sm font-medium text-indigo-700">Quản trị hệ thống</p><h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Quản lý tài khoản người dùng</h1><p className="mt-1 max-w-2xl text-sm text-slate-500">Cấp phát tài khoản, nhập danh sách hàng loạt và quản lý mật khẩu tạm.</p></div><div className="flex flex-wrap gap-2"><Button variant="outline" onClick={() => setAccountModalOpen(true)}><Plus className="size-4" />Cấp tài khoản</Button><Link href="/admin/accounts/import"><Button className="bg-[#352078] hover:bg-[#29175f]"><Upload className="size-4" />Nhập danh sách từ Excel</Button></Link></div></div>
    <div className="grid gap-4 md:grid-cols-3"><StatCard label="Tổng số tài khoản" value={accounts.length + 179} icon={<Users className="size-5" />} tone="indigo" /><StatCard label="Sinh viên (Role 3)" value={accounts.filter((a) => a.role_id === 3).length + 161} icon={<Users className="size-5" />} tone="blue" /><StatCard label="Giảng viên (Role 2)" value={accounts.filter((a) => a.role_id === 2).length + 13} icon={<KeyRound className="size-5" />} tone="amber" /></div>
    <section className="overflow-hidden rounded-2xl border bg-white shadow-sm dark:bg-slate-900"><div className="flex flex-col gap-3 border-b p-4 lg:flex-row lg:items-center"><div className="relative flex-1"><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm theo mã, họ tên hoặc email" className="pl-9" /></div><select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value as typeof roleFilter)} className="h-9 rounded-lg border bg-white px-3 text-sm text-slate-700 dark:bg-slate-900"><option value="all">Tất cả vai trò</option><option value="student">Sinh viên</option><option value="teacher">Giảng viên</option></select><Button variant="outline" size="sm"><Download className="size-4" />Xuất danh sách</Button></div><Table><TableHeader><TableRow className="bg-[#352078] hover:bg-[#352078]"><TableHead className="text-white">STT</TableHead><TableHead className="text-white">Họ và tên</TableHead><TableHead className="text-white">Email UTC2</TableHead><TableHead className="text-white">Vai trò</TableHead><TableHead className="text-white">Trạng thái</TableHead><TableHead className="text-white">Phiên đăng nhập</TableHead><TableHead className="text-right text-white">Thao tác</TableHead></TableRow></TableHeader><TableBody>{filteredAccounts.map((account, index) => <TableRow key={account.user_id}><TableCell className="text-slate-400">{String(index + 1).padStart(2, "0")}</TableCell><TableCell><p className="font-semibold text-slate-800 dark:text-slate-100">{account.full_name}</p><p className="text-xs text-slate-400">{account.user_id}</p></TableCell><TableCell className="text-sm text-slate-600 dark:text-slate-300">{account.email}</TableCell><TableCell><span className={`rounded-md px-2 py-1 text-xs font-semibold ${account.role_id === 2 ? "bg-indigo-100 text-indigo-700" : "bg-purple-100 text-purple-700"}`}>{roleLabel(account.role_id)}</span></TableCell><TableCell><span className={`rounded-md px-2 py-1 text-xs font-semibold ${account.status === "active" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>{account.status === "active" ? "Đã kích hoạt" : "Chưa đổi MK"}</span></TableCell><TableCell><span className="rounded bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{account.version}</span></TableCell><TableCell className="text-right"><Button variant="outline" size="sm" onClick={() => setResetAccount(account)}><KeyRound className="size-3.5" />Đặt lại MK</Button></TableCell></TableRow>)}</TableBody></Table><div className="flex items-center justify-between border-t px-4 py-3 text-sm text-slate-500"><span>Hiển thị {filteredAccounts.length} tài khoản mẫu; API danh sách tài khoản đang chờ backend.</span><span>Trang 1 / 1</span></div></section>{accountModalOpen && <AccountModal onClose={() => setAccountModalOpen(false)} onCreated={addAccount} />}{resetAccount && <ResetPasswordModal account={resetAccount} onClose={() => setResetAccount(null)} />}</div>;
}

function StatCard({ label, value, icon, tone }: { label: string; value: number; icon: React.ReactNode; tone: "indigo" | "blue" | "amber" }) {
  const styles = { indigo: "bg-indigo-50 text-indigo-700", blue: "bg-blue-50 text-blue-700", amber: "bg-amber-50 text-amber-700" };
  return <div className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900"><div className="flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-wide text-slate-400">{label}</p><p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">{value}</p></div><span className={`flex size-10 items-center justify-center rounded-xl ${styles[tone]}`}>{icon}</span></div><p className="mt-3 text-xs text-emerald-600">● Dữ liệu hiển thị theo phiên quản trị</p></div>;
}
