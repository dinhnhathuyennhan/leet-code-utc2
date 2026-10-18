"use client";

import type { ReactNode } from "react";

/**
 * Layout cho mọi trang trong `/student/classes/*`.
 *
 * KHÔNG wrap AppShell ở đây — AppShell đã được đăng ký ở layout cha
 * `(student)/layout.tsx`. Nếu wrap thêm sẽ sinh 2 topbar + 2 sidebar lồng nhau
 * (do Next.js chồng layout theo segment), gây lệch bố cục + khoảng trống lớn.
 *
 * Chỉ render children để Next.js tạo scope route segment này.
 */
export default function StudentClassesLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
