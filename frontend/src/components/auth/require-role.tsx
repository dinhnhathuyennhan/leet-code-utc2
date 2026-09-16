"use client";

import type { ReactNode } from "react";

import { useAuth } from "@/context/auth-context";
import type { Role } from "@/lib/api/types";

interface RequireRoleProps {
  allow: Role[];
  children: ReactNode;
  /** Rendered instead of the default message when the role check fails. */
  fallback?: ReactNode;
}

/**
 * Per-page role gate. Renders an inline "no access" message rather than
 * redirecting: a hard redirect risks a loop with the dashboard layout guard
 * and is more jarring for a bookmarked/shared URL than an inline message.
 *
 * This is a UX guard only — the real authorization boundary is the
 * backend's `require_role` dependency on each endpoint. Anyone can disable
 * JS or call the API directly, bypassing this component entirely.
 */
export function RequireRole({ allow, children, fallback }: RequireRoleProps) {
  const auth = useAuth();

  if (auth.status !== "authenticated" || !allow.includes(auth.user.role_id)) {
    return (
      fallback ?? (
        <p className="p-6 text-center text-sm text-muted-foreground">
          Bạn không có quyền truy cập trang này.
        </p>
      )
    );
  }

  return <>{children}</>;
}
