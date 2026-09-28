// app/login/page.tsx
"use client";

import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { LoginForm } from "@/components/shared/login-form";
import type { UserResponse } from "@/lib/api/types";
import { AuthLayout } from "@/components/shared/auth-layout";
import { getHomePath } from "@/lib/auth/redirect";
import { usePublicRoute } from "@/hooks/use-route-guard";

export default function LoginPage() {
  const router = useRouter();
  const { isChecking } = usePublicRoute();

  if (isChecking) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-900">
        <Loader2 className="size-8 animate-spin text-white" />
      </div>
    );
  }

  const handleLoginSuccess = (user: UserResponse) => {
    router.replace(getHomePath(user));
  };

  return (
    <AuthLayout>
      <LoginForm onSuccess={handleLoginSuccess} />
    </AuthLayout>
  );
}