"use client";

import { Fragment, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { getHomePath } from "@/lib/auth/redirect";
import { Loader2 } from "lucide-react";

const PUBLIC_ROUTES = ["/login", "/forgot-password"];
const LOGIN_ROUTE = "/login";
const CHANGE_PASSWORD_ROUTE = "/change-password";

const ROLE_CONFIG = {
  ADMIN: { path: "/admin", roleId: 1 },
  TEACHER: { path: "/teacher", roleId: 2 },
  STUDENT: { path: "/student", roleId: 3 },
} as const;

function hasRouteAccess(pathname: string, roleId: number): boolean {
  if (pathname === "/" || PUBLIC_ROUTES.includes(pathname)) {
    return true;
  }
  const matchedRole = Object.values(ROLE_CONFIG).find((config) =>
    pathname.startsWith(config.path)
  );

  if (matchedRole) {
    return roleId === matchedRole.roleId;
  }

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
  const searchParams = useSearchParams();
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
        if (hasRouteAccess(pathname, auth.user.role_id)) {
          // 1. Lấy chuỗi query (VD: "?page=2&sort=desc")
          const search = searchParams.toString();
          const queryString = search ? `?${search}` : "";
          
          // 2. Lấy hash hiện tại (An toàn cho SSR trong Next.js)
          const hash = typeof window !== "undefined" ? window.location.hash : "";
          
          // 3. Ghép lại thành URL hoàn chỉnh
          const fullPath = `${pathname}${queryString}${hash}`;

          // 4. CHẶN VÒNG LẶP VÔ HẠN: Chỉ set state nếu URL thực sự thay đổi
          if (lastAllowedPathRef.current !== fullPath) {
            lastAllowedPathRef.current = fullPath;
            setLastAllowedPath(fullPath);
          }
        }
      }
    }
  },[auth, pathname, searchParams, router]);
  if (auth.status === "loading") {
    return (
      <div className="h-[100dvh] w-full bg-slate-900" aria-busy="true" />
    );
  }

  // --- LUỒNG 2: Xử lý hiển thị màn hình 403 (Sai quyền) ---
  if (auth.status === "authenticated" && !hasRouteAccess(pathname, auth.user.role_id)) {
    return (
      <div className="flex h-[100dvh] w-full flex-col items-center justify-center bg-slate-900 text-slate-200">
        <h1 className="text-4xl font-bold mb-4">403</h1>
        <p className="mb-6">Bạn không có quyền truy cập vào trang này.</p>
        <button
          onClick={() => router.replace(getHomePath(auth.user))}
          className="rounded-md bg-blue-600 px-4 py-2 hover:bg-blue-700 transition"
        >
          Quay lại trang chủ
        </button>
      </div>
    );
  }

  // --- LUỒNG 1: Xử lý che màn hình khi đang Redirect ---
  const isUnauthenticatedPrivateRoute =
    auth.status === "unauthenticated" && !PUBLIC_ROUTES.includes(pathname);
  const isAuthenticatedRedirecting =
    auth.status === "authenticated" &&
    pathname !== LOGIN_ROUTE &&
    Boolean(getRedirectTarget(pathname, auth, lastAllowedPath));

  if (isUnauthenticatedPrivateRoute || isAuthenticatedRedirecting) {
    // Trả về Loading (màn hình nền tối) thay vì null để sửa lỗi chớp trắng UI
    return (
      <div className="h-[100dvh] w-full bg-slate-900 flex items-center justify-center" aria-busy="true">
        <Loader2 className="animate-spin text-white size-8" />
      </div>
    );
  }

  return <Fragment key={pathname}>{children}</Fragment>;
}