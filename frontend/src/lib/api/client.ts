import { refreshAccessToken, setSessionExpiredHandler } from "@/lib/axios";
import { ApiError } from "@/lib/api/error";
import type { AxiosError } from "axios";

export { setSessionExpiredHandler, refreshAccessToken };

// ─── Helper parse body lỗi từ FastAPI ────────────────────────────────────────

function extractErrorDetail(data: unknown, status: number): string {
  if (typeof data === "object" && data !== null) {
    const record = data as Record<string, unknown>;

    // 1. Dạng { "detail": "Email hoặc mật khẩu không đúng" }
    if (typeof record.detail === "string" && record.detail.trim() !== "") {
      return record.detail;
    }

    // 2. Dạng { "message": "Mật khẩu hiện tại không đúng" }
    if (typeof record.message === "string" && record.message.trim() !== "") {
      return record.message;
    }

    // 3. Dạng { "error": "Phiên đăng nhập đã hết hạn" }
    if (typeof record.error === "string" && record.error.trim() !== "") {
      return record.error;
    }

    // 4. Dạng AppError lồng nhau: { "detail": { "message": "..." } }
    if (typeof record.detail === "object" && record.detail !== null) {
      const nested = record.detail as Record<string, unknown>;
      if (typeof nested.message === "string" && nested.message.trim() !== "") {
        return nested.message;
      }
      if (typeof nested.error === "string" && nested.error.trim() !== "") {
        return nested.error;
      }
    }

    // 5. Dạng FastAPI 422 validation errors: { "detail": [{ "msg": "..." }] }
    if (Array.isArray(record.detail)) {
      const items = record.detail as Array<{ msg?: string }>;
      const messages = items
        .map((item) => item.msg)
        .filter((msg): msg is string => Boolean(msg));
      if (messages.length > 0) {
        return messages.join("; ");
      }
    }
  }

  // 6. Thông báo mặc định theo mã HTTP status khi Backend không gửi body lỗi
  if (status === 401) {
    return "Email hoặc mật khẩu không chính xác.";
  }
  if (status === 403) {
    return "Bạn không có quyền thực hiện thao tác này.";
  }
  if (status === 500) {
    return "Lỗi hệ thống máy chủ. Vui lòng thử lại sau.";
  }

  return `Yêu cầu thất bại (mã lỗi ${status}).`;
}

// ─── wrapAxiosError ───────────────────────────────────────────────────────────

/**
 * Dùng trong catch() của mỗi endpoint function.
 * Convert AxiosError → ApiError với message tiếng Việt sẵn dùng cho UI.
 */
export function wrapAxiosError(error: unknown): never {
  const axiosErr = error as AxiosError;

  // Không có response → network error (offline, timeout, CORS, DNS fail)
  if (!axiosErr.response) {
    throw new ApiError({
      status: 0,
      detail: "Mất kết nối, vui lòng thử lại.",
      isNetworkError: true,
    });
  }

  const { status, data } = axiosErr.response;
  throw new ApiError({
    status,
    detail: extractErrorDetail(data, status),
  });
}