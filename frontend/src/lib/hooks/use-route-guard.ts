// "use client";

// import { useEffect } from "react";
// import { useRouter, usePathname } from "next/navigation";
// import { useAuth } from "@/context/auth-context";
// import { getHomePath } from "@/lib/auth/redirect";

// /**
//  * Sử dụng hook này tại các trang nội bộ (Private Routes).
//  * Sẽ tự động chuyển hướng về /login nếu chưa đăng nhập,
//  * hoặc chuyển về /change-password nếu yêu cầu đổi mật khẩu.
//  */
// export function useProtectedRoute() {
//   const auth = useAuth();
//   const router = useRouter();
//   const pathname = usePathname();

//   useEffect(() => {
//     if (auth.status === "loading") return;

//     if (auth.status === "unauthenticated") {
//       router.replace("/login");
//     } else if (auth.status === "authenticated") {
//       if (auth.user.must_change_password && pathname !== "/change-password") {
//         router.replace("/change-password");
//       } else if (!auth.user.must_change_password && pathname === "/change-password") {
//         router.replace(getHomePath(auth.user));
//       }
//     }
//   }, [auth.status, auth.user, pathname, router]);

//   // Derive isAllowed without triggering a state update inside useEffect
//   const isAllowed =
//     auth.status === "authenticated" &&
//     (pathname === "/change-password" ? auth.user.must_change_password : !auth.user.must_change_password);

//   return { isAllowed, user: auth.user, status: auth.status };
// }

// /**
//  * Sử dụng hook này tại các trang công khai (Public Routes) như /login, /forgot-password.
//  * Sẽ tự động chuyển hướng về trang chủ nếu ĐÃ ĐĂNG NHẬP.
//  */
// export function usePublicRoute() {
//   const auth = useAuth();
//   const router = useRouter();

//   useEffect(() => {
//     if (auth.status === "authenticated") {
//       if (auth.user.must_change_password) {
//         router.replace("/change-password");
//       } else {
//         router.replace(getHomePath(auth.user));
//       }
//     }
//   }, [auth.status, auth.user, router]);

//   return { isChecking: auth.status === "loading" || auth.status === "authenticated" };
// }
