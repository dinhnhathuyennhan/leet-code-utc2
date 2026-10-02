import type { ReactNode } from "react";
import { Inbox, RefreshCw, TriangleAlert, type LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { getErrorMessage } from "@/lib/helpers/error-message";

interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
  className?: string;
}

/** Lỗi tải dữ liệu — hiện message từ ApiError + nút thử lại. */
export function ErrorState({ error, onRetry, className }: ErrorStateProps) {
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
