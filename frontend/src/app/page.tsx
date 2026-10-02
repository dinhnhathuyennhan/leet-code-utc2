// app/page.tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { getHomePath } from "@/lib/auth/redirect";

export default function Home() {
  const router = useRouter();
  const auth = useAuth();

  useEffect(() => {
    // 1. Chờ AuthProvider hoàn tất bootstrap()
    if (auth.status === "loading") return;

    // 2. Điều hướng dựa trên trạng thái phiên đăng nhập
    if (auth.status === "authenticated") {
      router.replace(getHomePath(auth.user));
    } else if (auth.status === "unauthenticated") {
      router.replace("/login");
    }
  }, [auth.status, auth.user, router]);

  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-900">
      <Loader2 className="size-8 animate-spin text-white" />
    </div>
  );
}