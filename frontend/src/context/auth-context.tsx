"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { setSessionExpiredHandler } from "@/lib/api/client";
import {
  changePassword as changePasswordRequest,
  login as loginRequest,
  logout as logoutRequest,
  refresh as refreshRequest,
} from "@/lib/api/endpoints/auth";
import type {
  ChangePasswordRequest,
  LoginRequest,
  LoginResponse,
  UserResponse,
} from "@/lib/api/types";
import { decodeAccessToken } from "@/lib/auth/decode-jwt";
import { setAccessToken } from "@/lib/auth/token-store";

type AuthState =
  | { status: "loading" }
  | { status: "unauthenticated" }
  | { status: "authenticated"; user: UserResponse };

type AuthContextValue = AuthState & {
  login: (data: LoginRequest) => Promise<UserResponse>;
  changePassword: (data: ChangePasswordRequest) => Promise<UserResponse>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const PROFILE_CACHE_KEY = "chamcode.profile";

interface CachedProfile {
  full_name: string;
  email: string;
  must_change_password: boolean;
}

function cacheProfile(user: UserResponse): void {
  try {
    const cached: CachedProfile = {
      full_name: user.full_name,
      email: user.email,
      must_change_password: user.must_change_password,
    };
    sessionStorage.setItem(PROFILE_CACHE_KEY, JSON.stringify(cached));
  } catch {
    // sessionStorage can throw (private browsing, disabled storage) — display-only cache, safe to skip.
  }
}

function readCachedProfile(): CachedProfile | null {
  try {
    const raw = sessionStorage.getItem(PROFILE_CACHE_KEY);
    return raw ? (JSON.parse(raw) as CachedProfile) : null;
  } catch {
    return null;
  }
}

function clearCachedProfile(): void {
  try {
    sessionStorage.removeItem(PROFILE_CACHE_KEY);
  } catch {
    // ignore
  }
}

/**
 * POST /auth/refresh returns only a fresh access token, no user object (a
 * gap in the current backend contract — recommend adding GET /auth/me).
 * user_id/role_id are recovered from the token's own claims (always
 * accurate: they come from the token just issued); full_name/email/
 * must_change_password are best-effort from the last login/change-password
 * response, cached in sessionStorage, purely to avoid a blank-profile flash.
 *
 * This is safe even when stale: any server-side change to
 * must_change_password also bumps token_version, which invalidates the
 * refresh token itself — so a truly stale cache can only occur in a fresh
 * tab that never completed a real login in this session.
 */
function buildUserFromAccessToken(accessToken: string): UserResponse | null {
  const claims = decodeAccessToken(accessToken);
  if (!claims) return null;

  const cached = readCachedProfile();
  return {
    user_id: claims.sub,
    role_id: claims.role,
    full_name: cached?.full_name ?? "",
    email: cached?.email ?? "",
    must_change_password: cached?.must_change_password ?? false,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  const handleSessionExpired = useCallback(() => {
    clearCachedProfile();
    setState({ status: "unauthenticated" });
  }, []);

  useEffect(() => {
    setSessionExpiredHandler(handleSessionExpired);
    return () => setSessionExpiredHandler(null);
  }, [handleSessionExpired]);

  // Silent session hydration: runs once on mount so a hard reload can
  // re-establish the session from the HttpOnly refresh cookie alone.
  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const token = await refreshRequest();
      if (cancelled) return;

      const user = token ? buildUserFromAccessToken(token) : null;
      setState(user ? { status: "authenticated", user } : { status: "unauthenticated" });
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (data: LoginRequest) => {
    const result: LoginResponse = await loginRequest(data);
    setAccessToken(result.access_token);
    cacheProfile(result.user);
    setState({ status: "authenticated", user: result.user });
    return result.user;
  }, []);

  const changePassword = useCallback(async (data: ChangePasswordRequest) => {
    const result: LoginResponse = await changePasswordRequest(data);
    setAccessToken(result.access_token);
    cacheProfile(result.user);
    setState({ status: "authenticated", user: result.user });
    return result.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } catch {
      // Best-effort: local session must clear even if the backend call fails
      // (e.g. the endpoint isn't implemented yet — see docs/api-design.md).
    } finally {
      setAccessToken(null);
      clearCachedProfile();
      setState({ status: "unauthenticated" });
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, login, changePassword, logout }),
    [state, login, changePassword, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
