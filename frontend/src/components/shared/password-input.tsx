"use client";

import * as React from "react";
import { Eye, EyeOff, Lock } from "lucide-react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

/**
 * Ô nhập mật khẩu: icon ổ khoá bên trái + nút ẩn/hiện bên phải.
 * Thuần hiển thị — nhận mọi prop của <input> và forward ref cho react-hook-form.
 * Dùng lại được ở màn hình đổi mật khẩu.
 */
export const PasswordInput = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  function PasswordInput({ className, ...props }, ref) {
    const [visible, setVisible] = React.useState(false);
    const ToggleIcon = visible ? EyeOff : Eye;

    return (
      <div className="relative">
        <Lock
          aria-hidden
          className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-[#808D9F]"
        />
        <Input
          ref={ref}
          type={visible ? "text" : "password"}
          className={cn("px-11", className)}
          {...props}
        />
        <button
          type="button"
          onClick={() => setVisible((value) => !value)}
          aria-label={visible ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
          className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-slate-400 transition-colors hover:text-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          <ToggleIcon className="size-4 text-[#808D9F]" />
        </button>
      </div>
    );
  },
);