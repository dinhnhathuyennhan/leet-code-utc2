import type { Role } from "@/lib/api/types";

/** Shape of the payload backend puts in an access token (see backend/app/core/token.py). */
export interface AccessTokenClaims {
  sub: string;
  role: Role;
  tv: number;
  type: "access";
  iat: number;
  exp: number;
}

function base64UrlDecode(segment: string): string {
  const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

function isAccessTokenClaims(value: unknown): value is AccessTokenClaims {
  if (typeof value !== "object" || value === null) return false;
  const claims = value as Record<string, unknown>;
  return (
    typeof claims.sub === "string" &&
    typeof claims.role === "number" &&
    typeof claims.tv === "number" &&
    claims.type === "access" &&
    typeof claims.exp === "number"
  );
}

/**
 * Decodes (does not verify) a JWT access token's payload. Verification is
 * the backend's job (it holds JWT_SECRET_KEY); the frontend only needs the
 * claims to know who is logged in and drive role-based UI.
 */
export function decodeAccessToken(token: string): AccessTokenClaims | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;

  try {
    const payload: unknown = JSON.parse(base64UrlDecode(parts[1]));
    return isAccessTokenClaims(payload) ? payload : null;
  } catch {
    return null;
  }
}
