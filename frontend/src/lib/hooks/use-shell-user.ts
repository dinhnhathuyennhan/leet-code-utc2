"use client";

// Cầu nối duy nhất giữa AppShell và auth-context.
// Dùng AuthProvider làm nguồn dữ liệu duy nhất cho shell.

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/context/auth-context";

export type ShellRole = "teacher" | "student";

export interface ShellUser {
  fullName: string;
  subtitle: string; // giảng viên: "Giảng viên - BM CNTT" · sinh viên: "MSSV - Lớp"
}

export function useShellUser(role: ShellRole) {
  const router = useRouter();
  const auth = useAuth();

  useEffect(() => {
    if (auth.status === "unauthenticated") {
      router.replace("/login");
    } else if (auth.status === "authenticated") {
      const expectedRole = role === "teacher" ? 2 : 3;
      if (auth.user.role_id !== expectedRole) router.replace("/");
    }
  }, [auth, role, router]);

  const user: ShellUser = auth.status === "authenticated"
    ? { fullName: auth.user.full_name || auth.user.email, subtitle: role === "teacher" ? "Giảng viên" : "Sinh viên" }
    : { fullName: "", subtitle: "" };

  return { user, logout: auth.logout };
}
