"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuth } from "@/context/auth-context";

/**
 * Auth guard for everything under /dashboard. Client-side only: the
 * refresh_token cookie is scoped to the backend's own origin, so a
 * Next.js middleware.ts on this app would never see it and could not make
 * a real auth decision — this layout is the actual boundary, backed by
 * AuthContext's in-memory session state.
 *
 * Deliberately no sidebar/topbar here — that's UI work owned separately.
 * This layout only decides: redirect, or render children.
 */
export default function DashboardLayout({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (auth.status === "unauthenticated") {
      router.replace("/login");
    } else if (auth.status === "authenticated" && auth.user.must_change_password) {
      router.replace("/change-password");
    }
  }, [auth, router]);

  if (auth.status === "loading") {
    // Placeholder only — replace with real loading UI when building pages.
    return <p className="p-6 text-sm text-muted-foreground">Đang tải...</p>;
  }

  if (auth.status === "unauthenticated") {
    return null;
  }

  if (auth.status === "authenticated" && auth.user.must_change_password) {
    return null;
  }

  return <>{children}</>;
}
