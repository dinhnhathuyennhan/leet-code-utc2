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
    <div className="flex h-full min-w-0 flex-col bg-card">
      <div className="flex h-[61px] shrink-0 items-center gap-2 border-b px-3 xl:px-4">
        <Image src="/images/code-logo.svg" alt="" width={38} height={38} className="h-9 w-auto" />
        <div className="min-w-0 leading-tight">
          <p className="truncate text-[15px] font-bold tracking-tight text-indigo-950 dark:text-indigo-200">
            UTC2 JUDGE MASTER
          </p>
          <p className="truncate text-xs text-muted-foreground">Hệ Thống Đánh Giá Lập Trình</p>
        </div>
      </div>

      <nav aria-label="Điều hướng chính" className="flex-1 space-y-1 overflow-y-auto p-3.5">
        {navItems.map((item) => {
          const active = isActive(pathname, item);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-medium transition-all duration-200",
                active
                  ? "bg-gradient-to-r from-indigo-600 to-indigo-950 text-white shadow-md shadow-indigo-500/20"
                  : "text-slate-600 hover:bg-indigo-50 hover:text-indigo-700 dark:text-slate-300 dark:hover:bg-slate-800",
              )}
            >
              <item.icon className="size-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="flex shrink-0 items-center gap-2 border-t p-3.5">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-indigo-800 text-sm font-semibold text-white">
          {getInitial(user.fullName)}
        </span>
        <div className="min-w-0 flex-1 leading-tight">
          <p className="truncate text-[13px] font-semibold">{user.fullName}</p>
          <p className="truncate text-[11px] text-muted-foreground">{user.subtitle}</p>
        </div>
        <Button variant="ghost" size="icon" onClick={onLogout} aria-label="Đăng xuất" className="text-slate-500 hover:text-red-600">
          <LogOut className="size-5" />
        </Button>
      </div>
    </div>
  );
}
