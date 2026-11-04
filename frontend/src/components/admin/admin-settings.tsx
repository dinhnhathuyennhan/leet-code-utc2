"use client";

import { useState, useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { CheckCircle2, KeyRound, Loader2, Play, Server, Settings, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState } from "@/components/shared/page-state";
import { PasswordInput } from "@/components/shared/password-input";
import { useAuth } from "@/context/auth-context";
import { runAdminJudge, testAdminAIConnection, testAdminJudge } from "@/lib/api/endpoints/admin-management";
import { getErrorMessage } from "@/lib/helpers/error-message";
import { useAdminProfile } from "@/lib/hooks/use-admin";
import type { AdminAIConnection, JudgeResult } from "@/lib/types/admin";
import { changePasswordSchema } from "@/lib/validations/validate-field-form";
import { AdminDialog, AdminHeading, ADMIN_PRIMARY, ADMIN_SELECT } from "./admin-ui";

const subscribe = () => () => {};
const clientSnapshot = () => true;
const serverSnapshot = () => false;

export function AdminSettings() {
  const profile = useAdminProfile();
  const { theme, setTheme } = useTheme();
  const hydrated = useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);
  const [busy, setBusy] = useState(false);
  const [code, setCode] = useState('print("Hello UTC2")');
  const [stdin, setStdin] = useState("");
  const [result, setResult] = useState<JudgeResult | null>(null);
  const [judgeError, setJudgeError] = useState<unknown>(null);
  const [aiBusy, setAiBusy] = useState(false);
  const [aiResult, setAiResult] = useState<AdminAIConnection | null>(null);
  const [aiError, setAiError] = useState<unknown>(null);
  const [passwordOpen, setPasswordOpen] = useState(false);
  async function run(test: boolean) {
    if (busy) return;
    setBusy(true); setJudgeError(null); setResult(null);
    try {
      const response = test ? await testAdminJudge() : await runAdminJudge({ source_code: code, language_id: 71, stdin });
      setResult(response);
      toast.success("Đã nhận phản hồi từ Judge0.");
    } catch (error) { setJudgeError(error); toast.error(getErrorMessage(error)); } finally { setBusy(false); }
  }
  async function checkAI() {
    if (aiBusy) return;
    setAiBusy(true); setAiResult(null); setAiError(null);
    try { setAiResult(await testAdminAIConnection()); }
    catch (error) { setAiError(error); toast.error(getErrorMessage(error)); }
    finally { setAiBusy(false); }
  }
  return <div className="space-y-6">
    <AdminHeading title="Cấu hình & bảo mật" description="Thông tin tài khoản quản trị, tùy chọn hiển thị và công cụ kiểm tra hệ thống chấm bài." />
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="space-y-5 rounded-2xl border bg-card p-6 shadow-sm">
        <h2 className="flex items-center gap-2 font-bold"><ShieldCheck className="size-5 text-indigo-600" />Tài khoản quản trị</h2>
        {profile.error ? <ErrorState error={profile.error} onRetry={() => void profile.refetch()} /> : profile.isPending ? <p>Đang tải tài khoản...</p> :
          <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-5 gap-y-3 text-sm"><dt className="text-muted-foreground">Họ tên</dt><dd>{profile.data?.full_name}</dd><dt className="text-muted-foreground">Mã tài khoản</dt><dd className="break-all">{profile.data?.user_id}</dd><dt className="text-muted-foreground">Email</dt><dd className="break-all">{profile.data?.email}</dd><dt className="text-muted-foreground">Vai trò</dt><dd>Quản trị viên</dd></dl>}
        <Button variant="outline" onClick={() => setPasswordOpen(true)}><KeyRound className="size-4" />Đổi mật khẩu</Button>
      </section>
      <section className="space-y-5 rounded-2xl border bg-card p-6 shadow-sm">
        <h2 className="flex items-center gap-2 font-bold"><Settings className="size-5 text-indigo-600" />Giao diện</h2>
        <label className="block space-y-2 text-sm font-medium">Chế độ hiển thị<select value={hydrated ? theme ?? "system" : "system"} disabled={!hydrated} onChange={(event) => setTheme(event.target.value)} className={`${ADMIN_SELECT} w-full`}><option value="light">Sáng</option><option value="dark">Tối</option><option value="system">Theo hệ thống</option></select></label>
        <p className="text-sm text-muted-foreground">Tùy chọn hiển thị được lưu trên trình duyệt này.</p>
        <p className="rounded-xl bg-muted p-4 text-sm leading-6 text-muted-foreground">Các thiết lập dùng chung như email thông báo, chính sách nộp bài và cấu hình máy chấm hiện chưa hỗ trợ chỉnh sửa trên giao diện.</p>
      </section>
    </div>
    <section className="space-y-5 rounded-2xl border bg-card p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="flex items-center gap-2 font-bold"><Server className="size-5 text-indigo-600" />Kiểm tra máy chấm Judge0</h2><p className="mt-1 text-sm text-muted-foreground">Gửi chương trình thử để kiểm tra kết nối và kết quả chạy Python.</p></div>
        <Button variant="outline" disabled={busy} onClick={() => void run(true)}>{busy && <Loader2 className="size-4 animate-spin" />}Kiểm tra kết nối</Button></div>
      <div className="grid gap-5 lg:grid-cols-2">
        <label className="space-y-2 text-sm font-medium">Mã nguồn Python<Textarea rows={8} maxLength={20000} value={code} onChange={(event) => setCode(event.target.value)} className="font-mono text-xs" disabled={busy} /></label>
        <label className="space-y-2 text-sm font-medium">Dữ liệu đầu vào (stdin)<Textarea rows={8} maxLength={10000} value={stdin} onChange={(event) => setStdin(event.target.value)} className="font-mono text-xs" disabled={busy} /></label>
      </div>
      <Button className={ADMIN_PRIMARY} disabled={busy || !code.trim()} onClick={() => void run(false)}>{busy ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}Chạy thử</Button>
      {judgeError != null && <ErrorState error={judgeError} />}
      {result && <div className="space-y-3 rounded-xl border bg-muted/40 p-4">
        <h3 className="flex items-center gap-2 font-semibold"><CheckCircle2 className="size-4" />Kết quả: {result.status?.description ?? "Đã nhận phản hồi"}</h3>
        <dl className="space-y-3">{[["stdout", result.stdout], ["stderr", result.stderr], ["Thông báo biên dịch", result.compile_output]].map(([label, value]) => <div key={label}><dt className="mb-1 text-xs font-medium text-muted-foreground">{label}</dt><dd><pre className="overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 font-mono text-xs text-slate-100">{value || "(trống)"}</pre></dd></div>)}</dl>
        {result.time && <p className="text-xs text-muted-foreground">Thời gian: {result.time}s · Bộ nhớ: {result.memory ?? "—"} KB</p>}
      </div>}
    </section>
    <section className="space-y-4 rounded-2xl border bg-card p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="flex items-center gap-2 font-bold"><Server className="size-5 text-indigo-600" />Kiểm tra kết nối AI review</h2><p className="mt-1 text-sm text-muted-foreground">Kiểm tra Ollama và mô hình dùng để phân tích lời giải.</p></div>
        <Button variant="outline" disabled={aiBusy} onClick={() => void checkAI()}>{aiBusy && <Loader2 className="size-4 animate-spin" />}Kiểm tra kết nối</Button></div>
      {aiError != null && <ErrorState error={aiError} />}
      {aiResult && <p role="status" className={`rounded-lg p-3 text-sm ${aiResult.model_available ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-500/15" : "bg-amber-50 text-amber-800 dark:bg-amber-500/15"}`}>
        {aiResult.model_available ? "Kết nối AI thành công." : "Đã kết nối Ollama nhưng chưa tìm thấy mô hình cấu hình."} Mô hình: {aiResult.model}
      </p>}
    </section>
    {passwordOpen && <AdminPasswordDialog onClose={() => setPasswordOpen(false)} />}
  </div>;
}

function AdminPasswordDialog({ onClose }: { onClose: () => void }) {
  const auth = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    const parsed = changePasswordSchema.safeParse({ currentPassword, newPassword, confirmPassword, logoutOtherDevices: true });
    if (!parsed.success) { toast.error(parsed.error.issues[0]?.message ?? "Vui lòng kiểm tra mật khẩu."); return; }
    setBusy(true);
    try {
      await auth.changePassword({ current_password: currentPassword, new_password: newPassword, confirm_password: confirmPassword });
      toast.success("Đã đổi mật khẩu quản trị."); onClose();
    } catch (error) { toast.error(getErrorMessage(error)); } finally { setBusy(false); }
  }
  return <AdminDialog open title="Đổi mật khẩu quản trị" description="Mật khẩu mới cần ít nhất 8 ký tự, có chữ hoa, chữ số và ký tự đặc biệt (!@#$%^&*)." onClose={onClose} busy={busy}>
    <form onSubmit={(event) => void submit(event)} className="space-y-4">
      <label className="block space-y-2 text-sm font-medium">Mật khẩu hiện tại<PasswordInput autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} disabled={busy} required /></label>
      <label className="block space-y-2 text-sm font-medium">Mật khẩu mới<PasswordInput autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} disabled={busy} required /></label>
      <label className="block space-y-2 text-sm font-medium">Xác nhận mật khẩu mới<PasswordInput autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} disabled={busy} required /></label>
      <div className="flex justify-end gap-2"><Button type="button" variant="outline" disabled={busy} onClick={onClose}>Hủy</Button><Button type="submit" disabled={busy} className={ADMIN_PRIMARY}>{busy ? "Đang lưu..." : "Lưu mật khẩu"}</Button></div>
    </form>
  </AdminDialog>;
}
