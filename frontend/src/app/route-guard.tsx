"use client";

import { Fragment, useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { getHomePath } from "@/lib/auth/redirect";

const PUBLIC_ROUTES = ["/login", "/forgot-password"];
const LOGIN_ROUTE = "/login";
const CHANGE_PASSWORD_ROUTE = "/change-password";

function hasRouteAccess(pathname: string, roleId: number): boolean {
  if (pathname === "/" || PUBLIC_ROUTES.includes(pathname)) {
    return true;
  }

  if (pathname.startsWith("/admin")) return roleId === 1;
  if (pathname.startsWith("/teacher")) return roleId === 2;
  if (pathname.startsWith("/student")) return roleId === 3;

  return true;
}

function getSafeFallbackPath(pathname: string | null, roleId: number, userHome: string): string {
  if (
    pathname &&
    pathname !== LOGIN_ROUTE &&
    pathname !== CHANGE_PASSWORD_ROUTE &&
    hasRouteAccess(pathname, roleId)
  ) {
    return pathname;
  }

  return userHome;
}

function getRedirectTarget(
  pathname: string,
  auth: Extract<ReturnType<typeof useAuth>, { status: "authenticated" }>,
  lastAllowedPath: string | null,
): string | null {
  if (pathname === "/forgot-password") return getHomePath(auth.user);

  if (auth.user.must_change_password && pathname !== CHANGE_PASSWORD_ROUTE) {
    return CHANGE_PASSWORD_ROUTE;
  }

  if (!auth.user.must_change_password && pathname === CHANGE_PASSWORD_ROUTE) {
    return getSafeFallbackPath(lastAllowedPath, auth.user.role_id, getHomePath(auth.user));
  }

  if (!hasRouteAccess(pathname, auth.user.role_id)) {
    return getSafeFallbackPath(lastAllowedPath, auth.user.role_id, getHomePath(auth.user));
  }

  return null;
}

export function RouteGuard({
  children,
}: {
  children: React.ReactNode;
}) {
  const auth = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const lastAllowedPathRef = useRef<string | null>(null);
  const [lastAllowedPath, setLastAllowedPath] = useState<string | null>(null);

  useEffect(() => {
    if (auth.status === "loading") return;

    const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

    if (auth.status === "unauthenticated" && !isPublicRoute) {
      router.replace("/login");
    } else if (auth.status === "authenticated") {
      if (pathname === LOGIN_ROUTE) {
        return;
      }

      const redirectTarget = getRedirectTarget(pathname, auth, lastAllowedPathRef.current);
      if (redirectTarget) {
        router.replace(redirectTarget);
      } else {
        lastAllowedPathRef.current = pathname;
        setLastAllowedPath(pathname);
      }
    }
  }, [auth, pathname, router]);

  if (auth.status === "loading") {
    return (
      <div className="h-[100dvh] w-full bg-slate-900" aria-busy="true" />
    );
  }

  const isUnauthenticatedPrivateRoute =
    auth.status === "unauthenticated" && !PUBLIC_ROUTES.includes(pathname);
  const isAuthenticatedRedirecting =
    auth.status === "authenticated" &&
    pathname !== LOGIN_ROUTE &&
    Boolean(getRedirectTarget(pathname, auth, lastAllowedPath));

  if (isUnauthenticatedPrivateRoute || isAuthenticatedRedirecting) {
    return null;
  }

  return <Fragment key={pathname}>{children}</Fragment>;
}