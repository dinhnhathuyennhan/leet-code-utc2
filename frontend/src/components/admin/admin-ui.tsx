"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import { Loader2, type LucideIcon } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { getErrorMessage } from "@/lib/helpers/error-message";

export const ADMIN_PRIMARY = "bg-[#352078] text-white hover:bg-[#29175f]";
export const ADMIN_SELECT = "h-10 rounded-lg border bg-background px-3 text-sm";

export function AdminHeading({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  return <header className="flex flex-wrap items-end justify-between gap-4">
    <div className="min-w-0 space-y-1">
      <p className="text-sm font-medium text-indigo-700 dark:text-indigo-300">Quản trị hệ thống</p>
      <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
      {description && <p className="max-w-3xl text-sm text-muted-foreground">{description}</p>}
    </div>
    {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
  </header>;
}

export function AdminMetric({ label, value, icon: Icon, detail }: { label: string; value: string | number | undefined; icon: LucideIcon; detail?: string }) {
  return <article className="rounded-2xl border bg-card p-5 shadow-sm">
    <div className="flex items-start justify-between gap-3">
      <div><p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className="mt-3 text-3xl font-bold">{value ?? "—"}</p></div>
      <span className="rounded-xl bg-indigo-50 p-3 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300"><Icon className="size-5" /></span>
    </div>
    {detail && <p className="mt-3 text-xs text-muted-foreground">{detail}</p>}
  </article>;
}

export function AdminLoading() {
  return <div aria-busy="true" aria-label="Đang tải dữ liệu" className="space-y-5"><Skeleton className="h-28 rounded-2xl" /><div className="grid gap-4 sm:grid-cols-3">{[1, 2, 3].map((id) => <Skeleton key={id} className="h-28 rounded-2xl" />)}</div><Skeleton className="h-72 rounded-2xl" /></div>;
}

export function AdminDialog({ title, description, open, onClose, busy, children }: {
  title: string; description: string; open: boolean; onClose: () => void; busy?: boolean; children: ReactNode;
}) {
  return <Dialog open={open} onOpenChange={(next) => { if (!next && !busy) onClose(); }}>
    <DialogContent showCloseButton={!busy} className="max-h-[90dvh] overflow-y-auto sm:max-w-2xl">
      <DialogHeader><DialogTitle>{title}</DialogTitle><DialogDescription>{description}</DialogDescription></DialogHeader>
      {children}
    </DialogContent>
  </Dialog>;
}

export function AdminConfirm({ label, title, description, onConfirm, disabled }: {
  label: string; title: string; description: string; onConfirm: () => Promise<unknown>; disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  async function confirm() {
    if (busy) return;
    setBusy(true);
    try { await onConfirm(); setOpen(false); } catch (error) { toast.error(getErrorMessage(error)); } finally { setBusy(false); }
  }
  return <><Button type="button" variant="outline" size="sm" onClick={() => setOpen(true)} disabled={disabled}>{label}</Button>
    <AdminDialog title={title} description={description} open={open} onClose={() => setOpen(false)} busy={busy}>
      <div className="flex justify-end gap-2 pt-3"><Button variant="outline" disabled={busy} onClick={() => setOpen(false)}>Hủy</Button>
        <Button variant="destructive" disabled={busy} onClick={() => void confirm()}>{busy && <Loader2 className="size-4 animate-spin" />}Xác nhận</Button></div>
    </AdminDialog></>;
}
