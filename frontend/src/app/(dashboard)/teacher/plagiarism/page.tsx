"use client";

import { Bot } from "lucide-react";
import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { PlagiarismAlertList } from "@/components/teacher/plagiarism-alert-list";
import { usePlagiarismAlerts } from "@/lib/hooks/use-dashboard";

export default function PlagiarismPage() {
  useBreadcrumbLabel("Cảnh báo đạo văn");
  const plagiarism = usePlagiarismAlerts();

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="flex items-center gap-2.5 text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-3xl">
          <Bot className="size-8 text-[#2f226b] dark:text-indigo-300" /> Cảnh báo đạo văn & Trùng lặp mã nguồn
        </h1>
        <p className="text-muted-foreground">
          Các trường hợp AST & Token tương đồng cao được phát hiện tự động bởi UTC2 Judge Master.
        </p>
      </div>

      <div className="max-w-4xl">
        <PlagiarismAlertList
          alerts={plagiarism.data}
          isLoading={plagiarism.isPending}
          error={plagiarism.error}
          onRetry={() => void plagiarism.refetch()}
        />
      </div>
    </div>
  );
}
