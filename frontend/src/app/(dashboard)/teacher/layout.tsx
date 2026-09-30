"use client";

import type { ReactNode } from "react";

import { AppShell } from "@/components/shared/app-shell";
import { useShellUser } from "@/lib/hooks/use-shell-user";
import { TEACHER_NAV } from "@/lib/constants/navigation";

export default function TeacherLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useShellUser("teacher");

  return (
    <AppShell navItems={TEACHER_NAV} homeHref="/teacher" user={user} onLogout={logout}>
      {children}
    </AppShell>
  );
}
