"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { useAuth } from "@/context/auth-context";
import { getHomePath } from "@/lib/auth/redirect";

const PUBLIC_ROUTES = ["/login", "/forgot-password"];

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || auth.status === "loading") return;

    const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

    // If unauthenticated and on a private route, redirect to login
    if (auth.status === "unauthenticated" && !isPublicRoute) {
      router.replace("/login");
    }
    // If authenticated, check if they are on a public route or need to change password
    else if (auth.status === "authenticated") {
      if (isPublicRoute) {
        // Automatically send authenticated users to their dashboard,
        // so they don't see the login page or get prompted to logout.
        router.replace(getHomePath(auth.user));
      } else if (auth.user.must_change_password && pathname !== "/change-password") {
        // Force them to change password page if required
        router.replace("/change-password");
      } else if (!auth.user.must_change_password && pathname === "/change-password") {
        // If they successfully changed password (or don't need to) and are on the change password page, bounce them to home
        router.replace(getHomePath(auth.user));
      }
    }
  }, [auth, pathname, router, mounted]);

  // While checking auth status initially, prevent flashing UI
  if (!mounted || auth.status === "loading") {
    return (
      <div className="flex h-[100dvh] w-full items-center justify-center bg-slate-900">
        <Loader2 className="size-8 animate-spin text-white" />
      </div>
    );
  }

  // If they are authenticated but hit a public page, show loading while redirecting to avoid layout flash
  if (auth.status === "authenticated" && PUBLIC_ROUTES.includes(pathname)) {
    return (
      <div className="flex h-[100dvh] w-full items-center justify-center bg-slate-900">
        <Loader2 className="size-8 animate-spin text-white" />
      </div>
    );
  }

  return <>{children}</>;
}
