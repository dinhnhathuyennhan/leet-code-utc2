import { apiFetch, refreshAccessToken } from "@/lib/api/client";
import type { ChangePasswordRequest, LoginRequest, LoginResponse } from "@/lib/api/types";

/** POST /auth/login — public, sets the HttpOnly refresh_token cookie. */
export function login(data: LoginRequest): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify(data),
  });
}

/** POST /auth/change-password — requires a valid access token. */
export function changePassword(data: ChangePasswordRequest): Promise<LoginResponse> {
  return apiFetch<LoginResponse>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * POST /auth/refresh — reads the refresh_token cookie, returns a fresh
 * access token (no user object). Re-exported from client.ts so there is a
 * single implementation shared by AuthProvider's bootstrap and apiFetch's
 * own 401 interceptor.
 */
export const refresh = refreshAccessToken;

/**
 * POST /auth/logout — not implemented server-side yet (see docs/api-design.md);
 * wired up ahead of time so callers don't need to change once it lands.
 */
export function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST", skipAuth: true });
}
