"use client";

import type { ReactNode } from "react";

import { AppShell } from "@/components/shared/app-shell";
import { useShellUser } from "@/lib/hooks/use-shell-user";
import { STUDENT_NAV } from "@/lib/constants/navigation";

/**
 * Layout chung cho toàn bộ `/student/*` — đăng ký AppShell với STUDENT_NAV.
 *
 * - `/student/classes/*` cũng được wrap (AppShell hiển thị ổn định trên
 *   mọi trang con của Student).
 * - Trang chủ sinh viên (`/`) vẫn dùng layout riêng của `app/(dashboard)/layout.tsx`.
 */
export default function StudentLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useShellUser("student");

  return (
    <AppShell navItems={STUDENT_NAV} homeHref="/student/dashboard" user={user} onLogout={logout}>
      {children}
    </AppShell>
  );
}
