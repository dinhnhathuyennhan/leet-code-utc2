// lib/api/endpoints/auth.ts
// Tất cả các API call liên quan đến auth.
// Mỗi function gọi axiosInstance trực tiếp theo đúng HTTP method,
// bắt lỗi bằng wrapAxiosError() để trả về ApiError chuẩn.

import axiosInstance, { refreshAccessToken } from "@/lib/axios";
import { wrapAxiosError } from "@/lib/api/client";
import type { ChangePasswordRequest, LoginRequest, LoginResponse } from "@/lib/api/types";

// ─── POST /auth/login ─────────────────────────────────────────────────────────

/** Public endpoint — skipAuth: true để không gắn Bearer token. */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  try {
    const res = await axiosInstance.post<LoginResponse>(
      "/auth/login",
      data,
      { skipAuth: true },
    );
    return res.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

// ─── POST /auth/change-password ───────────────────────────────────────────────

/**
 * Protected endpoint — Bearer token được gắn tự động bởi request interceptor.
 * Backend trả về LoginResponse với access_token mới sau khi đổi mật khẩu.
 *
 * LƯU Ý: 401 ở đây = "sai mật khẩu hiện tại" (business error), KHÔNG phải
 * session hết hạn — nên endpoint này nằm trong REFRESH_EXEMPT_PATHS (axios.ts).
 */
export async function changePassword(data: ChangePasswordRequest): Promise<LoginResponse> {
  try {
    const res = await axiosInstance.post<LoginResponse>(
      "/auth/change-password",
      data,
    );
    return res.data;
  } catch (error) {
    throw wrapAxiosError(error);
  }
}

// ─── POST /auth/refresh ───────────────────────────────────────────────────────

/**
 * Re-export từ axios.ts — dùng chung implementation giữa AuthProvider bootstrap
 * và response interceptor (tránh duplicate).
 */
export const refresh = refreshAccessToken;

// ─── POST /auth/logout ────────────────────────────────────────────────────────

/**
 * Best-effort — local session phải clear dù backend call thất bại.
 * (endpoint chưa implement server-side, wired sẵn để caller không cần đổi)
 */
export async function logout(): Promise<void> {
  try {
    await axiosInstance.post("/auth/logout", null, { skipAuth: true });
  } catch {
    // Cố ý bỏ qua — auth-context.tsx sẽ clear local state trong finally
  }
}
