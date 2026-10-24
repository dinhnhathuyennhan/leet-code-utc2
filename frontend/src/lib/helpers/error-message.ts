/**
 * Lấy message tiếng Việt hiển thị cho UI từ lỗi bất kỳ.
 * ApiError (do wrapAxiosError tạo) đã mang sẵn message tiếng Việt.
 */
export function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "status" in error && (error as { status?: unknown }).status === 500) {
    return "Hệ thống đang gặp sự cố. Vui lòng thử lại sau.";
  }
  if (error instanceof Error && error.message) return error.message;
  return "Đã có lỗi xảy ra, vui lòng thử lại.";
}
