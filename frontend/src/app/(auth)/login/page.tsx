// app/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, LogOut } from "lucide-react";
import { LoginForm } from "@/components/shared/login-form";
import type { UserResponse } from "@/lib/api/types";
import { AuthLayout } from "@/components/shared/auth-layout";
import { getHomePath } from "@/lib/auth/redirect";
import { useAuth } from "@/context/auth-context";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const router = useRouter();
  const auth = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLoginSuccess = (user: UserResponse) => {
    router.replace(getHomePath(user));
  };

  const handleLogout = async () => {
    setIsLoggingOut(true);
    await auth.logout();
    setIsLoggingOut(false);
  };

  if (auth.status === "authenticated") {
    return (
      <AuthLayout>
        <div className="w-full max-w-md rounded-3xl bg-white p-8 text-center shadow-2xl">
          <h1 className="text-2xl font-bold text-slate-900">Bạn đang đăng nhập</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Tài khoản {auth.user.email} đang được sử dụng. Hãy đăng xuất tài khoản hiện tại
            trước khi đăng nhập bằng tài khoản khác.
          </p>
          <div className="mt-7 flex flex-col-reverse gap-3 sm:flex-row sm:justify-center">
            <Button type="button" variant="outline" onClick={() => router.back()}>
              <ArrowLeft />
              Hủy
            </Button>
            <Button type="button" onClick={handleLogout} disabled={isLoggingOut}>
              <LogOut />
              {isLoggingOut ? "Đang đăng xuất..." : "Đăng xuất"}
            </Button>
          </div>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <LoginForm onSuccess={handleLoginSuccess} />
    </AuthLayout>
  );
}