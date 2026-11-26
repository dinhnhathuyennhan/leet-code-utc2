"use client";

// Thao tác quản lý tài khoản dùng chung cho Admin (trang Quản lý tài khoản) và
// Giáo viên (danh sách sinh viên của lớp học phần):
//  - Badge trạng thái khoá (`is_active`).
//  - Hộp xác nhận Khoá / Mở khoá → POST /users/{user_id}/lock | /unlock.
//  - Hộp sửa thông tin → PATCH /users/{user_id}.
// Quyền thật sự do backend quyết định (docs/api-design-auth.md); giao diện chỉ ẩn nút ở
// những tài khoản chắc chắn không được phép, lỗi 403 `NOT_ALLOWED_TO_MANAGE_ACCOUNT`
// (vd: GV mở khoá tài khoản do Admin khoá) hiện bằng toast với message của backend.

import { useState } from "react";
import { Loader2, Lock, LockOpen, Save } from "lucide-react";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/error";
import { lockUser, unlockUser, updateUser } from "@/lib/api/endpoints/admin";
import { Role, type AccountResponse, type UpdateUserRequest } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const UTC2_EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@st\.utc2\.edu\.vn$/i;
const STUDENT_CODE_PATTERN = /^[0-9]{10}$/;

/** Tài khoản đích của thao tác — đủ cho cả `AccountResponse` lẫn dòng ghi danh của lớp. */
export interface ManagedAccount {
  user_id: string;
  full_name: string;
  email: string;
  role_id: Role;
  student_code?: string | null;
  class_id?: string | null;
  /** `false` = đang bị khoá; `undefined`/`null` coi như đang hoạt động. */
  is_active?: boolean | null;
}

export function isAccountLocked(account: { is_active?: boolean | null }): boolean {
  return account.is_active === false;
}

/**
 * Admin chỉ quản lý (sửa/khoá) Giáo viên và Sinh viên — whitelist theo vai trò đích,
 * không tự khoá chính mình, không đụng Admin khác hay vai trò lạ.
 */
export function adminCanManage(account: { role_id: number; user_id: string }, currentUserId: string | undefined): boolean {
  return account.user_id !== currentUserId && (account.role_id === Role.TEACHER || account.role_id === Role.STUDENT);
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.detail : fallback;
}

export function AccountStatusBadge({
  isActive,
  showActive = false,
  className,
}: {
  isActive: boolean | null | undefined;
  /** Hiện cả badge "Hoạt động" (bảng có cột Trạng thái). Mặc định chỉ hiện khi bị khoá. */
  showActive?: boolean;
  className?: string;
}) {
  if (isActive === false) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 whitespace-nowrap rounded-md bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700",
          className,
        )}
      >
        <Lock className="size-3" aria-hidden="true" />
        Đã khoá
      </span>
    );
  }
  if (!showActive) return null;
  return (
    <span
      className={cn(
        "inline-flex items-center whitespace-nowrap rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700",
        className,
      )}
    >
      Hoạt động
    </span>
  );
}

/** Nút Khoá / Mở khoá theo trạng thái hiện tại; mở hộp xác nhận qua `onClick`. */
export function AccountLockButton({
  account,
  onClick,
  size = "sm",
}: {
  account: ManagedAccount;
  onClick: () => void;
  size?: "sm" | "icon-sm";
}) {
  const locked = isAccountLocked(account);
  const label = locked ? "Mở khoá" : "Khoá";
  const Icon = locked ? LockOpen : Lock;
  if (size === "icon-sm") {
    return (
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onClick}
        aria-label={`${label} tài khoản ${account.full_name}`}
        title={`${label} tài khoản`}
        className={locked ? "text-emerald-700" : "text-rose-700"}
      >
        <Icon className="size-4" />
      </Button>
    );
  }
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onClick}
      aria-label={`${label} tài khoản ${account.full_name}`}
      className={locked ? "text-emerald-700" : "text-rose-700"}
    >
      <Icon className="size-3.5" />
      {label}
    </Button>
  );
}

/**
 * Hộp xác nhận khoá/mở khoá. `account = null` → đóng.
 * `onChanged` được gọi sau khi request kết thúc (thành công hoặc lỗi) để refetch danh sách,
 * vì trạng thái trên màn hình có thể đã cũ (người khác vừa khoá/mở khoá) — trừ khi chính
 * người thao tác vừa bị khoá (`ACCOUNT_LOCKED`): phiên đã kết thúc, không gọi thêm API.
 */
