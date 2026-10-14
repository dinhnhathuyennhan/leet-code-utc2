"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Download, KeyRound, Loader2, Plus, Search, Upload, Users, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiError } from "@/lib/api/error";
import { createStudent, createTeacher, listUsers, resetUserPassword } from "@/lib/api/endpoints/admin";
import type { AccountResponse, Role } from "@/lib/api/types";
import { accountsQueryKey } from "@/lib/query-client";

const PAGE_SIZE = 20;
const ACCOUNT_EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@st\.utc2\.edu\.vn$/i;
const ACCOUNT_EMAIL_MESSAGE = "Email phải có đuôi @st.utc2.edu.vn.";

type RoleFilter = "all" | "student" | "teacher";

function roleLabel(roleId: Role): string {
  return roleId === 2 ? "Giảng viên" : roleId === 3 ? "Sinh viên" : "Admin";
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.detail : fallback;
}

async function copyPassword(password: string) {
  try {
    await navigator.clipboard.writeText(password);
    toast.success("Đã sao chép mật khẩu tạm");
  } catch {
    toast.error("Không thể sao chép tự động. Vui lòng chọn và sao chép mật khẩu thủ công.");
  }
}

function AccountModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [roleId, setRoleId] = useState<2 | 3>(3);
  const [form, setForm] = useState({
    user_id: "",
    full_name: "",
    date_of_birth: "2005-01-01",
    email: "",
    class_id: "",
  });
  const [emailError, setEmailError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [created, setCreated] = useState<{ account: AccountResponse; temporaryPassword: string } | null>(null);

  function update(name: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
    if (name === "email") setEmailError("");
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting || created) return;
    if (!ACCOUNT_EMAIL_PATTERN.test(form.email)) {
      setEmailError(ACCOUNT_EMAIL_MESSAGE);
      return;
    }

    setIsSubmitting(true);
    try {
      const account = roleId === 2
        ? await createTeacher({
            user_id: form.user_id,
            full_name: form.full_name,
            date_of_birth: form.date_of_birth,
            email: form.email,
          })
        : await createStudent({ ...form });

      // POST /teachers and POST /students return UserResponse without a password.
      // These are the same rules used in backend/app/services/user_service.py.
      const [year, month, day] = form.date_of_birth.split("-");
      const temporaryPassword = roleId === 3 ? account.user_id : `${day}${month}${year}`;
      setCreated({ account, temporaryPassword });
      onCreated();
      toast.success(`Đã cấp tài khoản ${roleLabel(roleId).toLowerCase()}`);
    } catch (error) {
      toast.error(errorMessage(error, "Không thể tạo tài khoản."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div role="dialog" aria-modal="true" aria-label="Cấp phát tài khoản" className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-950/45 p-4 backdrop-blur-sm">
      <div className="my-auto w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <p className="text-lg font-bold text-slate-900 dark:text-white">Cấp phát tài khoản</p>
            <p className="text-sm text-slate-500">
              Sinh viên dùng MSSV; giảng viên dùng ngày sinh dạng ddmmyyyy làm mật khẩu tạm.
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Đóng"><X className="size-5" /></Button>
        </div>

        {created ? (
          <div>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Đã tạo tài khoản cho {created.account.full_name} ({created.account.user_id}).
              Hãy lưu mật khẩu tạm trước khi đóng cửa sổ.
            </p>
            <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">
                Mật khẩu tạm, chỉ hiển thị lần này
              </p>
              <div className="mt-3 flex items-center gap-2">
                <code className="min-w-0 flex-1 select-all overflow-x-auto rounded-lg bg-white px-3 py-2 text-lg font-bold text-slate-900">
                  {created.temporaryPassword}
                </code>
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => void copyPassword(created.temporaryPassword)}
                  aria-label="Sao chép mật khẩu tạm"
                >
                  <Copy className="size-4" />
                </Button>
              </div>
            </div>
            <div className="mt-6 flex justify-end">
              <Button onClick={onClose}>Đóng</Button>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-5 grid grid-cols-2 gap-2 rounded-xl bg-slate-100 p-1 dark:bg-slate-800">
              {[{ id: 3 as const, label: "Sinh viên" }, { id: 2 as const, label: "Giảng viên" }].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  disabled={isSubmitting}
                  onClick={() => setRoleId(item.id)}
                  className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${roleId === item.id ? "bg-white text-indigo-800 shadow-sm dark:bg-slate-700 dark:text-white" : "text-slate-500"}`}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <form onSubmit={(event) => void submit(event)} className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-1.5">
                <Label htmlFor="account-user-id">Mã tài khoản</Label>
                <Input id="account-user-id" value={form.user_id} onChange={(event) => update("user_id", event.target.value)} disabled={isSubmitting} required />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="account-name">Họ và tên</Label>
                <Input id="account-name" value={form.full_name} onChange={(event) => update("full_name", event.target.value)} disabled={isSubmitting} required />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="account-dob">Ngày sinh</Label>
                <Input id="account-dob" type="date" value={form.date_of_birth} onChange={(event) => update("date_of_birth", event.target.value)} disabled={isSubmitting} required />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="account-email">Email UTC2</Label>
                <Input
                  id="account-email"
                  type="email"
                  value={form.email}
                  onChange={(event) => update("email", event.target.value)}
                  onInvalid={() => setEmailError(ACCOUNT_EMAIL_MESSAGE)}
                  pattern="[a-zA-Z0-9._%+-]+@st[.]utc2[.]edu[.]vn"
                  title={ACCOUNT_EMAIL_MESSAGE}
                  placeholder="ten@st.utc2.edu.vn"
                  aria-invalid={Boolean(emailError)}
                  aria-describedby={emailError ? "account-email-error" : undefined}
                  disabled={isSubmitting}
                  required
                />
                {emailError && <p id="account-email-error" role="alert" className="text-xs text-red-600">{emailError}</p>}
              </div>
              {roleId === 3 && (
                <div className="grid gap-1.5 sm:col-span-2">
                  <Label htmlFor="account-class">Mã lớp hành chính</Label>
                  <Input id="account-class" placeholder="VD: CQ.64.CNTT" value={form.class_id} onChange={(event) => update("class_id", event.target.value)} disabled={isSubmitting} required />
                </div>
              )}
              <div className="flex justify-end gap-2 pt-2 sm:col-span-2">
                <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>Hủy</Button>
                <Button type="submit" disabled={isSubmitting} className="bg-[#352078] hover:bg-[#29175f]">
                  <Plus className="size-4" />{isSubmitting ? "Đang tạo..." : "Cấp phát tài khoản"}
                </Button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

function ResetPasswordModal({
  account,
  onClose,
  onReset,
}: {
  account: AccountResponse;
  onClose: () => void;
  onReset: () => void;
}) {
  const [password, setPassword] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function reset() {
    if (isSubmitting || password) return;
    setIsSubmitting(true);
    try {
      const result = await resetUserPassword(account.user_id);
      setPassword(result.temporary_password);
      onReset();
      toast.success("Đặt lại mật khẩu thành công");
    } catch (error) {
      toast.error(errorMessage(error, "Không thể đặt lại mật khẩu."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div role="dialog" aria-modal="true" aria-label="Đặt lại mật khẩu" className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-950/45 p-4 backdrop-blur-sm">
      <div className="my-auto w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-lg font-bold">Đặt lại mật khẩu</p>
            <p className="text-sm text-slate-500">{account.full_name} · {account.user_id} · {account.email}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} disabled={isSubmitting} aria-label="Đóng"><X className="size-5" /></Button>
        </div>
        {password ? (
          <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Mật khẩu tạm, chỉ hiển thị lần này</p>
            <div className="mt-3 flex items-center gap-2">
              <code className="min-w-0 flex-1 select-all overflow-x-auto rounded-lg bg-white px-3 py-2 text-lg font-bold text-slate-900">{password}</code>
              <Button type="button" variant="outline" size="icon" onClick={() => void copyPassword(password)} aria-label="Sao chép mật khẩu tạm">
                <Copy className="size-4" />
              </Button>
            </div>
          </div>
        ) : (
          <p className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            Tất cả phiên đăng nhập cũ của tài khoản này sẽ bị vô hiệu hóa. Kiểm tra đúng mã và email trước khi xác nhận.
          </p>
        )}
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>{password ? "Đóng" : "Hủy"}</Button>
          {!password && (
            <Button onClick={() => void reset()} disabled={isSubmitting} className="bg-[#352078] hover:bg-[#29175f]">
              <KeyRound className="size-4" />{isSubmitting ? "Đang xử lý..." : "Xác nhận đặt lại"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export function AccountManagement() {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<RoleFilter>("all");
  const [page, setPage] = useState(1);
  const [accountModalOpen, setAccountModalOpen] = useState(false);
  const [resetAccount, setResetAccount] = useState<AccountResponse | null>(null);
  const roleId = roleFilter === "student" ? 3 : roleFilter === "teacher" ? 2 : undefined;

  const accountsQuery = useQuery({
    queryKey: [...accountsQueryKey, "list", roleId, page],
    queryFn: () => listUsers({ role_id: roleId, page, page_size: PAGE_SIZE }),
  });
  const totalQuery = useQuery({
    queryKey: [...accountsQueryKey, "count", "all"],
    queryFn: async () => (await listUsers({ page: 1, page_size: 1 })).total,
  });
  const teacherCountQuery = useQuery({
    queryKey: [...accountsQueryKey, "count", "teacher"],
    queryFn: async () => (await listUsers({ role_id: 2, page: 1, page_size: 1 })).total,
  });
  const studentCountQuery = useQuery({
    queryKey: [...accountsQueryKey, "count", "student"],
    queryFn: async () => (await listUsers({ role_id: 3, page: 1, page_size: 1 })).total,
  });

  const accounts = accountsQuery.isError ? undefined : accountsQuery.data?.items;
  const filteredAccounts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return (accounts ?? []).filter((account) =>
      `${account.full_name} ${account.user_id} ${account.email}`.toLowerCase().includes(normalizedQuery),
    );
  }, [accounts, query]);
  const totalPages = Math.max(1, Math.ceil((accountsQuery.data?.total ?? 0) / PAGE_SIZE));

  function refreshAccounts() {
    void queryClient.invalidateQueries({ queryKey: accountsQueryKey });
  }

  function changeRoleFilter(next: RoleFilter) {
    setRoleFilter(next);
    setPage(1);
    setQuery("");
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-sm font-medium text-indigo-700">Quản trị hệ thống</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Quản lý tài khoản người dùng</h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-500">Cấp phát tài khoản, nhập danh sách hàng loạt và quản lý mật khẩu tạm.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => setAccountModalOpen(true)}><Plus className="size-4" />Cấp tài khoản</Button>
          <Link href="/admin/accounts/import"><Button className="bg-[#352078] hover:bg-[#29175f]"><Upload className="size-4" />Nhập danh sách từ Excel</Button></Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Tổng số tài khoản" value={totalQuery.data} icon={<Users className="size-5" />} tone="indigo" />
        <StatCard label="Sinh viên (Role 3)" value={studentCountQuery.data} icon={<Users className="size-5" />} tone="blue" />
        <StatCard label="Giảng viên (Role 2)" value={teacherCountQuery.data} icon={<KeyRound className="size-5" />} tone="amber" />
      </div>
      {(totalQuery.isError || teacherCountQuery.isError || studentCountQuery.isError) && (
        <p role="alert" className="text-sm text-rose-700">
          Một số số liệu tài khoản không tải được. <button type="button" className="underline" onClick={() => void queryClient.invalidateQueries({ queryKey: [...accountsQueryKey, "count"] })}>Thử lại</button>
        </p>
      )}

      <section className="overflow-hidden rounded-2xl border bg-white shadow-sm dark:bg-slate-900">
        <div className="flex flex-col gap-3 border-b p-4 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm trong trang hiện tại theo mã, họ tên hoặc email" className="pl-9" aria-label="Tìm tài khoản trong trang hiện tại" />
          </div>
          <select
            value={roleFilter}
            onChange={(event) => changeRoleFilter(event.target.value as RoleFilter)}
            className="h-9 rounded-lg border bg-white px-3 text-sm text-slate-700 dark:bg-slate-900"
            aria-label="Lọc tài khoản theo vai trò"
          >
            <option value="all">Tất cả vai trò</option>
            <option value="student">Sinh viên</option>
            <option value="teacher">Giảng viên</option>
          </select>
          <Button variant="outline" size="sm" disabled title="Chức năng xuất danh sách chưa được hỗ trợ">
            <Download className="size-4" />Xuất danh sách
          </Button>
        </div>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-[#352078] hover:bg-[#352078]">
                <TableHead className="text-white">STT</TableHead>
                <TableHead className="text-white">Họ và tên</TableHead>
                <TableHead className="text-white">Email UTC2</TableHead>
                <TableHead className="text-white">Vai trò</TableHead>
                <TableHead className="text-white">Lớp</TableHead>
                <TableHead className="text-white">Ngày sinh</TableHead>
                <TableHead className="text-right text-white">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {accountsQuery.isPending ? (
                <TableRow><TableCell colSpan={7} className="py-8 text-center text-slate-500"><Loader2 className="mr-2 inline size-4 animate-spin" />Đang tải danh sách tài khoản...</TableCell></TableRow>
              ) : accountsQuery.isError ? (
                <TableRow><TableCell colSpan={7} className="py-8 text-center text-rose-700">
                  {errorMessage(accountsQuery.error, "Không tải được danh sách tài khoản.")}{" "}
                  <button type="button" className="underline" onClick={() => void accountsQuery.refetch()}>Thử lại</button>
                </TableCell></TableRow>
              ) : filteredAccounts.length === 0 ? (
                <TableRow><TableCell colSpan={7} className="py-8 text-center text-slate-500">
                  {!accounts?.length ? "Chưa có tài khoản nào." : "Không có tài khoản khớp trong trang này."}
                </TableCell></TableRow>
              ) : filteredAccounts.map((account, index) => (
                <TableRow key={account.user_id}>
                  <TableCell className="text-slate-400">{String((page - 1) * PAGE_SIZE + index + 1).padStart(2, "0")}</TableCell>
                  <TableCell>
                    <p className="font-semibold text-slate-800 dark:text-slate-100">{account.full_name}</p>
                    <p className="text-xs text-slate-400">{account.user_id}</p>
                  </TableCell>
                  <TableCell className="text-sm text-slate-600 dark:text-slate-300">{account.email}</TableCell>
                  <TableCell>
                    <span className={`rounded-md px-2 py-1 text-xs font-semibold ${account.role_id === 2 ? "bg-indigo-100 text-indigo-700" : account.role_id === 3 ? "bg-purple-100 text-purple-700" : "bg-slate-100 text-slate-700"}`}>
                      {roleLabel(account.role_id)}
                    </span>
                  </TableCell>
                  <TableCell>{account.class_id || "—"}</TableCell>
                  <TableCell>{account.date_of_birth || "—"}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" size="sm" onClick={() => setResetAccount(account)}>
                      <KeyRound className="size-3.5" />Đặt lại MK
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-3 text-sm text-slate-500">
          <span>
            Hiển thị {filteredAccounts.length} tài khoản trong trang {page}; tổng {accountsQuery.data?.total ?? "—"}.
            {query.trim() && " Tìm kiếm chỉ áp dụng cho trang hiện tại."}
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1 || accountsQuery.isPending} onClick={() => { setPage((current) => current - 1); setQuery(""); }}>Trước</Button>
            <span>Trang {page} / {accountsQuery.isPending || accountsQuery.isError ? "—" : totalPages}</span>
            <Button variant="outline" size="sm" disabled={accountsQuery.isPending || accountsQuery.isError || page >= totalPages} onClick={() => { setPage((current) => current + 1); setQuery(""); }}>Sau</Button>
          </div>
        </div>
      </section>
      {accountModalOpen && <AccountModal onClose={() => setAccountModalOpen(false)} onCreated={refreshAccounts} />}
      {resetAccount && <ResetPasswordModal account={resetAccount} onClose={() => setResetAccount(null)} onReset={refreshAccounts} />}
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  tone,
}: {
  label: string;
  value: number | undefined;
  icon: React.ReactNode;
  tone: "indigo" | "blue" | "amber";
}) {
  const styles = {
    indigo: "bg-indigo-50 text-indigo-700",
    blue: "bg-blue-50 text-blue-700",
    amber: "bg-amber-50 text-amber-700",
  };
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide text-slate-400">{label}</p>
          <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">{value ?? "—"}</p>
        </div>
        <span className={`flex size-10 items-center justify-center rounded-xl ${styles[tone]}`}>{icon}</span>
      </div>
      <p className="mt-3 text-xs text-slate-500">Dữ liệu từ hệ thống</p>
    </div>
  );
}
