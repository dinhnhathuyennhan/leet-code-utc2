// lib/axios.ts
// Axios instance duy nhất dùng cho toàn bộ API calls.
// - Request interceptor  : gắn Bearer token (bỏ qua khi skipAuth = true)
// - Response interceptor : tự động refresh khi 401, retry request gốc,
//                          gọi onSessionExpired() khi refresh cũng thất bại.

import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";

import { getAccessToken, setAccessToken } from "@/lib/auth/token-store";
import type { RefreshResponse } from "@/lib/api/types";

// ─── Module augmentation — thêm skipAuth vào axios config ────────────────────
// Khai báo trên cả AxiosRequestConfig (dùng khi gọi .post/.get/.patch v.v.)
// lẫn InternalAxiosRequestConfig (dùng trong interceptors).
declare module "axios" {
  interface AxiosRequestConfig {
    /** Khi true: request interceptor sẽ không gắn Authorization header. */
    skipAuth?: boolean;
  }
  interface InternalAxiosRequestConfig {
    /** Khi true: request interceptor sẽ không gắn Authorization header. */
    skipAuth?: boolean;
  }
}

// ─── Instance ─────────────────────────────────────────────────────────────────

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const AUTH_REFRESH_TIMEOUT_MS = 5_000;

export const axiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 10_000,
  headers: { "Content-Type": "application/json" },
  // BẮT BUỘC — để trình duyệt tự gửi cookie chứa refresh_token
  withCredentials: true,
});

// ─── Session-expired handler (AuthProvider đăng ký lúc mount) ─────────────────

type SessionExpiredHandler = () => void;
let onSessionExpired: SessionExpiredHandler | null = null;

/** AuthProvider gọi hàm này khi mount để nhận callback logout. */
export function setSessionExpiredHandler(handler: SessionExpiredHandler | null): void {
  onSessionExpired = handler;
}

// ─── Request interceptor — gắn access token ──────────────────────────────────

axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // skipAuth = true → public endpoint (login, logout…) → không gắn token
    if (!config.skipAuth) {
      const token = getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error: unknown) => Promise.reject(error),
);

// ─── Refresh logic ────────────────────────────────────────────────────────────

/**
 * Các path này KHÔNG trigger vòng refresh-and-retry:
 *  /auth/login           → 401 = sai credentials
 *  /auth/refresh         → 401 = refresh token hết hạn → logout ngay
 *  /auth/change-password → 401 = sai mật khẩu hiện tại (business error,
 *    xem backend/app/services/auth_service.py::WrongCurrentPasswordError)
 */
const REFRESH_EXEMPT_PATHS = new Set([
  "/auth/login",
  "/auth/refresh-access-token",
  "/auth/change-password",
]);

let refreshPromise: Promise<string | null> | null = null;

/**
 * POST /auth/refresh-access-token — cookie refresh_token tự đi kèm nhờ withCredentials.
 * Nhiều request 401 đồng thời dùng chung 1 lần gọi refresh duy nhất.
 */
export function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      // Dùng axios.post thuần — tránh kích hoạt lại response interceptor
      const response = await axios.post<RefreshResponse>(
        `${API_URL}/auth/refresh-access-token`,
        {},
        { withCredentials: true, timeout: AUTH_REFRESH_TIMEOUT_MS },
      );
      const newToken = response.data.access_token;
      setAccessToken(newToken);
      return newToken;
    } catch {
      setAccessToken(null);
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

// ─── Response interceptor — xử lý 401 ───────────────────────────────────────

axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    const path = originalRequest?.url ?? "";
    const isExempt = REFRESH_EXEMPT_PATHS.has(path);

    if (error.response?.status === 401 && !originalRequest._retry && !isExempt) {
      originalRequest._retry = true;

      const newToken = await refreshAccessToken();

      if (newToken) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return axiosInstance(originalRequest);
      }

      // Refresh thất bại → session hết hạn
      onSessionExpired?.();
    }

    return Promise.reject(error);
  },
);

export default axiosInstance;
