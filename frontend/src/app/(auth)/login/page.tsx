// app/login/page.tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LoginForm } from "@/components/shared/login-form";
import type { UserResponse } from "@/lib/api/types";
import { AuthLayout } from "@/components/shared/auth-layout";
import { useAuth } from "@/context/auth-context";
import { getHomePath } from "@/lib/auth/redirect";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const auth = useAuth();

  useEffect(() => {
    if (auth.status === "authenticated") {
      router.replace(getHomePath(auth.user));
    }
  }, [auth, router]);

  const handleLoginSuccess = (user: UserResponse) => {
    router.replace(getHomePath(user));
  };

  if (auth.status === "loading" || auth.status === "authenticated") {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-900">
        <Loader2 className="size-8 animate-spin text-white" />
      </div>
    );
  }

  return (
    <AuthLayout>
      <LoginForm onSuccess={handleLoginSuccess} />
    </AuthLayout>
  );
}