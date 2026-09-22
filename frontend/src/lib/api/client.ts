import { ApiError, isDetailBody, isValidationErrorBody } from "@/lib/api/error";
import { getAccessToken, setAccessToken } from "@/lib/auth/token-store";
import type { RefreshResponse } from "@/lib/api/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const GENERIC_NETWORK_ERROR = "Mất kết nối, vui lòng thử lại.";

type SessionExpiredHandler = () => void;
let onSessionExpired: SessionExpiredHandler | null = null;

/** Registered by AuthProvider on mount so client.ts stays framework-agnostic. */
export function setSessionExpiredHandler(handler: SessionExpiredHandler | null): void {
  onSessionExpired = handler;
}

/**
 * `/auth/login`, `/auth/refresh` never trigger the 401 -> refresh -> retry
 * dance (login/refresh 401s ARE the actual error, not a session expiring).
 * `/auth/change-password` is also excluded: the backend reuses HTTP 401 for
 * "current password wrong" on this endpoint (see
 * backend/app/services/auth_service.py::WrongCurrentPasswordError), which is
 * a business error, not an expired session — retrying it would risk a false
 * "session expired" logout when the user simply mistyped their password.
 */
const REFRESH_EXEMPT_PATHS = new Set(["/auth/login", "/auth/refresh", "/auth/change-password"]);

let refreshPromise: Promise<string | null> | null = null;

/**
 * Calls POST /auth/refresh (the refresh_token cookie rides along
 * automatically) and updates the in-memory access token. Concurrent callers
 * share one in-flight request instead of each firing their own refresh.
 */
export function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });

      if (!response.ok) {
        setAccessToken(null);
        return null;
      }

      const body = (await response.json()) as RefreshResponse;
      setAccessToken(body.access_token);
      return body.access_token;
    } catch {
      setAccessToken(null);
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

interface ApiFetchInit extends RequestInit {
  /** Skip attaching Authorization and skip the 401 refresh/retry dance. */
  skipAuth?: boolean;
}

async function parseJsonSafely(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function extractErrorDetail(body: unknown, status: number): string {
  if (isDetailBody(body)) return body.detail;
  if (isValidationErrorBody(body)) {
    return body.detail.map((item) => item.msg).join("; ");
  }
  return `Yêu cầu thất bại (mã lỗi ${status}).`;
}

async function performFetch(
  path: string,
  init: ApiFetchInit,
): Promise<Response> {
  const { skipAuth, headers, ...rest } = init;

  const finalHeaders = new Headers(headers);
  const token = getAccessToken();
  if (!skipAuth && token) {
    finalHeaders.set("Authorization", `Bearer ${token}`);
  }
  // FormData uploads must not get a manual Content-Type: the browser sets
  // the multipart boundary itself.
  if (
    rest.body !== undefined &&
    !(rest.body instanceof FormData) &&
    !finalHeaders.has("Content-Type")
  ) {
    finalHeaders.set("Content-Type", "application/json");
  }

  try {
    return await fetch(`${API_URL}${path}`, {
      ...rest,
      headers: finalHeaders,
      credentials: "include",
    });
  } catch {
    throw new ApiError({ status: 0, detail: GENERIC_NETWORK_ERROR, isNetworkError: true });
  }
}

/**
 * Typed fetch wrapper for the ChấmCode API: attaches the bearer token,
 * transparently refreshes and retries once on a session-expiry 401, and
 * throws ApiError with the backend's own Vietnamese message for every other
 * failure.
 */
export async function apiFetch<T>(path: string, init: ApiFetchInit = {}): Promise<T> {
  let response = await performFetch(path, init);

  const eligibleForRefresh = !init.skipAuth && !REFRESH_EXEMPT_PATHS.has(path);
  if (response.status === 401 && eligibleForRefresh) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      response = await performFetch(path, init);
    } else {
      onSessionExpired?.();
    }
  }

  if (!response.ok) {
    const body = await parseJsonSafely(response);
    throw new ApiError({ status: response.status, detail: extractErrorDetail(body, response.status) });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await parseJsonSafely(response)) as T;
}


//Bản test
// Fetch wrapper dùng chung: gắn JWT, gửi cookie refresh, chuẩn hoá lỗi (mục 3.2).
// Mọi request của frontend phải đi qua file này — không gọi `fetch` trần ở nơi khác.

// import { getAccessToken } from "@/lib/auth/token";

// const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// /** Lỗi đã chuẩn hoá để tầng UI chỉ cần đọc `status` + `message`. */
// export class ApiError extends Error {
//   /** 0 = không gọi tới được server (mất mạng / CORS / server chết). */
//   readonly status: number;
//   readonly detail?: unknown;

//   constructor(status: number, message: string, detail?: unknown) {
//     super(message);
//     this.name = "ApiError";
//     this.status = status;
//     this.detail = detail;
//   }

//   /** Exception flow E1 của mọi use-case: mất kết nối hoặc server lỗi. */
//   get isConnectionError(): boolean {
//     return this.status === 0 || this.status >= 500;
//   }
// }

// interface RequestOptions extends Omit<RequestInit, "body"> {
//   body?: unknown;
//   /** Bỏ qua việc gắn Authorization header (dùng cho /auth/login). */
//   skipAuth?: boolean;
// }

// export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
//   const { body, skipAuth, headers, ...init } = options;
//   const token = skipAuth ? null : getAccessToken();

//   let response: Response;
//   try {
//     response = await fetch(`${BASE_URL}${path}`, {
//       ...init,
//       // Cookie refresh token là HttpOnly → luôn phải gửi kèm credentials.
//       credentials: "include",
//       headers: {
//         "Content-Type": "application/json",
//         ...(token ? { Authorization: `Bearer ${token}` } : {}),
//         ...headers,
//       },
//       body: body === undefined ? undefined : JSON.stringify(body),
//     });
//   } catch (error) {
//     // fetch chỉ throw khi không tới được server → coi là lỗi kết nối.
//     throw new ApiError(0, "Lỗi kết nối từ server", error);
//   }

//   if (response.status === 204) {
//     return undefined as T;
//   }

//   const payload = await response.json().catch(() => null);

//   if (!response.ok) {
//     const message =
//       (payload as { detail?: string } | null)?.detail ?? "Đã có lỗi xảy ra, vui lòng thử lại";
//     throw new ApiError(response.status, message, payload);
//   }

//   return payload as T;
// }