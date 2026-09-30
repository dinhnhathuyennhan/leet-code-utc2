"use client";

import Link from "next/link";
import { useState } from "react";
import { Bell, ChevronDown, KeyRound, LogOut, Moon, Sun, User } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { ToggleGroup, ToggleGroupItem } from "../ui/toggle-group";

const LANG_ITEM =
  "h-7 min-w-9 rounded-full px-2.5 text-xs font-semibold text-slate-500 data-[state=on]:bg-card data-[state=on]:text-indigo-700 data-[state=on]:shadow-sm";

/** TODO(i18n): mới là công tắc giao diện — nối với thư viện i18n khi dự án chọn xong. */
function LanguageToggle() {
  const [lang, setLang] = useState("vi");
  return (
    <ToggleGroup
      type="single"
      value={lang}
      onValueChange={(value) => value && setLang(value)}
      aria-label="Ngôn ngữ"
      className="rounded-full bg-indigo-50 p-0.5 dark:bg-slate-800"
    >
      <ToggleGroupItem value="vi" className={LANG_ITEM}>VI</ToggleGroupItem>
      <ToggleGroupItem value="en" className={LANG_ITEM}>EN</ToggleGroupItem>
    </ToggleGroup>
  );
}

/** Hai icon đổi bằng class `dark:` nên không cần chờ mount (tránh hydration mismatch). */
function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label="Đổi giao diện sáng/tối"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      className="rounded-full text-slate-500"
    >
      <Sun className="size-5 dark:hidden" />
      <Moon className="hidden size-5 dark:block" />
    </Button>
  );
}

function NotificationButton({ hasUnread }: { hasUnread: boolean }) {
  return (
    <Button variant="ghost" size="icon" aria-label="Thông báo" className="relative rounded-full text-slate-500">
      <Bell className="size-5" />
      {hasUnread && <span className="absolute right-2 top-2 size-2 rounded-full bg-red-500 ring-2 ring-card" />}
    </Button>
  );
}

function UserMenu({ onLogout }: { onLogout: () => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Menu tài khoản"
          className="flex items-center gap-1.5 rounded-full p-0.5 pr-1 outline-none transition-colors hover:bg-indigo-50 focus-visible:ring-2 focus-visible:ring-indigo-500 dark:hover:bg-slate-800"
        >
          <span className="flex size-10 items-center justify-center rounded-full bg-indigo-950 text-white">
            <User className="size-5" />
          </span>
          <ChevronDown className="size-4 text-slate-500" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-52">
        <DropdownMenuItem asChild>
          <Link href="/change-password"><KeyRound className="size-4" /> Đổi mật khẩu</Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={onLogout} className="text-red-600 focus:text-red-600">
          <LogOut className="size-4" /> Đăng xuất
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function TopbarActions({ onLogout, hasUnread = false }: { onLogout: () => void; hasUnread?: boolean }) {
  return (
    <div className="flex items-center gap-1.5 sm:gap-3">
      <LanguageToggle />
      <ThemeToggle />
      <NotificationButton hasUnread={hasUnread} />
      <span aria-hidden className="mx-1 hidden h-6 w-px bg-border sm:block" />
      <UserMenu onLogout={onLogout} />
    </div>
  );
}
