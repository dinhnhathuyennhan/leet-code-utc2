// app/change-password/page.tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ChangePasswordForm } from "@/components/shared/change-password-form";
import { useAuth } from "@/context/auth-context";
import { getHomePath } from "@/lib/auth/redirect";
import { Loader2 } from "lucide-react";

export default function ChangePasswordPage() {
  const router = useRouter();
  const auth = useAuth();

  useEffect(() => {
    if (auth.status === "loading") return;

    // 1. Chưa đăng nhập -> Chuyển về /login
    if (auth.status === "unauthenticated") {
      router.replace("/login");
      return;
    }

    // 2. Đã đăng nhập nhưng KHÔNG cần đổi mật khẩu -> Chuyển về Dashboard
    if (auth.status === "authenticated" && !auth.user.must_change_password) {
      router.replace(getHomePath(auth.user));
    }
  }, [auth, router]);

  const handleSuccess = () => {
    if (auth.status === "authenticated") {
      // Đổi mật khẩu xong, coi như must_change_password = false -> Vào Dashboard
      router.replace(getHomePath({ ...auth.user, must_change_password: false }));
    }
  };

  // Chỉ cho phép hiển thị Form khi đã Đăng nhập VÀ Bắt buộc đổi mật khẩu
  const canAccess = auth.status === "authenticated" && auth.user.must_change_password;

  if (!canAccess) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-900">
        <Loader2 className="size-8 animate-spin text-white" />
      </div>
    );
  }

  return (
    <div
      className="flex min-h-screen w-full items-center justify-center p-4"
      style={{
        backgroundImage: "url('/images/change-password-bg.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      <ChangePasswordForm onSuccess={handleSuccess} />
    </div>
  );
}