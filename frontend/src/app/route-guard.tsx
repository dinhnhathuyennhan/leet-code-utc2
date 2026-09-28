"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { useAuth } from "@/context/auth-context";
import { getHomePath } from "@/lib/auth/redirect";

const PUBLIC_ROUTES = ["/login", "/forgot-password"];

export function RouteGuard({
  children,
}: {
  children: React.ReactNode;
}) {
  const auth = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (auth.status === "loading") return;

    const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

    if (auth.status === "unauthenticated" && !isPublicRoute) {
      router.replace("/login");
    } else if (auth.status === "authenticated") {
      if (isPublicRoute) {
        router.replace(getHomePath(auth.user));
      } else if (
        auth.user.must_change_password &&
        pathname !== "/change-password"
      ) {
        router.replace("/change-password");
      } else if (
        !auth.user.must_change_password &&
        pathname === "/change-password"
      ) {
        router.replace(getHomePath(auth.user));
      }
    }
  }, [auth, pathname, router]);

  if (auth.status === "loading") {
    return (
      <div className="flex h-[100dvh] w-full items-center justify-center bg-slate-900">
        <Loader2 className="size-8 animate-spin text-white" />
      </div>
    );
  }

  if (
    auth.status === "authenticated" &&
    PUBLIC_ROUTES.includes(pathname)
  ) {
    return (
      <div className="flex h-[100dvh] w-full items-center justify-center bg-slate-900">
        <Loader2 className="size-8 animate-spin text-white" />
      </div>
    );
  }

  return <>{children}</>;
}