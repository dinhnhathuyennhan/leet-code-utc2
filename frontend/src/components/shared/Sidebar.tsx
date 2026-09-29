"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { NavItem } from "@/lib/constants/navigation";
import type { ShellUser } from "@/lib/hooks/use-shell-user";
import { getInitial } from "@/lib/helpers/format";
import { cn } from "@/lib/utils";

interface SidebarProps {
  navItems: NavItem[];
  user: ShellUser;
  onLogout: () => void;
  /** Gọi khi bấm một mục — dùng để đóng menu trên mobile. */
  onNavigate?: () => void;
}

function isActive(pathname: string, item: NavItem): boolean {
  if (pathname === item.href) return true;
  if (item.alsoMatch?.some((prefix) => pathname.startsWith(prefix))) return true;
  return !item.exact && pathname.startsWith(`${item.href}/`);
}

export function Sidebar({ navItems, user, onLogout, onNavigate }: SidebarProps) {
  const pathname = usePathname();

  return (
    <div className="flex h-full flex-col bg-card">
      <div className="flex h-16 shrink-0 items-center gap-3 border-b px-5">
        <Image src="/images/code-logo.svg" alt="" width={44} height={44} className="h-10 w-auto" />
        <div className="min-w-0 leading-tight">
          <p className="truncate text-base font-bold tracking-tight text-indigo-950 dark:text-indigo-200">
            UTC2 JUDGE MASTER
          </p>
          <p className="truncate text-xs text-muted-foreground">Hệ Thống Đánh Giá Lập Trình</p>
        </div>
      </div>

      <nav aria-label="Điều hướng chính" className="flex-1 space-y-1.5 overflow-y-auto p-4">
        {navItems.map((item) => {
          const active = isActive(pathname, item);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-[15px] font-medium transition-all duration-200",
                active
                  ? "bg-gradient-to-r from-indigo-600 to-indigo-950 text-white shadow-md shadow-indigo-500/20"
                  : "text-slate-600 hover:bg-indigo-50 hover:text-indigo-700 dark:text-slate-300 dark:hover:bg-slate-800",
              )}
            >
              <item.icon className="size-5 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="flex shrink-0 items-center gap-3 border-t p-4">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-indigo-950 text-base font-semibold text-white">
          {getInitial(user.fullName)}
        </span>
        <div className="min-w-0 flex-1 leading-tight">
          <p className="truncate text-sm font-semibold">{user.fullName}</p>
          <p className="truncate text-xs text-muted-foreground">{user.subtitle}</p>
        </div>
        <Button variant="ghost" size="icon" onClick={onLogout} aria-label="Đăng xuất" className="text-slate-500 hover:text-red-600">
          <LogOut className="size-5" />
        </Button>
      </div>
    </div>
  );
}
