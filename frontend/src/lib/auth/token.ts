// //bản test
// // Lưu/đọc access token phía client.
// // Refresh token do server đặt trong cookie HttpOnly — file này không đụng tới.

// const ACCESS_TOKEN_KEY = "utc2_access_token";

// /**
//  * `rememberMe = true`  → localStorage (giữ qua nhiều lần mở trình duyệt).
//  * `rememberMe = false` → sessionStorage (mất khi đóng tab).
//  */
// export function saveAccessToken(token: string, rememberMe: boolean): void {
//   if (typeof window === "undefined") return;
//   clearAccessToken();
//   const storage = rememberMe ? window.localStorage : window.sessionStorage;
//   storage.setItem(ACCESS_TOKEN_KEY, token);
// }

// export function getAccessToken(): string | null {
//   if (typeof window === "undefined") return null;
//   return (
//     window.localStorage.getItem(ACCESS_TOKEN_KEY) ??
//     window.sessionStorage.getItem(ACCESS_TOKEN_KEY)
//   );
// }

// export function clearAccessToken(): void {
//   if (typeof window === "undefined") return;
//   window.localStorage.removeItem(ACCESS_TOKEN_KEY);
//   window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
// }