"use client";

import type { ReactNode } from "react";

import { AppShell } from "@/components/shared/app-shell";
import { useShellUser } from "@/lib/hooks/use-shell-user";
import { STUDENT_NAV } from "@/lib/constants/navigation";

export default function StudentLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useShellUser("student");

  return (
    <AppShell navItems={STUDENT_NAV} homeHref="/" user={user} onLogout={logout}>
      {children}
    </AppShell>
  );
}
