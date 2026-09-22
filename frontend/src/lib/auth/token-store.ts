/**
 * Access-token holder, persisted to localStorage so it survives a hard
 * reload/tab close without waiting on `POST /auth/refresh` first.
 */

const STORAGE_KEY = "chamcode.accessToken";

function readStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

let accessToken: string | null = readStoredToken();

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
  if (typeof window === "undefined") return;
  try {
    if (token) {
      localStorage.setItem(STORAGE_KEY, token);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // localStorage can throw (private browsing, disabled storage) — token stays in-memory only.
  }
}
