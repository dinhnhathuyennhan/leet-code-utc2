import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/error";

/**
 * Most account-management endpoints don't exist server-side yet (see
 * docs/api-design.md), so a plain 404 is an expected, permanent outcome
 * today — retrying it just delays the error UI. Only network failures and
 * 5xx are worth a single retry.
 */
function shouldRetry(failureCount: number, error: unknown): boolean {
  if (failureCount >= 1) return false;
  if (error instanceof ApiError) {
    return error.isNetworkError || error.status >= 500;
  }
  return false;
}

export function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: shouldRetry,
        staleTime: 30_000,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * Shared query-key namespace for account data. No list endpoint exists yet
 * (no `GET` route to list users), so nothing invalidates this today — it's
 * here so the first `useQuery(["accounts", ...])` that's added later doesn't
 * need a naming decision.
 */
export const accountsQueryKey = ["accounts"] as const;
