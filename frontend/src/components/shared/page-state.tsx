import { useState, type ReactNode } from "react";
import { Inbox, Loader2, RefreshCw, WifiOff, TriangleAlert, type LucideIcon } from "lucide-react";
import { ApiError } from "@/lib/api/error";

import { Button } from "@/components/ui/button";
import { getErrorMessage } from "@/lib/helpers/error-message";

interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
  className?: string;
}

/** Lỗi tải dữ liệu — hiện message từ ApiError + nút thử lại. */
export function ErrorState({ error, onRetry, className }: ErrorStateProps) {
  const [retrying, setRetrying] = useState(false);
  const retry = async () => {
    if (!onRetry || retrying) return;
    setRetrying(true);
    try { await onRetry(); } finally { setRetrying(false); }
  };
  if (error instanceof ApiError && error.isNetworkError) {
    return (
      <div role="alert" className={`flex min-h-56 flex-col items-center justify-center gap-3 rounded-xl border bg-card px-6 py-10 text-center ${className ?? ""}`}>
        <WifiOff className="size-9 text-amber-500" />
        <h2 className="text-lg font-semibold">Mất kết nối máy chủ</h2>
        <p className="max-w-md text-sm text-muted-foreground">Kiểm tra kết nối mạng rồi thử lại. Dữ liệu đang nhập trên biểu mẫu sẽ được giữ nguyên.</p>
        {onRetry && <Button onClick={() => void retry()} disabled={retrying} variant="outline" size="sm">{retrying ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Thử kết nối lại</Button>}
      </div>
    );
  }
  return (
    <div role="alert" className={`flex flex-col items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-6 py-10 text-center dark:border-red-500/30 dark:bg-red-500/10 ${className ?? ""}`}>
      <TriangleAlert className="size-8 text-red-500" />
      <p className="max-w-md text-sm font-medium text-red-700 dark:text-red-300">{getErrorMessage(error)}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="border-red-300 bg-card text-red-600 hover:bg-red-50">
          <RefreshCw className="size-4" /> Thử lại
        </Button>
      )}
    </div>
  );
}

export function ConnectionLostState({ onRetry, retrying = false }: { onRetry: () => void; retrying?: boolean }) {
  return <div role="alert" className="flex min-h-[100dvh] flex-col items-center justify-center gap-4 bg-slate-50 px-6 text-center dark:bg-slate-950"><WifiOff className="size-12 text-amber-500" /><h1 className="text-2xl font-bold">Không thể kết nối máy chủ</h1><p className="max-w-md text-sm text-muted-foreground">Bạn vẫn đang ở trang hiện tại. Khi máy chủ hoạt động trở lại, hãy thử kết nối lại để tiếp tục.</p><Button onClick={onRetry} disabled={retrying}>{retrying ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Thử lại</Button></div>;
}

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  children?: ReactNode;
}

export function EmptyState({ icon: Icon = Inbox, title, description, children }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed bg-card px-6 py-14 text-center">
      <span className="mb-1 flex size-12 items-center justify-center rounded-full bg-indigo-50 text-indigo-500 dark:bg-indigo-500/15">
        <Icon className="size-6" />
      </span>
      <p className="text-base font-semibold">{title}</p>
      {description && <p className="max-w-sm text-sm text-muted-foreground">{description}</p>}
      {children}
    </div>
  );
}
