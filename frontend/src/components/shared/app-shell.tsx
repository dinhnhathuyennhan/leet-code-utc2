"use client";

import { useState, type ReactNode } from "react";

import { BackToTop } from "@/components/shared/back-to-top";
import { BreadcrumbProvider } from "@/components/shared/breadcrumb-context";
import { Sidebar } from "@/components/shared/Sidebar";
import { Topbar } from "@/components/shared/top-bar";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";
import type { ShellUser } from "@/lib/hooks/use-shell-user";
import type { NavItem } from "@/lib/constants/navigation";

interface AppShellProps {
  navItems: NavItem[];
  homeHref: string;
  user: ShellUser;
  onLogout: () => void;
  children: ReactNode;
}

/**
 * Khung dùng chung cho mọi màn hình sau đăng nhập (giảng viên + sinh viên).
 * Đặt trong layout.tsx nên sidebar/topbar không bị mount lại khi chuyển trang.
 */
export function AppShell({ navItems, homeHref, user, onLogout, children }: AppShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <BreadcrumbProvider>
      <div className="min-h-dvh bg-[#f3f4f9] dark:bg-slate-950">
        <aside className="fixed inset-y-0 left-0 z-30 hidden w-[16.6667vw] border-r bg-card lg:block">
          <Sidebar navItems={navItems} user={user} onLogout={onLogout} />
        </aside>

        <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
          <SheetContent side="left" className="w-[min(82vw,280px)] p-0 [&>button]:hidden">
            <SheetTitle className="sr-only">Menu điều hướng</SheetTitle>
            <SheetDescription className="sr-only">Chọn mục cần truy cập</SheetDescription>
            <Sidebar navItems={navItems} user={user} onLogout={onLogout} onNavigate={() => setMenuOpen(false)} />
          </SheetContent>
        </Sheet>

        <div className="lg:pl-[16.6667vw]">
          <Topbar homeHref={homeHref} onMenuClick={() => setMenuOpen(true)} onLogout={onLogout} />
          <main className="w-full p-4 sm:p-6 lg:p-6">{children}</main>
        </div>

        <BackToTop />
      </div>
    </BreadcrumbProvider>
  );
}
