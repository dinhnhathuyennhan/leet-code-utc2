"use client";

import type { ReactNode } from "react";
import { Loader2 } from "lucide-react";

import { AppShell } from "@/components/shared/app-shell";
import { useShellUser } from "@/lib/auth/use-shell-user";
import { STUDENT_NAV } from "@/lib/constants/navigation";
import { useProtectedRoute } from "@/hooks/use-route-guard";

export default function StudentLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useShellUser("student");
  const { isAllowed } = useProtectedRoute();

  if (!isAllowed) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-50">
        <Loader2 className="size-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <AppShell navItems={STUDENT_NAV} homeHref="/" user={user} onLogout={logout}>
      {children}
    </AppShell>
  );
}