export function AccountLockDialog({
  account,
  onClose,
  onChanged,
}: {
  account: ManagedAccount | null;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [submitting, setSubmitting] = useState(false);
  // Giữ tài khoản cuối cùng để nội dung không đổi trong lúc hộp đang đóng (animation).
  const [shown, setShown] = useState<ManagedAccount | null>(account);
  if (account && account !== shown) setShown(account);
  const target = account ?? shown;
  const locked = target ? isAccountLocked(target) : false;

  async function confirm() {
    if (!account || submitting) return;
    let sessionEnded = false;
    setSubmitting(true);
    try {
      if (locked) {
        await unlockUser(account.user_id);
        toast.success(`Đã mở khoá tài khoản ${account.full_name}`);
      } else {
        await lockUser(account.user_id);
        toast.success(`Đã khoá tài khoản ${account.full_name}`);
      }
      onClose();
    } catch (error) {
      sessionEnded = error instanceof ApiError && error.code === "ACCOUNT_LOCKED";
      toast.error(errorMessage(error, locked ? "Không thể mở khoá tài khoản." : "Không thể khoá tài khoản."));
      onClose();
    } finally {
      setSubmitting(false);
      if (!sessionEnded) onChanged();
    }
  }

  return (
    <AlertDialog
      open={Boolean(account)}
      onOpenChange={(next) => {
        if (!next && !submitting) onClose();
      }}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{locked ? "Mở khoá tài khoản" : "Khoá tài khoản"}</AlertDialogTitle>
          <AlertDialogDescription>
            {locked ? (
              <>
                Mở khoá tài khoản <strong>{target?.full_name}</strong>
                {target?.student_code ? ` (${target.student_code})` : ""}? Người dùng phải đăng nhập lại
                từ đầu sau khi được mở khoá.
              </>
            ) : (
              <>
                Khoá tài khoản <strong>{target?.full_name}</strong>
                {target?.student_code ? ` (${target.student_code})` : ""}? Tài khoản sẽ bị đăng xuất khỏi
                mọi thiết bị và không đăng nhập được cho đến khi được mở khoá.
              </>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={submitting}>Huỷ</AlertDialogCancel>
          <AlertDialogAction
            disabled={submitting}
            variant={locked ? "default" : "destructive"}
            onClick={(event) => {
              event.preventDefault();
              void confirm();
            }}
          >
            {submitting && <Loader2 className="size-4 animate-spin" />}
            {submitting ? "Đang xử lý..." : locked ? "Xác nhận mở khoá" : "Xác nhận khoá"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

function normalizeName(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

/** Chỉ gửi field thực sự đổi và hợp với vai trò của tài khoản đích (tránh 422 `FIELD_NOT_EDITABLE`). */
export function buildUpdatePayload(
  account: ManagedAccount,
  form: { full_name: string; email: string; student_code: string; class_id: string },
): UpdateUserRequest {
  const payload: UpdateUserRequest = {};
  const fullName = normalizeName(form.full_name);
  if (fullName !== account.full_name) payload.full_name = fullName;
  if (account.role_id === Role.STUDENT) {
    const studentCode = form.student_code.trim();
    const classId = form.class_id.trim();
    if (studentCode !== (account.student_code ?? "")) payload.student_code = studentCode;
    if (classId !== (account.class_id ?? "")) payload.class_id = classId;
  } else {
    const email = form.email.trim();
    if (email !== account.email) payload.email = email;
  }
  return payload;
}

function EditAccountForm({
  account,
  onClose,
  onSaved,
  onSavingChange,
}: {
  account: ManagedAccount;
  onClose: () => void;
  onSaved: (updated: AccountResponse) => void;
  onSavingChange: (saving: boolean) => void;
}) {
  const isStudent = account.role_id === Role.STUDENT;
  const [form, setForm] = useState({
    full_name: account.full_name,
    email: account.email,
    student_code: account.student_code ?? "",
    class_id: account.class_id ?? "",
  });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSavingState] = useState(false);
  function setSaving(next: boolean) {
    setSavingState(next);
    onSavingChange(next);
  }

  function update(name: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
    setError(null);
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    if (!normalizeName(form.full_name)) return setError("Họ và tên không được để trống.");
    if (isStudent && !STUDENT_CODE_PATTERN.test(form.student_code.trim()))
      return setError("Mã sinh viên phải gồm đúng 10 chữ số.");
    if (isStudent && !form.class_id.trim()) return setError("Mã lớp không được trống.");
    if (!isStudent && !UTC2_EMAIL_PATTERN.test(form.email.trim()))
      return setError("Email phải có đuôi @st.utc2.edu.vn.");

    const payload = buildUpdatePayload(account, form);
    if (Object.keys(payload).length === 0) {
      toast.info("Không có thay đổi nào.");
      onClose();
      return;
    }
    setSaving(true);
    try {
      const updated = await updateUser(account.user_id, payload);
      toast.success(`Đã cập nhật tài khoản ${updated.full_name}`);
      onSaved(updated);
      onClose();
    } catch (err) {
      const message = errorMessage(err, "Không thể cập nhật tài khoản.");
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={(event) => void submit(event)} className="grid gap-4" noValidate>
      <div className="grid gap-1.5">
        <Label htmlFor="edit-account-name">Họ và tên</Label>
        <Input
          id="edit-account-name"
          value={form.full_name}
          onChange={(event) => update("full_name", event.target.value)}
          disabled={saving}
          required
        />
      </div>
      {isStudent ? (
        <>
          <div className="grid gap-1.5">
            <Label htmlFor="edit-account-student-code">Mã sinh viên (MSSV)</Label>
            <Input
              id="edit-account-student-code"
              value={form.student_code}
              onChange={(event) => update("student_code", event.target.value.replace(/\D/g, ""))}
              inputMode="numeric"
              maxLength={10}
              disabled={saving}
              required
            />
            <p className="text-xs text-muted-foreground">
              Email tự đổi theo MSSV: {form.student_code.trim() || "<MSSV>"}@st.utc2.edu.vn
            </p>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="edit-account-class">Mã lớp hành chính</Label>
            <Input
              id="edit-account-class"
              value={form.class_id}
              onChange={(event) => update("class_id", event.target.value)}
              placeholder="VD: CQ.64.CNTT"
              disabled={saving}
              required
            />
          </div>
        </>
      ) : (
        <div className="grid gap-1.5">
          <Label htmlFor="edit-account-email">Email UTC2</Label>
          <Input
            id="edit-account-email"
            type="email"
            value={form.email}
            onChange={(event) => update("email", event.target.value)}
            placeholder="ten@st.utc2.edu.vn"
            disabled={saving}
            required
          />
          <p className="text-xs text-muted-foreground">Từ lần đăng nhập sau phải dùng email mới.</p>
        </div>
      )}
      {error && (
        <p role="alert" className="text-sm text-rose-700">
          {error}
        </p>
      )}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onClose} disabled={saving}>
          Huỷ
        </Button>
        <Button type="submit" disabled={saving} className="bg-[#352078] text-white hover:bg-[#29175f]">
          {saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
          {saving ? "Đang lưu..." : "Lưu thay đổi"}
        </Button>
      </div>
    </form>
  );
}

/** Hộp sửa thông tin tài khoản (PATCH /users/{user_id}). `account = null` → đóng. */
export function EditAccountDialog({
  account,
  onClose,
  onSaved,
}: {
  account: ManagedAccount | null;
  onClose: () => void;
  onSaved: (updated: AccountResponse) => void;
}) {
  // Đang lưu thì không cho đóng (Esc/click ngoài), để lỗi trả về còn form mà sửa tiếp.
  const [saving, setSaving] = useState(false);
  return (
    <Dialog
      open={Boolean(account)}
      onOpenChange={(next) => {
        if (!next && !saving) onClose();
      }}
    >
      <DialogContent className="sm:max-w-md" showCloseButton={!saving}>
        <DialogHeader>
          <DialogTitle>Sửa thông tin tài khoản</DialogTitle>
          <DialogDescription>
            {account?.role_id === Role.STUDENT
              ? "Sinh viên: sửa họ tên, MSSV và lớp hành chính."
              : "Sửa họ tên và email."}
          </DialogDescription>
        </DialogHeader>
        {/* key: mở cho tài khoản khác thì form nạp lại từ đầu */}
        {account && <EditAccountForm key={account.user_id} account={account} onClose={onClose} onSaved={onSaved} onSavingChange={setSaving} />}
      </DialogContent>
    </Dialog>
  );
}
