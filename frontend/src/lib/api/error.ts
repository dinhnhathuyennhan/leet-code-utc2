/**
 * Thrown by apiFetch for every non-2xx response and for network failures.
 * `detail` is safe to render directly: for business/HTTP errors it is the
 * backend's own Vietnamese message (`{"detail": "..."}`, see docs/api-design.md);
 * for a network failure or an unparsable body it falls back to a generic
 * Vietnamese message.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;
  readonly isNetworkError: boolean;

  constructor(params: { status: number; detail: string; isNetworkError?: boolean }) {
    super(params.detail);
    this.name = "ApiError";
    this.status = params.status;
    this.detail = params.detail;
    this.isNetworkError = params.isNetworkError ?? false;
  }
}

export function isDetailBody(value: unknown): value is { detail: string } {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Record<string, unknown>).detail === "string"
  );
}

/** FastAPI 422 validation errors: {"detail": [{"loc": [...], "msg": "...", ...}, ...]}. */
export function isValidationErrorBody(
  value: unknown,
): value is { detail: Array<{ loc: unknown[]; msg: string }> } {
  return (
    typeof value === "object" &&
    value !== null &&
    Array.isArray((value as Record<string, unknown>).detail)
  );
}
