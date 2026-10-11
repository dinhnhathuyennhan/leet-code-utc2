"use client";

import type { ReactNode } from "react";

import { AppShell } from "@/components/shared/app-shell";
import { ADMIN_NAV } from "@/lib/constants/navigation";
import { useShellUser } from "@/lib/hooks/use-shell-user";

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useShellUser("admin");
  return <AppShell navItems={ADMIN_NAV} homeHref="/admin/dashboard" user={user} onLogout={logout}>{children}</AppShell>;
}
